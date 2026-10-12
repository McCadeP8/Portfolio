from pathlib import Path

from fantasy_basketball.projections import import_projections


def test_projection_aliases_and_raw_preservation(tmp_path: Path):
    source = Path(__file__).parent / "fixtures" / "projections.csv"
    result, missing, preserved = import_projections(source, tmp_path, snapshot_date="2026-10-09")
    assert list(result["player_name"]) == ["Nikola Jokic", "Luka Doncic"]
    assert result.loc[0, "three_m"] == 1.1
    assert "fg_m" not in missing
    assert preserved.exists()


def test_messy_shooting_cells_repeated_headers_and_derived_stats(tmp_path: Path):
    source = Path(__file__).parent / "fixtures" / "messy_projections.csv"
    result, missing, _ = import_projections(
        source,
        tmp_path,
        snapshot_date="2026-10-09",
        stat_basis="season_total",
        minutes_basis="per_game",
    )
    assert len(result) == 2
    jokic = result.iloc[0]
    assert jokic["fg_m"] == 754.6
    assert jokic["fg_a"] == 1317.6
    assert round(jokic["two_m"], 1) == 622.8
    assert round(jokic["two_a"], 1) == 987.1
    expected_ts = 2042.6 / (2 * (1317.6 + 0.44 * 491.8))
    assert abs(jokic["ts_pct"] - expected_ts) < 1e-12
    assert jokic["stat_basis"] == "season_total"

