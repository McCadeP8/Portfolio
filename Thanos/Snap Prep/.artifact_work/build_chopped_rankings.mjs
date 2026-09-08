import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import { fileURLToPath } from 'node:url';
import { Workbook } from '@oai/artifact-tool';
import { POS, DEFAULTS, evaluate } from './survival_model.mjs';

const work = path.dirname(fileURLToPath(import.meta.url)), root = path.resolve(work, '..');
const args = process.argv.slice(2);
const option = (name, fallback) => args.find(a => a.startsWith(`--${name}=`))?.split('=').slice(1).join('=') ?? fallback;
const trials = Number(option('trials', '256')), seed = Number(option('seed', '20260904'));
const resultsFile = path.join(work, option('results', 'results_survival.json'));
const key = v => String(v ?? '').normalize('NFKD').replace(/[\u0300-\u036f]/g, '').toLowerCase().replace(/[^a-z0-9]/g, '');
const team = v => String(v ?? '').toUpperCase().replace(/^JAX$/, 'JAC');
const num = v => { const n = Number(v); assert(Number.isFinite(n), `Invalid number ${v}`); return n; };
const round = (v, digits = 2) => Math.round(v * 10 ** digits) / 10 ** digits;
async function csvRows(name) {
  const wb = await Workbook.fromCSV(await fs.readFile(path.join(root, 'data/base', name), 'utf8'), { sheetName: 'Source' });
  const [headers, ...values] = wb.worksheets.getItemAt(0).getUsedRange(true).values;
  return values.filter(row => row[0]).map(row => Object.fromEntries(headers.map((h, j) => [h, row[j]])));
}
function points(r) {
  if (r.position === 'K' || r.position === 'DST') return num(r.fantasypros_points);
  return num(r.pass_yards) / 25 + 6 * num(r.pass_tds) - 2 * num(r.interceptions) + num(r.rush_yards) / 10 + 6 * num(r.rush_tds)
    + .5 * num(r.receptions) + num(r.receiving_yards) / 10 + 6 * num(r.receiving_tds) - 2 * num(r.fumbles_lost);
}
async function inputs() {
  const old = await csvRows('previous_chopped_rankings_2026.csv'), reference = await csvRows('league_reference_2026.csv'), source = await csvRows('player_stat_projections_2026.csv');
  const byTeam = new Map(reference.map(r => [team(r.Team), num(r['Bye Week'])]));
  const byName = new Map(reference.map(r => [key(r.Player), r])), oldByName = new Map(old.map(r => [key(r.player), r]));
  const dstTeams = ['ARI','ATL','BAL','BUF','CAR','CHI','CIN','CLE','DAL','DEN','DET','GB','HOU','IND','JAC','KC','LV','LAC','LAR','MIA','MIN','NE','NO','NYG','NYJ','PHI','PIT','SF','SEA','TB','TEN','WAS'];
  const dstNames = ['Arizona Cardinals','Atlanta Falcons','Baltimore Ravens','Buffalo Bills','Carolina Panthers','Chicago Bears','Cincinnati Bengals','Cleveland Browns','Dallas Cowboys','Denver Broncos','Detroit Lions','Green Bay Packers','Houston Texans','Indianapolis Colts','Jacksonville Jaguars','Kansas City Chiefs','Las Vegas Raiders','Los Angeles Chargers','Los Angeles Rams','Miami Dolphins','Minnesota Vikings','New England Patriots','New Orleans Saints','New York Giants','New York Jets','Philadelphia Eagles','Pittsburgh Steelers','San Francisco 49ers','Seattle Seahawks','Tampa Bay Buccaneers','Tennessee Titans','Washington Commanders'];
  const dst = new Map(dstNames.map((n, i) => [key(n), dstTeams[i]])), groups = new Map();
  for (const r of source) { const id = `${r.position}:${key(r.player)}`; if (!groups.has(id)) groups.set(id, {}); groups.get(id)[r.scenario] = r; }
  const players = [], excluded = [];
  for (const group of groups.values()) {
    const r = group.consensus; if (!r) continue;
    const nameKey = key(r.player), prev = oldByName.get(nameKey), ref = byName.get(nameKey);
    const nflTeam = nameKey === 'kalebjohnson' ? 'GB' : team(r.team) || dst.get(nameKey) || team(ref?.Team), bye = byTeam.get(nflTeam);
    if (!bye) { excluded.push(r.player); continue; }
    const override = prev && ['marshawnlloyd','kalebjohnson','chrisbrooks'].includes(nameKey);
    const mean = override ? num(prev.baseline_half_ppr_projection) : points(r);
    if (mean <= 0 && !prev) { excluded.push(r.player); continue; }
    const low = override ? num(prev.projection_floor) : Math.min(mean, points(group.low ?? r));
    const high = override ? num(prev.projection_ceiling) : Math.max(mean, points(group.high ?? r));
    const marketRank = ref && Number(ref['External Average Rank']) > 0 ? num(ref['External Average Rank']) : prev ? num(prev.chopped_rank) : 1000 + 300 / mean;
    players.push({ id: players.length, key: nameKey, player: r.player, pos: POS.indexOf(r.position), team: nflTeam, bye, mean, low, high,
      marketRank: nameKey === 'joshjacobs' ? 170 : nameKey === 'marshawnlloyd' ? 106 : marketRank,
      previousRank: prev ? num(prev.chopped_rank) : null, source: prev?.source_url ?? '', news: prev?.news_adjustment ?? '' });
  }
  const boardIds = players.filter(p => p.previousRank !== null).map(p => p.id);
  assert.equal(boardIds.length, 252, `Missing original players: ${old.filter(r => !players.some(p => p.key === key(r.player))).map(r => r.player).join(', ')}`);
  return { players, boardIds, excluded };
}
let result;
if (args.includes('--export')) result = JSON.parse(await fs.readFile(resultsFile, 'utf8'));
else {
  const data = await inputs();
  const config = { ...DEFAULTS, waiverRounds: Number(option('waiver-rounds', '1')), exemptIrEligible: option('exempt-ir', 'true') === 'true' };
  const focus = option('focus', '').split(',').filter(Boolean);
  const targetIds = focus.length ? data.boardIds.filter(id => focus.includes(data.players[id].key)) : data.boardIds;
  console.log(JSON.stringify({ trials, pairedRuns: trials * targetIds.length, eligiblePlayers: data.players.length, excludedInputs: data.excluded, config }));
  const started = Date.now();
  result = { ...data, ...evaluate(data.players, data.boardIds, trials, seed, config,
    (n, total) => console.log(`Completed ${n}/${total} matched league worlds; elapsed ${Math.round((Date.now() - started) / 1000)} seconds`), targetIds), elapsedSeconds: (Date.now() - started) / 1000 };
  await fs.writeFile(resultsFile, JSON.stringify(result));
  if (args.includes('--simulate-only')) process.exit(0);
}
const { players, boardIds, metrics } = result;
const ordered = boardIds.map(id => {
  const p = players[id], m = metrics[id], value = m.gain / m.n;
  const se = Math.sqrt(Math.max(0, (m.gain2 - m.gain * m.gain / m.n) / (m.n - 1)) / m.n);
  return { ...p, m, value, se };
}).sort((a, b) => b.value - a.value || a.previousRank - b.previousRank);
const counts = {};
const headers = ['chopped_rank','position','position_rank','player','previous_rank','rank_change','survival_score_gain','score_mc_se',
  'survival_weeks_gain','championship_lift_pct','start_when_alive_available_pct','late_start_when_alive_available_pct',
  'expected_original_team_starts','expected_original_team_points','paired_trials','team','bye','baseline_half_ppr_points','ir_note','news_snapshot','source_url'];
const matrix = [headers, ...ordered.map((p, i) => {
  const m = p.m, position = POS[p.pos]; counts[position] = (counts[position] ?? 0) + 1;
  return [i + 1, position, counts[position], p.player, p.previousRank, p.previousRank - i - 1, round(p.value, 3), round(p.se, 3),
    round(m.weeks / m.n, 3), round(100 * m.wins / m.n, 2), m.opp ? round(100 * m.starts / m.opp, 1) : 0,
    m.lateOpp ? round(100 * m.lateStarts / m.lateOpp, 1) : 0, round(m.starts / m.n), round(m.points / m.n), m.n, p.team, p.bye, round(p.mean),
    p.key === 'joshjacobs' ? `Exempt IR eligibility assumed ${result.cfg.exemptIrEligible}; no fixed return date` : '', p.news, p.source];
})];
assert.equal(matrix.length, 253); assert.equal(new Set(matrix.slice(1).map(r => r[3])).size, 252);
assert(matrix.slice(1).every(row => row.every(v => typeof v !== 'number' || Number.isFinite(v))));
const workbook = Workbook.create(), sheet = workbook.worksheets.add('Draft rankings');
sheet.getRangeByIndexes(0, 0, matrix.length, headers.length).values = matrix;
sheet.getRange('A1:U253').format.font = { name: 'Arial', size: 10 };
sheet.getRange('A1:U1').format = { fill: '#3B1E54', font: { bold: true, color: '#FFFFFF' }, wrapText: true, rowHeight: 58 };
sheet.getRange('A1:C253').format.columnWidth = 10; sheet.getRange('D1:D253').format.columnWidth = 23;
sheet.getRange('E1:F253').format.columnWidth = 12; sheet.getRange('G1:N253').format.columnWidth = 17;
sheet.getRange('G2:J253').setNumberFormat('0.000'); sheet.getRange('K2:N253').setNumberFormat('0.0');
sheet.getRange('O1:R253').format.columnWidth = 13; sheet.getRange('S1:U253').format.columnWidth = 40;
sheet.freezePanes.freezeRows(1); sheet.showGridLines = false;
console.log((await workbook.inspect({ kind: 'table', range: 'Draft rankings!A1:L12', tableMaxRows: 12, tableMaxCols: 12 })).ndjson);
console.log((await workbook.inspect({ kind: 'match', searchTerm: '#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!', options: { useRegex: true, maxResults: 30 } })).ndjson);
const preview = await workbook.render({ sheetName: 'Draft rankings', range: 'A1:L18', scale: 1, format: 'png' });
await fs.writeFile(path.join(work, 'chopped_rankings_preview.png'), new Uint8Array(await preview.arrayBuffer()));
const escape = v => /[",\r\n]/.test(String(v ?? '')) ? `"${String(v).replaceAll('"','""')}"` : String(v ?? '');
const values = sheet.getRangeByIndexes(0, 0, matrix.length, headers.length).values;
await fs.writeFile(path.join(root, 'chopped_league_draft_rankings_2026.csv'), values.map(row => row.map(escape).join(',')).join('\r\n') + '\r\n');
console.log(JSON.stringify({ counts, trials: result.trials, focused: ordered.filter(p => ['joshallen','treymcbride','brockbowers','lamarjackson','marshawnlloyd','joshjacobs'].includes(p.key)).map(p => ({ player: p.player, rank: ordered.indexOf(p) + 1, old: p.previousRank, score: round(p.value, 3), se: round(p.se, 3), startPct: round(p.m.starts / p.m.opp * 100, 1) })) }, null, 2));
