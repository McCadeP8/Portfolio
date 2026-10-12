import pandas as pd

from fantasy_basketball.matching import match_players, normalize_name


def test_name_normalization_handles_accents_punctuation_and_suffixes():
    assert normalize_name("Nikola Jokić Jr.") == "nikola jokic"
    assert normalize_name("De'Aaron Fox") == "deaaron fox"


def test_fuzzy_match_is_suggestion_only():
    ft = pd.DataFrame([{"fantrax_player_id": "1", "player_name": "Nikola Jokic"}])
    projections = pd.DataFrame([{"player_name": "Nikola Jokic"}, {"player_name": "Nikola Jokik"}])
    matched, exceptions = match_players(ft, projections)
    assert matched.loc[0, "match_method"] == "exact_name"
    assert matched.loc[1, "match_method"] == "unmatched"
    assert pd.isna(matched.loc[1, "fantrax_player_id"])
    assert exceptions.loc[0, "suggested_player_name"] == "Nikola Jokic"


def test_duplicate_name_uses_nba_team_as_exact_tie_breaker():
    ft = pd.DataFrame([
        {"fantrax_player_id": "old", "player_name": "Jalen Johnson", "nba_team": "(N/A)"},
        {"fantrax_player_id": "current", "player_name": "Jalen Johnson", "nba_team": "ATL"},
    ])
    projections = pd.DataFrame([{"player_name": "Jalen Johnson", "nba_team": "ATL"}])
    matched, exceptions = match_players(ft, projections)
    assert matched.loc[0, "fantrax_player_id"] == "current"
    assert matched.loc[0, "match_method"] == "exact_name_team"
    assert exceptions.empty

