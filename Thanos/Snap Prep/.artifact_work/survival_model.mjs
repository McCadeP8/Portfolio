import assert from 'node:assert/strict';

export const POS = ['QB', 'RB', 'WR', 'TE', 'K', 'DST'];
export const DEFAULTS = {
  teams: 18, weeks: 17, activeSlots: 14, irSlots: 2,
  seasonSigma: [0.18, 0.28, 0.25, 0.28, 0.20, 0.25],
  weeklyCV: [0.30, 0.55, 0.60, 0.55, 0.45, 0.75],
  injuryHazard: [0.012, 0.025, 0.020, 0.022, 0.008, 0],
  priorGames: 6, waiverRounds: 1, exemptIrEligible: true,
  championshipWeight: 8,
};
export function rng(seed) {
  return () => { let t = seed += 0x6D2B79F5; t = Math.imul(t ^ t >>> 15, t | 1); t ^= t + Math.imul(t ^ t >>> 7, t | 61); return ((t ^ t >>> 14) >>> 0) / 4294967296; };
}
function normal(r) { return Math.sqrt(-2 * Math.log(Math.max(1e-12, r()))) * Math.cos(2 * Math.PI * r()); }
function logFactor(r, sigma) { return Math.exp(sigma * normal(r) - sigma * sigma / 2); }
function triangular(r, a, m, b) {
  if (b <= a) return m;
  const u = r(); return u < (m - a) / (b - a) ? a + Math.sqrt(u * (b - a) * (m - a)) : b - Math.sqrt((1 - u) * (b - a) * (b - m));
}

// Exact primary-position + W/R/T lineup optimizer. Missing slots score zero.
// Only the supplied pre-game values are read, never this week's realized score.
export function lineup(roster, players, values) {
  const first = [-1, -1, -1, -1, -1, -1], second = [-1, -1, -1, -1, -1, -1];
  let flex = -1;
  for (const id of roster) {
    if (!(values[id] > 0)) continue;
    const pos = players[id].pos;
    let spare = id;
    if (first[pos] < 0 || values[id] > values[first[pos]]) { spare = first[pos]; first[pos] = id; }
    if (pos === 1 || pos === 2) {
      if (spare >= 0 && (second[pos] < 0 || values[spare] > values[second[pos]])) { const prior = second[pos]; second[pos] = spare; spare = prior; }
    }
    if (spare >= 0 && pos >= 1 && pos <= 3 && (flex < 0 || values[spare] > values[flex])) flex = spare;
  }
  const selected = first.filter(id => id >= 0);
  if (second[1] >= 0) selected.push(second[1]);
  if (second[2] >= 0) selected.push(second[2]);
  if (flex >= 0) selected.push(flex);
  return { ids: selected, sum: selected.reduce((s, id) => s + values[id], 0) };
}

function missing(counts) {
  const mins = [1, 2, 2, 1];
  const deficits = mins.map((n, p) => Math.max(0, n - counts[p]));
  return deficits.reduce((a, b) => a + b, 0) + Math.max(0, 6 - counts[1] - counts[2] - counts[3] - deficits[1] - deficits[2] - deficits[3]);
}

export function draft(players, boardIds, seed, cfg = DEFAULTS) {
  const r = rng(seed), teams = Array.from({ length: cfg.teams }, () => []);
  const counts = teams.map(() => [0, 0, 0, 0, 0, 0]);
  const free = new Set(boardIds), mins = [1, 2, 2, 1];
  const tastes = teams.map(() => players.map(p => Math.log(Math.max(1, p.marketRank)) + normal(r) * 0.27));
  for (let round = 0; round < 14; round++) for (let k = 0; k < cfg.teams; k++) {
    const t = round % 2 ? cfg.teams - 1 - k : k;
    const deficits = mins.map((n, p) => counts.reduce((s, c) => s + Math.max(0, n - c[p]), 0));
    const available = POS.map((_, p) => [...free].filter(id => players[id].pos === p).length);
    let best = -1, priority = Infinity;
    for (const id of free) {
      const p = players[id].pos;
      if (round < 12) {
        if (p >= 4 || ((p === 0 || p === 3) && counts[t][p] >= 2)) continue;
        if (counts[t][p] >= mins[p] && available[p] <= deficits[p]) continue;
        const next = counts[t].slice(); next[p]++;
        if (missing(next) > 11 - round) continue;
      } else if (p < 4 || counts[t][p] > 0) continue;
      if (tastes[t][id] < priority) { best = id; priority = tastes[t][id]; }
    }
    assert(best >= 0, `Draft has no legal choice in round ${round + 1}, team ${t}`);
    teams[t].push(best); counts[t][players[best].pos]++; free.delete(best);
  }
  assert.equal(free.size, 0);
  for (let t = 0; t < teams.length; t++) {
    assert.equal(teams[t].length, 14); assert.equal(missing(counts[t]), 0);
    assert.equal(counts[t][4], 1); assert.equal(counts[t][5], 1);
  }
  return teams;
}

export function world(players, seed, cfg = DEFAULTS) {
  const r = rng(seed), n = players.length;
  const jacobs = players.findIndex(p => p.key === 'joshjacobs');
  const lloyd = players.findIndex(p => p.key === 'marshawnlloyd');
  const u = r(), returnWeek = u < .15 ? 5 : u < .40 ? 9 : u < .75 ? 13 : 18;
  const latent = players.map(p => triangular(r, p.low, p.mean, p.high) / 17 * logFactor(r, cfg.seasonSigma[p.pos]));
  const prior = players.map(p => p.mean / 17), observed = new Float64Array(n), games = new Int16Array(n);
  const endInjury = new Int16Array(n), longInjury = new Uint8Array(n);
  const forecasts = [], keep = [], actuals = [], irEligible = [], orders = [];
  // Calibrate Lloyd's absent/present role split to the updated season projection,
  // rather than discounting that already-updated projection for Jacobs twice.
  const lloydLeadScale = 16 / (16 - .6 * (12 * .15 + 8 * .25 + 5 * .35));
  for (let w = 1; w <= cfg.weeks; w++) {
    const f = new Float64Array(n), k = new Float64Array(n), a = new Float64Array(n), ir = new Uint8Array(n);
    for (let id = 0; id < n; id++) {
      const p = players[id];
      const role = id === lloyd ? lloydLeadScale * (w >= returnWeek ? .4 : 1) : 1;
      // Injuries are announced before lineups; long injury spells can use IR.
      if (endInjury[id] < w && p.bye !== w && r() < cfg.injuryHazard[p.pos]) {
        const severity = r(), duration = severity < .65 ? 1 : severity < .90 ? 3 : 6;
        endInjury[id] = w + duration - 1;
        longInjury[id] = Number(duration >= 4);
      }
      const exempt = id === jacobs && w < returnWeek;
      const injured = endInjury[id] >= w;
      ir[id] = Number((injured && longInjury[id]) || (exempt && cfg.exemptIrEligible));
      const learned = (cfg.priorGames * prior[id] + observed[id]) / (cfg.priorGames + games[id]);
      k[id] = learned * role * (exempt ? .35 : injured ? .65 : 1);
      if (p.bye === w || injured || exempt) continue;
      f[id] = learned * role;
      const sigma = Math.sqrt(Math.log(1 + cfg.weeklyCV[p.pos] ** 2));
      a[id] = p.pos === 5 ? Math.max(-8, latent[id] * role + normal(r) * Math.max(3, latent[id] * cfg.weeklyCV[p.pos])) : latent[id] * role * logFactor(r, sigma);
    }
    // Freeze decisions before using any current-week observations.
    forecasts.push(f); keep.push(k); actuals.push(a); irEligible.push(ir);
    orders.push(POS.map((_, p) => players.filter(x => x.pos === p).map(x => x.id).sort((x, y) => f[y] - f[x] || x - y)));
    for (let id = 0; id < n; id++) if (f[id] > 0) {
      const role = id === lloyd ? lloydLeadScale * (w >= returnWeek ? .4 : 1) : 1;
      observed[id] += a[id] / role; games[id]++;
    }
  }
  const priority = Array.from({ length: cfg.teams }, (_, t) => t);
  for (let i = priority.length - 1; i > 0; i--) { const j = Math.floor(r() * (i + 1)); [priority[i], priority[j]] = [priority[j], priority[i]]; }
  return { forecasts, keep, actuals, irEligible, orders, priority, returnWeek };
}

function utility(roster, players, f, k) {
  return lineup(roster, players, f).sum + .25 * lineup(roster, players, k).sum + .04 * roster.reduce((s, id) => s + k[id], 0);
}

function trim(roster, players, f, k, owner, activeSlots) {
  while (roster.length > activeSlots) {
    let drop = -1, best = -Infinity;
    for (const id of roster) {
      const value = utility(roster.filter(x => x !== id), players, f, k);
      if (value > best) { best = value; drop = id; }
    }
    roster.splice(roster.indexOf(drop), 1); owner[drop] = -1;
  }
}

export function runLeague(players, initial, wld, cfg = DEFAULTS, removeId = -1, details = false) {
  const rosters = initial.map(x => x.slice()), irs = initial.map(() => []);
  const owner = new Int16Array(players.length).fill(-1), original = new Int16Array(players.length).fill(-1);
  for (let t = 0; t < initial.length; t++) for (const id of initial[t]) owner[id] = original[id] = t;
  if (removeId >= 0) {
    const t = owner[removeId]; assert(t >= 0);
    rosters[t].splice(rosters[t].indexOf(removeId), 1); owner[removeId] = -2;
    const replacement = wld.orders[0][players[removeId].pos].find(id => owner[id] === -1);
    if (replacement !== undefined) { rosters[t].push(replacement); owner[replacement] = t; }
  }
  const alive = new Set(initial.map((_, t) => t)), eliminated = new Int16Array(initial.length).fill(18);
  const starts = new Int16Array(players.length), opportunities = new Int16Array(players.length);
  const ownPoints = new Float64Array(players.length), lateStarts = new Int16Array(players.length), lateOpp = new Int16Array(players.length);
  const logs = [], weekCounts = [];
  for (let w = 0; w < cfg.weeks; w++) {
    const f = wld.forecasts[w], k = wld.keep[w], eligibility = wld.irEligible[w];
    weekCounts.push(alive.size);
    for (const t of alive) {
      for (const id of irs[t].slice()) if (!eligibility[id]) { irs[t].splice(irs[t].indexOf(id), 1); rosters[t].push(id); }
      for (const id of rosters[t].slice()) if (eligibility[id] && irs[t].length < cfg.irSlots) { rosters[t].splice(rosters[t].indexOf(id), 1); irs[t].push(id); }
      trim(rosters[t], players, f, k, owner, cfg.activeSlots);
    }
    // One claim per survivor per round; later rounds/weeks rotate priority.
    for (let round = 0; round < cfg.waiverRounds; round++) for (let z = 0; z < cfg.teams; z++) {
      const t = wld.priority[(z + w + round) % cfg.teams]; if (!alive.has(t)) continue;
      const roster = rosters[t], base = utility(roster, players, f, k);
      const selected = lineup(roster, players, f).ids;
      const bench = roster.filter(id => !selected.includes(id)).sort((a, b) => k[a] - k[b]);
      let bestGain = 0.01, add = -1, drop = -1;
      for (let pos = 0; pos < 6; pos++) {
        const candidate = wld.orders[w][pos].find(id => owner[id] === -1 && f[id] > 0);
        if (candidate === undefined) continue;
        const same = roster.filter(id => players[id].pos === pos).sort((a, b) => k[a] - k[b]);
        const drops = roster.length < cfg.activeSlots ? [-1] : [...new Set([bench[0], same[0]].filter(id => id !== undefined))];
        for (const d of drops) {
          const test = roster.filter(id => id !== d); test.push(candidate);
          const gain = utility(test, players, f, k) - base;
          if (gain > bestGain) { bestGain = gain; add = candidate; drop = d; }
        }
      }
      if (add >= 0) {
        if (drop >= 0) { roster.splice(roster.indexOf(drop), 1); owner[drop] = -1; }
        roster.push(add); owner[add] = t;
      }
    }
    let loser = -1, low = Infinity;
    for (const t of alive) {
      const selected = lineup(rosters[t], players, f).ids;
      const score = selected.reduce((s, id) => s + wld.actuals[w][id], 0);
      if (score < low || (score === low && t < loser)) { low = score; loser = t; }
      if (details) {
        for (const id of initial[t]) if (f[id] > 0) { opportunities[id]++; if (w >= 13) lateOpp[id]++; }
        for (const id of selected) if (original[id] === t) { starts[id]++; ownPoints[id] += wld.actuals[w][id]; if (w >= 13) lateStarts[id]++; }
      }
    }
    if (details) {
      const all = [...alive].flatMap(t => [...rosters[t], ...irs[t]]);
      assert.equal(new Set(all).size, all.length, 'Duplicate ownership');
      for (const t of alive) { assert(rosters[t].length <= cfg.activeSlots); assert(irs[t].length <= cfg.irSlots); }
    }
    assert(loser >= 0); eliminated[loser] = w + 1; alive.delete(loser);
    for (const id of [...rosters[loser], ...irs[loser]]) owner[id] = -1;
    if (details) logs.push({ week: w + 1, teams: weekCounts[w], eliminatedTeam: loser, score: low, released: rosters[loser].length + irs[loser].length });
    if (removeId >= 0 && loser === original[removeId] && !details) {
      return { eliminated, champion: -1, original, starts, opportunities, ownPoints, lateStarts, lateOpp, logs };
    }
  }
  assert.equal(alive.size, 1); assert.deepEqual(weekCounts, Array.from({ length: 17 }, (_, w) => 18 - w));
  const champion = [...alive][0];
  return { eliminated, champion, original, starts, opportunities, ownPoints, lateStarts, lateOpp, logs };
}

export function evaluate(players, boardIds, trials, seed, cfg = DEFAULTS, progress = () => {}, targetIds = boardIds) {
  const metrics = players.map(() => ({ n: 0, gain: 0, gain2: 0, weeks: 0, wins: 0, starts: 0, opp: 0, points: 0, lateStarts: 0, lateOpp: 0 }));
  let example = null;
  for (let s = 0; s < trials; s++) {
    const initial = draft(players, boardIds, seed + s * 131 + 1, cfg);
    const wld = world(players, seed + s * 131 + 2, cfg);
    const baseline = runLeague(players, initial, wld, cfg, -1, true);
    if (s === 0) example = baseline.logs;
    for (const id of targetIds) {
      const t = baseline.original[id];
      const counter = runLeague(players, initial, wld, cfg, id);
      const weeks = Math.min(17, baseline.eliminated[t]) - Math.min(17, counter.eliminated[t]);
      const win = Number(baseline.champion === t) - Number(counter.champion === t);
      const gain = weeks + cfg.championshipWeight * win;
      const m = metrics[id]; m.n++; m.gain += gain; m.gain2 += gain * gain; m.weeks += weeks; m.wins += win;
      m.starts += baseline.starts[id]; m.opp += baseline.opportunities[id]; m.points += baseline.ownPoints[id];
      m.lateStarts += baseline.lateStarts[id]; m.lateOpp += baseline.lateOpp[id];
    }
    if ((s + 1) % 8 === 0 || s === trials - 1) progress(s + 1, trials);
  }
  return { metrics, example, cfg, trials, seed };
}
