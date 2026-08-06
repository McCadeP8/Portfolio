from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from io import BytesIO
import re
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd

from court_engine import CourtConfig, draw_branded_court
from data import team_info
import functions as fantrax
from jersey_engine import JerseyConfig, draw_uniform, figure_bytes as jersey_figure_bytes
from jersey_rotation import select_game_uniforms

from .datasets import DatasetRepository


BOX_SUM_STATS = ["GP", "MP", "2PTM", "2PTA", "3PTM", "3PTA", "FTM", "FTA", "PTS", "OREB", "DREB", "AST", "ST", "BLK", "TO", "+/-"]
CATEGORIES = ["MP", "TS%", "2PT%", "3PT%", "FT%", "PTS", "OREB", "DREB", "AST", "ST", "BLK", "TO", "+/-"]
WEIGHTS = {"PTS": 61, "AST": 41, "TS%": 41, "2PT%": 31, "+/-": 31, "3PT%": 31, "BLK": 31, "DREB": 31, "OREB": 31, "ST": 31, "FT%": 21, "MP": 11, "TO": 21}
PERCENTAGES = {"TS%", "2PT%", "3PT%", "FT%"}
SIMULATED_DATE_OFFSET_DAYS = 168


@dataclass(frozen=True)
class RotationPeriod:
    year: int
    period: int
    start: date
    end: date

    @property
    def opening_morning(self) -> bool:
        return self.start == self.as_of

    as_of: date


@dataclass(frozen=True)
class FantraxPost:
    kind: str
    filename: str
    image_bytes: bytes


def simulated_today(real_today: date | None = None, offset_days: int = SIMULATED_DATE_OFFSET_DAYS) -> date:
    """Advance through 2025-26 while the real calendar advances through the offseason."""
    return (real_today or date.today()) - timedelta(days=int(offset_days))


def period_for_date(calendar: pd.DataFrame, as_of: date) -> RotationPeriod | None:
    required = {"Year", "Period", "Date"}
    if calendar is None or calendar.empty or not required.issubset(calendar.columns):
        return None
    work = calendar[list(required)].copy()
    work["Date"] = pd.to_datetime(work["Date"], errors="coerce").dt.date
    work["Year"] = pd.to_numeric(work["Year"], errors="coerce")
    work["Period"] = pd.to_numeric(work["Period"], errors="coerce")
    work = work.dropna()
    current = work[work["Date"] == as_of]
    if current.empty:
        return None
    year, period = int(current.iloc[-1]["Year"]), int(current.iloc[-1]["Period"])
    dates = work[(work["Year"] == year) & (work["Period"] == period)]["Date"]
    return RotationPeriod(year, period, min(dates), max(dates), as_of)


def planned_post_kinds(period: RotationPeriod | None, slot: str = "all") -> list[str]:
    if period is None:
        return []
    overnight = ["matchup_recap", "mobile_matchup_recap", "record_leader"]
    if not period.opening_morning:
        overnight = ["overnight_scores", "mobile_overnight_scores", *overnight]
    opening = ["matchup_preview", "mobile_matchup_preview", "standings", "mobile_standings"] if period.opening_morning else []
    if slot == "overnight":
        return overnight
    if slot == "opening":
        return opening
    return [*opening, *overnight]


def _normalize_name(value: Any) -> str:
    text = re.sub(r"\b(Jr|Sr|II|III|IV|V)\b\.?", "", str(value or ""), flags=re.I)
    return re.sub(r"[^a-z0-9]+", "", text.lower())


def _team_key(value: Any) -> str:
    text = str(value or "").strip()
    for city, info in team_info.items():
        full = f"{city} {info.get('nickname', '')}".strip()
        if text == city or text == full or text.startswith(city + " "):
            return city
    return text


def _recalc(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    for column in BOX_SUM_STATS:
        out[column] = pd.to_numeric(out.get(column, 0), errors="coerce").fillna(0)
    attempts = out["2PTA"] + out["3PTA"] + 0.44 * out["FTA"]
    out["TS%"] = (out["PTS"] / (2 * attempts)).where(attempts > 0, 0)
    out["2PT%"] = (out["2PTM"] / out["2PTA"]).where(out["2PTA"] > 0, 0)
    out["3PT%"] = (out["3PTM"] / out["3PTA"]).where(out["3PTA"] > 0, 0)
    out["FT%"] = (out["FTM"] / out["FTA"]).where(out["FTA"] > 0, 0)
    return out


class FantraxRotation:
    def __init__(self, repository: DatasetRepository, project_root: Path, as_of: date):
        self.repository = repository
        self.root = Path(project_root)
        self.as_of = as_of
        self.calendar = fantrax.get_period_calendar()
        self.period = period_for_date(self.calendar, as_of)
        self.schedule = repository.read("schedule", required=True)
        self.standings = repository.read("standings", required=True)
        self.team_stats = repository.read("team_stats", required=True)
        self.rosters = repository.read("rosters", required=True)
        self.boxscores = repository.read("nba_boxscores", required=True)
        self.matchup_archive = repository.read("matchup_stats", required=True)
        self.players = repository.read("fantrax_players")
        self._bridge = self._player_bridge()

    def _player_bridge(self) -> pd.DataFrame:
        players = self.players.rename(columns={"name": "display_player", "fantraxId": "fantrax_id"}).copy()
        if players.empty or self.boxscores.empty:
            return pd.DataFrame(columns=["fantrax_id", "display_player", "espn_player_id"])
        players["fantrax_id"] = players["fantrax_id"].astype(str)
        players["_key"] = players["display_player"].map(_normalize_name)
        box = self.boxscores[["nba_player_id", "player_name"]].dropna().drop_duplicates().copy()
        box["_key"] = box["player_name"].map(_normalize_name)
        unique = box.groupby("_key")["nba_player_id"].nunique()
        box = box[box["_key"].isin(unique[unique == 1].index)]
        bridge = players.merge(box, on="_key", how="inner").rename(columns={"nba_player_id": "espn_player_id"})
        overrides = self.root / "player_id_overrides.csv"
        if overrides.exists():
            fixed = pd.read_csv(overrides).rename(columns={"fantraxId": "fantrax_id", "fantrax_name": "display_player"})
            fixed = fixed.dropna(subset=["fantrax_id", "espn_player_id"])
            fixed["fantrax_id"] = fixed["fantrax_id"].astype(str)
            bridge = bridge[~bridge["fantrax_id"].isin(fixed["fantrax_id"])]
            bridge = pd.concat([bridge, fixed], ignore_index=True, sort=False)
        bridge["espn_player_id"] = bridge["espn_player_id"].astype(str)
        return bridge[["fantrax_id", "display_player", "espn_player_id"]].drop_duplicates("fantrax_id")

    def matchup_rows(self, matchup: pd.Series | dict, through: date | None = None) -> pd.DataFrame:
        row = dict(matchup)
        year, period = int(row["Year"]), int(row["Period"])
        days = self.calendar.copy()
        days["Date"] = pd.to_datetime(days["Date"], errors="coerce").dt.date
        days = days[(pd.to_numeric(days["Year"], errors="coerce") == year) & (pd.to_numeric(days["Period"], errors="coerce") == period)]
        if through is not None:
            days = days[days["Date"] <= through]
        if days.empty:
            return pd.DataFrame()
        days = days[["Day", "Date"]].dropna().copy()
        days["Day"] = days["Day"].astype(int)
        active = self.rosters.copy()
        active = active[(pd.to_numeric(active["Year"], errors="coerce") == year) & (active["status"].astype(str).str.upper() == "ACTIVE")]
        active = active.rename(columns={"id": "fantrax_id", "period": "Day"})
        active["Day"] = pd.to_numeric(active["Day"], errors="coerce")
        active = active[active["Day"].isin(days["Day"])].copy()
        active["sbc_team"] = active["team_name"].map(_team_key)
        active = active[active["sbc_team"].isin([str(row["TeamA"]), str(row["TeamB"])])]
        active["fantrax_id"] = active["fantrax_id"].astype(str)
        active = active.merge(self._bridge, on="fantrax_id", how="left")
        box = self.boxscores[pd.to_numeric(self.boxscores["sbc_year"], errors="coerce") == year].copy()
        box["Date"] = pd.to_datetime(box["Date"], errors="coerce").dt.date
        box = box.merge(days, on="Date", how="inner")
        box["nba_player_id"] = box["nba_player_id"].astype(str)
        merged = active.merge(box, left_on=["Day", "espn_player_id"], right_on=["Day", "nba_player_id"], how="inner")
        if merged.empty:
            return merged
        merged["display_player"] = merged["display_player"].fillna(merged["player_name"])
        return merged.sort_values(["sbc_team", "display_player", "Date", "nba_game_id"]).reset_index(drop=True)

    def aggregate_players(self, rows: pd.DataFrame) -> pd.DataFrame:
        if rows.empty:
            return pd.DataFrame()
        keys = ["sbc_team", "fantrax_id", "espn_player_id", "display_player"]
        return _recalc(rows.groupby(keys, as_index=False)[BOX_SUM_STATS].sum()).sort_values(["sbc_team", "PTS"], ascending=[True, False])

    def team_totals(self, rows: pd.DataFrame) -> pd.DataFrame:
        if rows.empty:
            return pd.DataFrame(columns=["Team", *CATEGORIES])
        return _recalc(rows.groupby("sbc_team", as_index=False)[BOX_SUM_STATS].sum()).rename(columns={"sbc_team": "Team"})

    def category_results(self, totals: pd.DataFrame, team_a: str, team_b: str) -> tuple[pd.DataFrame, float, float]:
        if totals.empty or team_a not in set(totals["Team"]) or team_b not in set(totals["Team"]):
            return pd.DataFrame(), 0.0, 0.0
        table = totals.set_index("Team")
        output, score_a, score_b = [], 0.0, 0.0
        for stat, weight in WEIGHTS.items():
            a, b = float(table.loc[team_a, stat]), float(table.loc[team_b, stat])
            winner = team_a if (a < b if stat == "TO" else a > b) else team_b if (b < a if stat == "TO" else b > a) else "Tie"
            if winner == team_a:
                score_a += weight
            elif winner == team_b:
                score_b += weight
            else:
                score_a += weight / 2
                score_b += weight / 2
            output.append({"Category": stat, team_a: a, team_b: b, "Votes": weight, "Winner": winner})
        return pd.DataFrame(output), score_a, score_b

    def slate(self) -> pd.DataFrame:
        if self.period is None:
            return pd.DataFrame()
        games = self.schedule[(pd.to_numeric(self.schedule["Year"], errors="coerce") == self.period.year) & (pd.to_numeric(self.schedule["Period"], errors="coerce") == self.period.period)].copy()
        totals = []
        for _, game in games.iterrows():
            rows = self.matchup_rows(game, self.as_of)
            team_totals = self.team_totals(rows)
            if not team_totals.empty:
                team_totals["Game_ID"] = str(game.get("Game_ID", ""))
                totals.append(team_totals)
        # Every game in a period sees the same team aggregate, so deduplicate before scoring.
        live = pd.concat(totals, ignore_index=True).drop_duplicates("Team") if totals else pd.DataFrame()
        scored = fantrax.get_weekly_scores_df(self.period.year, self.period.period, games, live, self._standings_source(self.period.period - 1))
        if not live.empty:
            score_lookup = {}
            indexed = live.set_index("Team")
            for _, game in scored.iterrows():
                team_a, team_b = str(game["TeamA"]), str(game["TeamB"])
                categories, a, b = self.category_results(indexed.reset_index(), team_a, team_b)
                score_lookup[str(game.get("Game_ID", ""))] = (a, b)
            for index, game in scored.iterrows():
                a, b = score_lookup.get(str(game.get("Game_ID", "")), (0, 0))
                scored.loc[index, ["TeamA_Score", "TeamB_Score"]] = [a, b]
        return scored.reset_index(drop=True)

    def _standings_source(self, through_period: int) -> pd.DataFrame:
        year = self.period.year if self.period else 0
        eligible = self.standings[(pd.to_numeric(self.standings["Year"], errors="coerce") == year) & (pd.to_numeric(self.standings["Period"], errors="coerce") <= through_period)].copy()
        if eligible.empty:
            return self.standings
        chosen = int(pd.to_numeric(eligible["Period"], errors="coerce").max())
        return eligible[pd.to_numeric(eligible["Period"], errors="coerce") == chosen]

    def standings_table(self, conference: str) -> pd.DataFrame:
        through = max(0, self.period.period - 1) if self.period else 0
        source = self._standings_source(through).copy()
        if source.empty:
            return source
        source = source[source["Team"].map(lambda team: team_info.get(str(team), {}).get("conf")) == conference].copy()
        records = source.get("Record", pd.Series("0-0", index=source.index)).astype(str).str.extract(r"(\d+)\D+(\d+)").fillna(0).astype(int)
        source["wins"], source["losses"] = records[0], records[1]
        source["_pct"] = source["wins"] / (source["wins"] + source["losses"]).replace(0, pd.NA)
        source = source.sort_values(["_pct", "wins", "Team"], ascending=[False, False, True]).reset_index(drop=True)
        source["GB"] = ((source["wins"].max() - source["wins"]) / 2 + (source["losses"] - source["losses"].min()) / 2).round(1).astype(str)
        source.loc[source.index == 0, "GB"] = "-"
        source["FullTeam"] = source["Team"].map(lambda team: f"{team} {team_info.get(str(team), {}).get('nickname', '')}".strip())
        source["Logo"] = source["Team"].map(lambda team: team_info.get(str(team), {}).get("logo", ""))
        source["WinPct"] = (source["_pct"].fillna(0) * 100).round(1).astype(str) + "%"
        source["Streak"] = "-"
        source["Last10"] = source.apply(lambda row: f"{min(10, int(row['wins']))}-{max(0, min(10, int(row['wins'] + row['losses'])) - min(10, int(row['wins'])))}", axis=1)
        return source

    def featured(self, slate: pd.DataFrame) -> list[pd.Series]:
        standings = pd.concat([self.standings_table("West"), self.standings_table("East")], ignore_index=True)
        lookup = {str(row["Team"]): {"wins": float(row["wins"]), "losses": float(row["losses"]), "seed": index + 1} for index, row in standings.iterrows()}
        ranked = slate.copy()
        def rank(row):
            a = lookup.get(str(row.get("TeamA")), {"wins": 0, "losses": 0, "seed": 15})
            b = lookup.get(str(row.get("TeamB")), {"wins": 0, "losses": 0, "seed": 15})
            pa = a["wins"] / max(1, a["wins"] + a["losses"]); pb = b["wins"] / max(1, b["wins"] + b["losses"])
            strength = (pa + pb) * 100
            closeness = (1 - abs(pa - pb)) * 24
            race = max(0, 14 - min(abs(a["seed"] - 6), abs(a["seed"] - 10), abs(b["seed"] - 6), abs(b["seed"] - 10)))
            bonus = {"Playoffs": 80, "Play-In": 70, "In-Season Tournament": 35}.get(str(row.get("Type")), 0)
            return strength + closeness + race + bonus
        ranked["_rank"] = ranked.apply(rank, axis=1)
        return [row.copy() for _, row in ranked.sort_values("_rank", ascending=False).head(2).iterrows()]

    def team_averages(self, teams: list[str]) -> dict[str, dict[str, float | None]]:
        stats = self.team_stats[(pd.to_numeric(self.team_stats["Year"], errors="coerce") == self.period.year) & (pd.to_numeric(self.team_stats["Period"], errors="coerce") < self.period.period)].copy()
        result = {}
        for team in teams:
            rows = stats[stats["Team"].astype(str) == team]
            if rows.empty:
                result[team] = {category: None for category in CATEGORIES}; continue
            periods = max(1, rows["Period"].nunique())
            total = _recalc(pd.DataFrame([{column: pd.to_numeric(rows.get(column), errors="coerce").fillna(0).sum() for column in BOX_SUM_STATS}])).iloc[0]
            result[team] = {category: float(total[category]) if category in PERCENTAGES else float(total[category]) / periods for category in CATEGORIES}
        return result

    def lineup(self, team: str) -> pd.DataFrame:
        opening_days = self.calendar[(pd.to_numeric(self.calendar["Year"], errors="coerce") == self.period.year) & (pd.to_numeric(self.calendar["Period"], errors="coerce") == self.period.period)]
        day = int(pd.to_numeric(opening_days["Day"], errors="coerce").min())
        roster = self.rosters[(pd.to_numeric(self.rosters["Year"], errors="coerce") == self.period.year) & (pd.to_numeric(self.rosters["period"], errors="coerce") == day) & (self.rosters["status"].astype(str).str.upper() == "ACTIVE")].copy()
        roster = roster[roster["team_name"].map(_team_key) == team].rename(columns={"id": "fantrax_id", "position": "slot"})
        roster["fantrax_id"] = roster["fantrax_id"].astype(str)
        roster = roster.merge(self._bridge, on="fantrax_id", how="left")
        roster["headshot"] = roster["espn_player_id"].map(lambda value: f"https://a.espncdn.com/i/headshots/nba/players/full/{value}.png" if pd.notna(value) else "")
        slots, selected = ["PG", "SG", "SF", "PF", "C"], []
        for slot in slots:
            candidates = roster[(roster["slot"].astype(str).str.upper() == slot) & (~roster.index.isin(selected))]
            if candidates.empty:
                candidates = roster[~roster.index.isin(selected)]
            if not candidates.empty:
                selected.append(candidates.index[0])
        result = roster.loc[selected].head(5).copy()
        result["slot"] = slots[:len(result)]
        return result

    def _uniform_config(self, team: str, edition: str) -> tuple[JerseyConfig, str]:
        path = self.root / "jersey_team_configs.csv"
        table = pd.read_csv(path) if path.exists() else pd.DataFrame()
        row = table[(table.get("team", pd.Series(dtype=str)).astype(str) == team) & (table.get("edition", pd.Series(dtype=str)).astype(str) == edition)]
        values = {key: value for key, value in row.iloc[0].to_dict().items() if not pd.isna(value)} if not row.empty else {}
        config = JerseyConfig.from_mapping(values) if values else JerseyConfig(team=team, edition=edition)
        logo_team = str(row.iloc[0].get("logo_team") or team) if not row.empty else team
        return config, str(team_info.get(logo_team, team_info.get(team, {})).get("logo", ""))

    def jersey(self, team: str, edition: str) -> bytes:
        config, logo = self._uniform_config(team, edition)
        figure, _ = draw_uniform(config, logo=logo, view="front", dpi=120, background="none", show_view_label=False)
        content = jersey_figure_bytes(figure, "png", dpi=150, transparent=True)
        plt.close(figure)
        return content

    def court(self, home_team: str) -> bytes:
        path = self.root / "court_team_configs.csv"
        table = pd.read_csv(path) if path.exists() else pd.DataFrame()
        row = table[table.get("team", pd.Series(dtype=str)).astype(str) == home_team]
        values = {key: value for key, value in row.iloc[0].to_dict().items() if not pd.isna(value)} if not row.empty else {}
        config = CourtConfig.from_mapping(values) if values else CourtConfig(team=home_team)
        logo_team = str(row.iloc[0].get("center_logo_team") or home_team) if not row.empty else home_team
        logo = team_info.get(logo_team, team_info.get(home_team, {})).get("logo", "")
        figure, _ = draw_branded_court(config, logo=logo, orientation="horizontal", view="full", figsize=(12.4, 6.7), dpi=120)
        output = BytesIO(); figure.savefig(output, format="png", dpi=150, transparent=False, bbox_inches="tight", pad_inches=0.04); plt.close(figure)
        return output.getvalue()

    def preview_assets(self, featured: list[pd.Series]) -> list[dict[str, Any]]:
        assets = []
        for game in featured:
            a, b = str(game["TeamA"]), str(game["TeamB"])
            try:
                road, home, _ = select_game_uniforms(game, a, b, lambda team, edition: self._uniform_config(team, edition)[0])
            except Exception:
                road, home = "Icon", "Association"
            assets.append({"court": self.court(b), "road_jersey": self.jersey(a, road), "home_jersey": self.jersey(b, home), "road_edition": road, "home_edition": home, "lineups": {a: self.lineup(a), b: self.lineup(b)}, "team_averages": self.team_averages([a, b])})
        return assets

    def _trend(self, game: pd.Series) -> pd.DataFrame:
        days = self.calendar[(pd.to_numeric(self.calendar["Year"], errors="coerce") == self.period.year) & (pd.to_numeric(self.calendar["Period"], errors="coerce") == self.period.period)].copy()
        days["Date"] = pd.to_datetime(days["Date"], errors="coerce").dt.date
        points = []
        for day in sorted(value for value in days["Date"].dropna().unique() if value <= self.as_of):
            totals = self.team_totals(self.matchup_rows(game, day))
            _, a, b = self.category_results(totals, str(game["TeamA"]), str(game["TeamB"]))
            points.append({"game_date": pd.Timestamp(day).strftime("%Y%m%d"), "wallclock": pd.Timestamp(day, tz="America/New_York") + pd.Timedelta(hours=23), str(game["TeamA"]): a, str(game["TeamB"]): b})
        return pd.DataFrame(points)

    def _career_totals(self, through: date) -> pd.DataFrame:
        resolved = period_for_date(self.calendar, through)
        if resolved is None:
            return pd.DataFrame()
        archive = self.matchup_archive.copy()
        archive["sbc_year"] = pd.to_numeric(archive["sbc_year"], errors="coerce")
        archive["sbc_period"] = pd.to_numeric(archive["sbc_period"], errors="coerce")
        archive = archive[
            (archive["sbc_year"] < resolved.year)
            | ((archive["sbc_year"] == resolved.year) & (archive["sbc_period"] < resolved.period))
        ].copy()
        archive["sbc_team"] = archive["sbc_team"].map(_team_key)
        # A team can have multiple simultaneous schedule rows in tournament
        # periods; its player aggregate is repeated on each Game_ID.
        archive = archive.drop_duplicates(["sbc_year", "sbc_period", "sbc_team", "fantrax_id"])
        archive = archive.rename(columns={"fantrax_name": "display_player"})
        current_games = self.schedule[
            (pd.to_numeric(self.schedule["Year"], errors="coerce") == resolved.year)
            & (pd.to_numeric(self.schedule["Period"], errors="coerce") == resolved.period)
        ]
        partial_rows = []
        for _, game in current_games.iterrows():
            rows = self.matchup_rows(game, through)
            if not rows.empty:
                partial_rows.append(rows)
        if partial_rows:
            partial = pd.concat(partial_rows, ignore_index=True)
            partial = partial.drop_duplicates(["sbc_team", "fantrax_id", "nba_game_id"])
            partial = partial.groupby(["sbc_team", "fantrax_id", "display_player", "espn_player_id"], as_index=False)[BOX_SUM_STATS].sum()
        else:
            partial = pd.DataFrame()
        columns = ["sbc_team", "fantrax_id", "display_player", *BOX_SUM_STATS]
        pieces = [archive.reindex(columns=columns)]
        if not partial.empty:
            pieces.append(partial.reindex(columns=columns))
        combined = pd.concat(pieces, ignore_index=True)
        for column in BOX_SUM_STATS:
            combined[column] = pd.to_numeric(combined[column], errors="coerce").fillna(0)
        totals = combined.groupby(["sbc_team", "fantrax_id", "display_player"], as_index=False)[BOX_SUM_STATS].sum()
        return _recalc(totals)

    def record_changes(self) -> list[dict[str, Any]]:
        """Find franchise leaders who moved from second to first since yesterday."""
        today = self._career_totals(self.as_of)
        yesterday = self._career_totals(self.as_of - timedelta(days=1))
        if today.empty or yesterday.empty:
            return []
        changes = []
        for team in sorted(set(today["sbc_team"].astype(str))):
            current_team = today[today["sbc_team"].astype(str) == team].copy()
            prior_team = yesterday[yesterday["sbc_team"].astype(str) == team].copy()
            if current_team.empty or prior_team.empty:
                continue
            for statistic in ["GP", *CATEGORIES]:
                eligible_today, eligible_prior = current_team.copy(), prior_team.copy()
                if statistic == "TS%":
                    eligible_today = eligible_today[(eligible_today["2PTA"] + eligible_today["3PTA"] + 0.44 * eligible_today["FTA"]) >= 200]
                    eligible_prior = eligible_prior[(eligible_prior["2PTA"] + eligible_prior["3PTA"] + 0.44 * eligible_prior["FTA"]) >= 200]
                elif statistic == "2PT%":
                    eligible_today = eligible_today[eligible_today["2PTA"] >= 100]; eligible_prior = eligible_prior[eligible_prior["2PTA"] >= 100]
                elif statistic == "3PT%":
                    eligible_today = eligible_today[eligible_today["3PTA"] >= 100]; eligible_prior = eligible_prior[eligible_prior["3PTA"] >= 100]
                elif statistic == "FT%":
                    eligible_today = eligible_today[eligible_today["FTA"] >= 100]; eligible_prior = eligible_prior[eligible_prior["FTA"] >= 100]
                if eligible_today.empty or eligible_prior.empty:
                    continue
                current_leader = eligible_today.sort_values([statistic, "display_player"], ascending=[False, True]).iloc[0]
                prior_leader = eligible_prior.sort_values([statistic, "display_player"], ascending=[False, True]).iloc[0]
                if str(current_leader["fantrax_id"]) == str(prior_leader["fantrax_id"]):
                    continue
                passed_now = eligible_today[eligible_today["fantrax_id"].astype(str) == str(prior_leader["fantrax_id"])]
                previous_value = float(passed_now.iloc[0][statistic]) if not passed_now.empty else float(prior_leader[statistic])
                if float(current_leader[statistic]) <= previous_value:
                    continue
                changes.append({
                    "team": team,
                    "statistic": statistic,
                    "new_leader": str(current_leader["display_player"]),
                    "previous_leader": str(prior_leader["display_player"]),
                    "new_value": float(current_leader[statistic]),
                    "previous_value": previous_value,
                    "new_player_id": str(self._bridge.set_index("fantrax_id").get("espn_player_id", pd.Series(dtype=str)).get(str(current_leader["fantrax_id"]), "")),
                    "previous_player_id": str(self._bridge.set_index("fantrax_id").get("espn_player_id", pd.Series(dtype=str)).get(str(prior_leader["fantrax_id"]), "")),
                })
        return changes

    def recap_posts(self, slate: pd.DataFrame, featured: list[pd.Series]) -> list[FantraxPost]:
        posts = []
        for game in featured:
            game_id = str(game.get("Game_ID", ""))
            scored = slate[slate.get("Game_ID", pd.Series(dtype=str)).astype(str) == game_id]
            current = scored.iloc[0].copy() if not scored.empty else game.copy()
            rows = self.matchup_rows(current, self.as_of)
            if rows.empty:
                continue
            players, totals = self.aggregate_players(rows), self.team_totals(rows)
            a, b = str(current["TeamA"]), str(current["TeamB"])
            categories, _, _ = self.category_results(totals, a, b)
            try:
                road, home, _ = select_game_uniforms(current, a, b, lambda team, edition: self._uniform_config(team, edition)[0])
            except Exception:
                road, home = "Icon", "Association"
            kwargs = dict(trend_table=self._trend(current), court_image=self.court(b), road_jersey_image=self.jersey(a, road), home_jersey_image=self.jersey(b, home), road_edition=road, home_edition=home, matchup_date_label=self.period_label())
            posts.append(FantraxPost("matchup_recap", f"sbcfbl-matchup-recap-{game_id}.png", fantrax.build_matchup_recap_image(current, categories, players, **kwargs)))
            posts.append(FantraxPost("mobile_matchup_recap", f"sbcfbl-mobile-matchup-recap-{game_id}.png", fantrax.build_mobile_matchup_recap_image(current, categories, players, **kwargs)))
        return posts

    def period_label(self) -> str:
        def fmt(value): return pd.Timestamp(value).strftime("%b %d").replace(" 0", " ")
        return fmt(self.period.start) if self.period.start == self.period.end else f"{fmt(self.period.start)}-{fmt(self.period.end)}"

    def build_posts(self, kinds: list[str] | None = None) -> tuple[list[FantraxPost], list[str]]:
        kinds = kinds or planned_post_kinds(self.period)
        if self.period is None:
            return [], []
        slate = self.slate()
        if slate.empty:
            return [], kinds
        featured = self.featured(slate)
        assets = None
        posts, skipped = [], []
        season = f"{self.period.year - 1}-{str(self.period.year)[-2:]}"
        generated = datetime.combine(self.as_of, datetime.min.time()).replace(hour=3)
        if "overnight_scores" in kinds:
            progress = fantrax.matchup_period_progress(self.calendar, self.period.year, self.period.period, as_of=self.as_of)
            posts.append(FantraxPost("overnight_scores", f"sbcfbl-overnight-scores-{self.period.year}-p{self.period.period}.png", fantrax.build_live_scoreboard_image(slate, progress, season, self.period_label(), generated)))
        if "mobile_overnight_scores" in kinds:
            progress = fantrax.matchup_period_progress(self.calendar, self.period.year, self.period.period, as_of=self.as_of)
            posts.append(FantraxPost("mobile_overnight_scores", f"sbcfbl-mobile-overnight-scores-{self.period.year}-p{self.period.period}.png", fantrax.build_mobile_live_scoreboard_image(slate, progress, season, self.period_label(), generated)))
        if any(kind in kinds for kind in ("matchup_preview", "mobile_matchup_preview")):
            assets = self.preview_assets(featured)
        if "matchup_preview" in kinds:
            posts.append(FantraxPost("matchup_preview", f"sbcfbl-matchup-preview-{self.period.year}-p{self.period.period}.png", fantrax.build_matchup_preview_image(slate, featured, assets or [], season, self.period_label(), generated)))
        if "mobile_matchup_preview" in kinds:
            posts.append(FantraxPost("mobile_matchup_preview", f"sbcfbl-mobile-matchup-preview-{self.period.year}-p{self.period.period}.png", fantrax.build_mobile_matchup_preview_image(slate, featured, assets or [], season, self.period_label(), generated)))
        if any(kind in kinds for kind in ("standings", "mobile_standings")):
            west, east = self.standings_table("West"), self.standings_table("East")
            postseason = self.schedule[(pd.to_numeric(self.schedule["Year"], errors="coerce") == self.period.year) & (pd.to_numeric(self.schedule["Period"], errors="coerce") < self.period.period) & (self.schedule["Type"].astype(str).isin(["Play-In", "Playoffs"]))].copy()
            projected = postseason.empty
            if "standings" in kinds:
                posts.append(FantraxPost("standings", f"sbcfbl-standings-{self.period.year}-p{self.period.period}.png", fantrax.build_standings_bracket_image(west, east, postseason, season, self.period_label(), projected, generated)))
            if "mobile_standings" in kinds:
                posts.append(FantraxPost("mobile_standings", f"sbcfbl-mobile-standings-{self.period.year}-p{self.period.period}.png", fantrax.build_mobile_standings_image(west, east, postseason, season, self.period_label(), projected, generated)))
        if any(kind in kinds for kind in ("matchup_recap", "mobile_matchup_recap")):
            recap_posts = self.recap_posts(slate, featured)
            posts.extend(post for post in recap_posts if post.kind in kinds)
        if "record_leader" in kinds:
            changes = self.record_changes()
            for change in changes:
                slug = re.sub(r"[^a-z0-9]+", "-", change["new_leader"].lower()).strip("-")
                stat_slug = re.sub(r"[^a-z0-9]+", "-", change["statistic"].lower()).strip("-")
                headshot = lambda player_id: f"https://a.espncdn.com/i/headshots/nba/players/full/{player_id}.png" if player_id else ""
                image = fantrax.build_record_leader_announcement_image(
                    change["team"], change["statistic"], change["new_leader"], change["previous_leader"],
                    change["new_value"], change["previous_value"], headshot(change["new_player_id"]),
                    headshot(change["previous_player_id"]), generated,
                )
                posts.append(FantraxPost("record_leader", f"sbcfbl-record-{change['team'].lower()}-{stat_slug}-{slug}.png", image))
            if not changes:
                skipped.append("record_leader:no-new-record")
        return posts, skipped
