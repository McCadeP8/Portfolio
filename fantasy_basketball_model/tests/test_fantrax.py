from pathlib import Path

from fantasy_basketball.fantrax import FantraxClient


class FakeResponse:
    def __init__(self, payload): self.payload = payload
    def raise_for_status(self): return None
    def json(self): return self.payload


class FakeSession:
    def __init__(self, payload):
        self.payload = payload
        self.headers = {}
    def get(self, *args, **kwargs): return FakeResponse(self.payload)


def test_roster_normalization(tmp_path: Path):
    payload = {"period": 1, "rosters": {"t1": {"teamName": "Team One", "rosterItems": [{"id": "p1", "position": "PG", "status": "ACTIVE"}]}}}
    client = FantraxClient("league", tmp_path, session=FakeSession(payload))
    roster, teams = client.fetch_rosters(1)
    assert roster.loc[0, "fantrax_player_id"] == "p1"
    assert teams.loc[0, "fantasy_team_name"] == "Team One"
    assert len(list(tmp_path.glob("rosters_period_001_*.json"))) == 1

