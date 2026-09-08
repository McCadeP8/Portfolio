import test from 'node:test';
import assert from 'node:assert/strict';
import { lineup, draft, world, runLeague, DEFAULTS } from './survival_model.mjs';

function fixture() {
  const players = [], board = [];
  const limits = [27, 81, 81, 27, 18, 18];
  for (let p = 0; p < 6; p++) for (let j = 0; j < limits[p] + 8; j++) {
    const id = players.length, mean = 200 - j;
    players.push({ id, key: `p${p}_${j}`, player: `P${p}_${j}`, pos: p, mean, low: mean * .8, high: mean * 1.2, marketRank: j * 6 + p + 1, bye: 5 + j % 10 });
    if (j < limits[p]) board.push(id);
  }
  return { players, board };
}

test('lineup enforces all nine slots and WRT flex without duplicate players', () => {
  const positions = [0, 0, 1, 1, 1, 2, 2, 3, 3, 4, 5];
  const players = positions.map((pos, id) => ({ pos, id }));
  const values = [30, 29, 20, 15, 12, 18, 14, 10, 13, 8, 7];
  const pick = lineup(players.map(x => x.id), players, values);
  assert.equal(pick.ids.length, 9); assert.equal(new Set(pick.ids).size, 9);
  assert(!pick.ids.includes(1)); assert(!pick.ids.includes(7)); assert(pick.ids.includes(4));
});

test('zero availability removes players even when real-world points would be high', () => {
  const players = [{ pos: 0 }, { pos: 0 }];
  assert.deepEqual(lineup([0, 1], players, [0, 10]).ids, [1]);
});

test('snake draft yields 18 legal unique 14-player rosters', () => {
  const { players, board } = fixture();
  for (let seed = 1; seed <= 12; seed++) {
    const rosters = draft(players, board, seed);
    assert.equal(new Set(rosters.flat()).size, 252);
    assert.deepEqual(rosters, draft(players, board, seed));
  }
});

test('weekly engine eliminates exactly one team, releases players, and preserves capacity', () => {
  const { players, board } = fixture();
  const rosters = draft(players, board, 7), w = world(players, 9);
  for (let week = 0; week < 17; week++) for (const p of players) if (p.bye === week + 1) {
    assert.equal(w.forecasts[week][p.id], 0); assert.equal(w.actuals[week][p.id], 0);
  }
  const result = runLeague(players, rosters, w, DEFAULTS, -1, true);
  assert.equal(new Set(result.logs.map(x => x.eliminatedTeam)).size, 17);
  assert.deepEqual(result.logs.map(x => x.teams), Array.from({ length: 17 }, (_, i) => 18 - i));
  assert(result.logs.every(x => x.released >= 13 && x.released <= 16));
  assert.deepEqual(result.eliminated, runLeague(players, rosters, w).eliminated);
  const counter = runLeague(players, rosters, w, DEFAULTS, board[0], true);
  assert.equal(counter.starts[board[0]], 0);
});

test('IR eligibility is conditional, with no free exemption assumed when disabled', () => {
  const players = [{ id: 0, pos: 1, key: 'joshjacobs', mean: 230, low: 210, high: 260, bye: 11 }];
  const w1 = world(players, 20, { ...DEFAULTS, injuryHazard: [0, 0, 0, 0, 0, 0], exemptIrEligible: true });
  const w2 = world(players, 20, { ...DEFAULTS, injuryHazard: [0, 0, 0, 0, 0, 0], exemptIrEligible: false });
  assert.equal(w1.irEligible[0][0], 1); assert.equal(w2.irEligible[0][0], 0);
  assert.equal(w1.forecasts[0][0], 0); assert.equal(w1.actuals[0][0], 0);
});

test('opening forecasts cannot see latent season ability or future weekly scores', () => {
  const { players } = fixture();
  const cfg = { ...DEFAULTS, injuryHazard: [0, 0, 0, 0, 0, 0] };
  const first = world(players, 101, cfg), second = world(players, 202, cfg);
  assert.deepEqual(first.forecasts[0], second.forecasts[0]);
  assert.notDeepEqual(first.actuals[0], second.actuals[0]);
  for (const p of players) {
    const expected = (cfg.priorGames * p.mean / 17 + first.actuals[0][p.id]) / (cfg.priorGames + 1);
    assert(Math.abs(first.forecasts[1][p.id] - expected) < 1e-10);
  }
});
