from yahoo_2026 import extract_league_id, normalize_matchups, normalize_teams


CONFIG = {"league_label": "Test", "draft_type": "snake", "league_id": "123"}


def team_node(team_id="1", name="Alpha", points=None):
    team = [[
        {"team_key": f"470.l.123.t.{team_id}"}, {"team_id": team_id}, {"name": name},
        {"url": f"https://example.test/{team_id}"},
        {"team_logos": [{"team_logo": {"url": "logo.png"}}]},
        {"managers": [{"manager": {"nickname": "Owner", "guid": "abc"}}]},
    ]]
    if points is not None:
        team.append({"team_points": {"total": str(points)}, "team_projected_points": {"total": "100"}})
    return {"team": team}


def test_extract_league_id_ignores_team_suffix():
    assert extract_league_id("https://football.fantasysports.yahoo.com/f1/436157/1") == "436157"
    assert extract_league_id("328829") == "328829"


def test_normalize_teams():
    payload = {"fantasy_content": {"league": [
        {"league_key": "470.l.123"},
        {"teams": {"0": team_node(), "count": 1}},
    ]}}
    rows = normalize_teams(payload, CONFIG, "now")
    assert rows[0]["team_name"] == "Alpha"
    assert rows[0]["manager_nickname"] == "Owner"
    assert rows[0]["logo_url"] == "logo.png"


def test_normalize_matchups():
    matchup = {
        "week": "1", "status": "midevent",
        "0": {"teams": {"0": team_node("1", "Alpha", 12.5), "1": team_node("2", "Beta", 8), "count": 2}},
    }
    payload = {"fantasy_content": {"league": [
        {"league_key": "470.l.123"},
        {"scoreboard": {"week": 1, "0": {"matchups": {"0": {"matchup": matchup}, "count": 1}}}},
    ]}}
    rows = normalize_matchups(payload, CONFIG, "now")
    assert rows[0]["team_1_name"] == "Alpha"
    assert rows[0]["team_2_name"] == "Beta"
    assert rows[0]["team_1_points"] == 12.5
