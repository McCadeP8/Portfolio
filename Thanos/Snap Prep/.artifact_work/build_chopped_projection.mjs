import fs from "node:fs/promises";
import path from "node:path";
import { Workbook } from "@oai/artifact-tool";

const root = path.resolve("..");
const projectionPath = path.join(root, "data", "base", "player_stat_projections_2026.csv");
const byePath = path.resolve(
  root,
  "..",
  "..",
  "Smack Talkers Prep",
  "output",
  "csv",
  "Smack_Talkers_2026_Combined_Rankings_Notes.csv",
);
const outputPath = path.join(root, "chopped_league_starting_points_2026.csv");
const previewPath = path.join(root, ".artifact_work", "chopped_projection_preview.png");

function number(value) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : 0;
}

function key(value) {
  return String(value ?? "")
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]/g, "");
}

function normalizeTeam(value) {
  const team = String(value ?? "").trim().toUpperCase();
  return team === "JAX" ? "JAC" : team;
}

function rowsToObjects(values) {
  const [headers, ...rows] = values;
  return rows
    .filter((row) => row.some((cell) => cell !== null && cell !== ""))
    .map((row) => Object.fromEntries(headers.map((header, index) => [String(header), row[index]])));
}

async function importCsvObjects(filePath, sheetName) {
  const text = await fs.readFile(filePath, "utf8");
  const workbook = await Workbook.fromCSV(text, { sheetName });
  const sheet = workbook.worksheets.getItem(sheetName);
  return rowsToObjects(sheet.getUsedRange(true).values);
}

function projectedPoints(row) {
  if (row.position === "K" || row.position === "DST") {
    return number(row.fantasypros_points);
  }

  return (
    number(row.pass_yards) / 25
    + number(row.pass_tds) * 6
    - number(row.interceptions) * 2
    + number(row.rush_yards) / 10
    + number(row.rush_tds) * 6
    + number(row.receptions) * 0.5
    + number(row.receiving_yards) / 10
    + number(row.receiving_tds) * 6
    - number(row.fumbles_lost) * 2
  );
}

function rankPlayers(players) {
  return [...players].sort(
    (a, b) => b.seasonPoints - a.seasonPoints || a.player.localeCompare(b.player),
  );
}

function takeTop(players, position, count, selected) {
  const eligible = rankPlayers(
    players.filter((player) => player.position === position && !selected.has(player.id)),
  ).slice(0, count);
  for (const player of eligible) selected.add(player.id);
  return eligible;
}

function csvEscape(value) {
  if (typeof value === "number") return String(value);
  const text = String(value ?? "");
  return /[",\r\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
}

const projectionRows = await importCsvObjects(projectionPath, "Projection Source");
const byeRows = await importCsvObjects(byePath, "Bye Source");

const byeByTeam = new Map();
const byeByPlayer = new Map();
for (const row of byeRows) {
  const bye = number(row["Bye Week"]);
  const team = normalizeTeam(row.Team);
  if (team && bye) byeByTeam.set(team, bye);
  if (row.Player && bye) byeByPlayer.set(key(row.Player), bye);
}

const players = projectionRows
  .filter((row) => String(row.scenario).toLowerCase() === "consensus")
  .map((row) => {
    const player = String(row.player).trim();
    const position = String(row.position).trim().toUpperCase();
    const team = normalizeTeam(row.team);
    const seasonPoints = projectedPoints({ ...row, position });
    return {
      id: `${position}:${key(player)}`,
      position,
      player,
      team,
      bye: byeByPlayer.get(key(player)) || byeByTeam.get(team) || 0,
      seasonPoints,
      weeklyPoints: seasonPoints / 17,
    };
  })
  .filter((player) => ["QB", "RB", "WR", "TE", "K", "DST"].includes(player.position));

const initialSelected = new Set();
const initialPool = [];
for (const [position, count] of [["QB", 18], ["RB", 36], ["WR", 36], ["TE", 18], ["K", 18], ["DST", 18]]) {
  initialPool.push(...takeTop(players, position, count, initialSelected));
}
const flex = rankPlayers(
  players.filter(
    (player) => ["RB", "WR", "TE"].includes(player.position) && !initialSelected.has(player.id),
  ),
).slice(0, 18);
for (const player of flex) initialSelected.add(player.id);
initialPool.push(...flex);

if (initialPool.length !== 162 || new Set(initialPool.map((player) => player.id)).size !== 162) {
  throw new Error(`Expected 162 unique Week 1 starters; found ${initialPool.length}.`);
}

const outputById = new Map(
  initialPool.map((player) => [player.id, { ...player, weeks: Array(17).fill(0) }]),
);

for (let week = 1; week <= 17; week += 1) {
  const teams = 19 - week;
  const active = initialPool.filter((player) => player.bye !== week);
  const selected = new Set();

  for (const [position, count] of [["QB", teams], ["RB", teams * 2], ["WR", teams * 2], ["TE", teams], ["K", teams], ["DST", teams]]) {
    const picked = takeTop(active, position, count, selected);
    if (picked.length !== count) {
      throw new Error(`Week ${week}: needed ${count} ${position}, found ${picked.length}.`);
    }
  }

  const flexPicked = rankPlayers(
    active.filter(
      (player) => ["RB", "WR", "TE"].includes(player.position) && !selected.has(player.id),
    ),
  ).slice(0, teams);
  if (flexPicked.length !== teams) {
    throw new Error(`Week ${week}: needed ${teams} flex players, found ${flexPicked.length}.`);
  }
  for (const player of flexPicked) selected.add(player.id);

  if (selected.size !== teams * 9) {
    throw new Error(`Week ${week}: expected ${teams * 9} starters, selected ${selected.size}.`);
  }
  for (const id of selected) outputById.get(id).weeks[week - 1] = outputById.get(id).weeklyPoints;
}

const positionOrder = new Map([["QB", 0], ["RB", 1], ["WR", 2], ["TE", 3], ["K", 4], ["DST", 5]]);
const outputRows = [...outputById.values()]
  .map((player) => ({
    ...player,
    total: player.weeks.reduce((sum, points) => sum + points, 0),
  }))
  .sort(
    (a, b) => positionOrder.get(a.position) - positionOrder.get(b.position)
      || b.total - a.total
      || a.player.localeCompare(b.player),
  );

const headers = ["position", "player", ...Array.from({ length: 17 }, (_, i) => `Week ${i + 1}`), "total"];
const matrix = [
  headers,
  ...outputRows.map((player) => [
    player.position,
    player.player,
    ...player.weeks.map((value) => Math.round(value * 100) / 100),
    Math.round(player.total * 100) / 100,
  ]),
];

const workbook = Workbook.create();
const sheet = workbook.worksheets.add("Chopped Projections");
sheet.getRangeByIndexes(0, 0, matrix.length, headers.length).values = matrix;
sheet.freezePanes.freezeRows(1);
sheet.showGridLines = false;
sheet.getRange(`A1:T1`).format = {
  fill: "#3B1E54",
  font: { bold: true, color: "#FFFFFF" },
};
sheet.getRange(`C2:T${matrix.length}`).format.numberFormat = "0.00";
sheet.getRange(`A1:T${matrix.length}`).format.autofitColumns();
sheet.getRange("A:A").format.columnWidth = 10;
sheet.getRange("B:B").format.columnWidth = 24;

const inspected = await workbook.inspect({
  kind: "table",
  range: "Chopped Projections!A1:T12",
  include: "values,formulas",
  tableMaxRows: 12,
  tableMaxCols: 20,
});
console.log(inspected.ndjson);

const errors = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
  options: { useRegex: true, maxResults: 50 },
  summary: "final formula error scan",
});
console.log(errors.ndjson);

const preview = await workbook.render({
  sheetName: "Chopped Projections",
  range: "A1:T18",
  scale: 1,
  format: "png",
});
await fs.writeFile(previewPath, new Uint8Array(await preview.arrayBuffer()));

const writtenValues = sheet.getRangeByIndexes(0, 0, matrix.length, headers.length).values;
const csv = `${writtenValues.map((row) => row.map(csvEscape).join(",")).join("\r\n")}\r\n`;
await fs.writeFile(outputPath, csv, "utf8");

const counts = Object.fromEntries(
  [...positionOrder.keys()].map((position) => [
    position,
    outputRows.filter((player) => player.position === position).length,
  ]),
);
const weeklyStarterCounts = Array.from({ length: 17 }, (_, index) => {
  const week = index + 1;
  return outputRows.filter((player) => player.weeks[index] > 0).length;
});
console.log(JSON.stringify({
  outputPath,
  rows: outputRows.length,
  counts,
  flexCounts: {
    RB: counts.RB - 36,
    WR: counts.WR - 36,
    TE: counts.TE - 18,
  },
  weeklyStarterCounts,
  missingByes: outputRows.filter((player) => !player.bye).map((player) => player.player),
}, null, 2));
