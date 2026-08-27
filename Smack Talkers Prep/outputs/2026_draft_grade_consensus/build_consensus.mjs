import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const sourcePath = "C:/Users/mppac/Downloads/DraftGrades.csv";
const outputDir = path.resolve(".");
const outputPath = path.join(outputDir, "Smack_Talkers_2026_Consensus_Draft_Grades.xlsx");

function parseCsv(text) {
  const rows = [];
  let row = [], value = "", quoted = false;
  for (let i = 0; i < text.length; i++) {
    const char = text[i];
    if (char === '"') {
      if (quoted && text[i + 1] === '"') { value += '"'; i++; }
      else quoted = !quoted;
    } else if (char === "," && !quoted) {
      row.push(value); value = "";
    } else if ((char === "\n" || char === "\r") && !quoted) {
      if (char === "\r" && text[i + 1] === "\n") i++;
      row.push(value); value = "";
      if (row.some(cell => cell !== "")) rows.push(row);
      row = [];
    } else value += char;
  }
  if (value || row.length) { row.push(value); rows.push(row); }
  return rows;
}

const raw = parseCsv(await fs.readFile(sourcePath, "utf8"));
const headers = raw[0].map(header => header.replace(/^\uFEFF/, "").trim());
const records = raw.slice(1).map(values => Object.fromEntries(headers.map((header, index) => [header, values[index] ?? ""])));

const letterScores = {
  "A+": 98, "A": 95, "A-": 91,
  "B+": 88, "B": 85, "B-": 81,
  "C+": 78, "C": 75, "C-": 71,
  "D+": 68, "D": 65, "D-": 61, "F": 55,
};
const gradeThresholds = [
  [0, "F"], [60, "D-"], [63, "D"], [67, "D+"], [70, "C-"], [73, "C"],
  [77, "C+"], [80, "B-"], [83, "B"], [87, "B+"], [90, "A-"], [93, "A"], [97, "A+"],
];

for (const record of records) {
  record.SiteRank = Number(record.SiteRank);
  const numeric = Number(record.SiteValue);
  record.displayValue = Number.isFinite(numeric) && record.SiteValue.trim() !== "" ? numeric : record.SiteValue;
  record.normalizedScore = Number.isFinite(numeric) && record.SiteValue.trim() !== "" ? numeric : letterScores[record.SiteValue];
}

const siteOrder = {
  Snake: ["FantasyPros", "Yahoo", "FanDraft", "McCade's"],
  Auction: ["FantasyPros", "FanDraft", "McCade's"],
};

function summarizeLeague(league) {
  const sites = siteOrder[league];
  const byTeam = new Map();
  for (const record of records.filter(row => row.League === league)) {
    if (!byTeam.has(record.Team)) byTeam.set(record.Team, {});
    byTeam.get(record.Team)[record.Site] = record;
  }
  const teams = [...byTeam.entries()].map(([team, siteMap]) => {
    const rows = sites.map(site => siteMap[site]);
    if (rows.some(row => !row)) throw new Error(`${league} / ${team} is missing a site grade`);
    const averageRank = rows.reduce((sum, row) => sum + row.SiteRank, 0) / rows.length;
    const averageScore = rows.reduce((sum, row) => sum + row.normalizedScore, 0) / rows.length;
    return { team, siteMap, rows, averageRank, averageScore };
  });
  teams.sort((a, b) => a.averageRank - b.averageRank || b.averageScore - a.averageScore || a.team.localeCompare(b.team));
  return { sites, teams };
}

const summaries = { Snake: summarizeLeague("Snake"), Auction: summarizeLeague("Auction") };
const ownerNames = [...new Set(records.map(row => row.Team))];
const ownerRows = ownerNames.map(owner => {
  const snake = summaries.Snake.teams.find(team => team.team === owner);
  const auction = summaries.Auction.teams.find(team => team.team === owner);
  const available = [snake, auction].filter(Boolean);
  return {
    owner, snake, auction,
    combinedRank: available.reduce((sum, row) => sum + row.averageRank, 0) / available.length,
    formats: snake && auction ? "Both" : snake ? "Snake" : "Auction",
  };
}).sort((a, b) => a.combinedRank - b.combinedRank || a.owner.localeCompare(b.owner));

const workbook = Workbook.create();
const snakeSheet = workbook.worksheets.add("Snake Consensus");
const auctionSheet = workbook.worksheets.add("Auction Consensus");
const overallSheet = workbook.worksheets.add("Overall Summary");
const sourceSheet = workbook.worksheets.add("Source Grades");
const methodologySheet = workbook.worksheets.add("Methodology");

const navy = "#0B1F3A", blue = "#2E75B6", sky = "#DCEAF7", gold = "#E3B341";
const ink = "#172033", muted = "#5F6B7A", light = "#F5F7FA", white = "#FFFFFF";

function scoreColor(score) {
  const low = [248, 105, 107], mid = [255, 224, 130], high = [99, 190, 123];
  const bounded = Math.max(55, Math.min(100, score));
  const t = (bounded - 55) / 45;
  const from = t < 0.5 ? low : mid, to = t < 0.5 ? mid : high, local = t < 0.5 ? t * 2 : (t - 0.5) * 2;
  const rgb = from.map((value, index) => Math.round(value + (to[index] - value) * local));
  return `#${rgb.map(value => value.toString(16).padStart(2, "0")).join("")}`;
}

function rankColor(rank) {
  return scoreColor(100 - (rank - 1) * (45 / 11));
}

function applyBase(sheet, titleRange, title, subtitle, widthMap) {
  sheet.showGridLines = false;
  titleRange.merge();
  titleRange.values = [[title]];
  titleRange.format = { fill: navy, font: { bold: true, color: white, size: 22 }, verticalAlignment: "center" };
  titleRange.format.rowHeightPx = 40;
  const subtitleRange = titleRange.offset(1, 0);
  subtitleRange.merge();
  subtitleRange.values = [[subtitle]];
  subtitleRange.format = { fill: "#EAF1F8", font: { color: muted, italic: true, size: 11 }, wrapText: true, verticalAlignment: "center" };
  subtitleRange.format.rowHeightPx = 34;
  for (const [column, pixels] of Object.entries(widthMap)) sheet.getRange(`${column}1:${column}40`).format.columnWidthPx = pixels;
}

function addRankGradient(range) {
  range.conditionalFormats.add("colorScale", {
    criteria: [
      { type: "lowestValue", color: "#63BE7B" },
      { type: "percentile", value: 50, color: "#FFEB84" },
      { type: "highestValue", color: "#F8696B" },
    ],
  });
}

function addScoreGradient(range) {
  range.conditionalFormats.add("colorScale", {
    criteria: [
      { type: "lowestValue", color: "#F8696B" },
      { type: "percentile", value: 50, color: "#FFEB84" },
      { type: "highestValue", color: "#63BE7B" },
    ],
  });
}

// Methodology first so source-sheet formulas can reference its lookup tables.
applyBase(methodologySheet, methodologySheet.getRange("A1:F1"), "Consensus methodology", "How mixed letter and numeric grades are standardized and ranked", { A: 150, B: 190, C: 18, D: 120, E: 150, F: 360 });
methodologySheet.getRange("A4:F4").values = [["Rule", "Definition", "", "Output", "Formula logic", "Interpretation"]];
methodologySheet.getRange("A4:F4").format = { fill: blue, font: { bold: true, color: white }, verticalAlignment: "center" };
methodologySheet.getRange("A5:F10").values = [
  ["Average rank", "Arithmetic mean of every site's published team rank", "", "Lower is better", "AVERAGE(site ranks)", "Primary consensus ordering"],
  ["Consensus rank", "Rank of average site rank within that draft", "", "1–12", "RANK(avg rank, league, ascending)", "Tie-break: average grade score"],
  ["Normalized grade", "Numeric grades stay numeric; letters use the scale below", "", "0–100 scale", "Numeric or lookup", "Used only to create one consensus letter grade"],
  ["Consensus grade", "Letter band from the average normalized grade score", "", "A+ to F", "Approximate threshold lookup", "Does not replace any site's original grade"],
  ["Rank spread", "Worst site rank minus best site rank", "", "0–11", "MAX(rank)-MIN(rank)", "7+ places is labeled polarizing"],
  ["Overall summary", "Average of available Snake and Auction average ranks", "", "Lower is better", "AVERAGE(format averages)", "One-format owners are clearly labeled"],
];
methodologySheet.getRange("A5:F10").format = { fill: white, font: { color: ink }, wrapText: true, verticalAlignment: "top", borders: { preset: "insideHorizontal", style: "thin", color: "#D9E1E8" } };
methodologySheet.getRange("A12:B12").values = [["Letter grade", "Normalized score"]];
methodologySheet.getRange("A12:B12").format = { fill: navy, font: { bold: true, color: white } };
const letterRows = Object.entries(letterScores);
methodologySheet.getRange(`A13:B${12 + letterRows.length}`).values = letterRows;
methodologySheet.getRange(`B13:B${12 + letterRows.length}`).format.numberFormat = "0";
methodologySheet.getRange("D12:E12").values = [["Minimum score", "Consensus grade"]];
methodologySheet.getRange("D12:E12").format = { fill: navy, font: { bold: true, color: white } };
methodologySheet.getRange(`D13:E${12 + gradeThresholds.length}`).values = gradeThresholds;
methodologySheet.getRange("A28:F28").merge();
methodologySheet.getRange("A28:F28").values = [["Source: C:/Users/mppac/Downloads/DraftGrades.csv · External rankings and grades are reproduced as provided."]];
methodologySheet.getRange("A28:F28").format = { fill: "#FFF6DA", font: { color: "#6A5313", italic: true }, wrapText: true };
methodologySheet.freezePanes.freezeRows(4);

// Source data sheet.
applyBase(sourceSheet, sourceSheet.getRange("A1:F1"), "Source grades", "Original rows from DraftGrades.csv with a formula-driven normalized score", { A: 90, B: 105, C: 115, D: 125, E: 110, F: 125 });
sourceSheet.getRange("A5:F5").values = [["League", "Team", "Site", "Published Grade", "Published Rank", "Normalized Score"]];
const sourceValues = records.map(record => [record.League, record.Team, record.Site, record.displayValue, record.SiteRank, null]);
sourceSheet.getRange(`A6:F${5 + sourceValues.length}`).values = sourceValues;
records.forEach((record, index) => { record.sourceRow = 6 + index; });
for (const record of records) {
  const formula = typeof record.displayValue === "number"
    ? `=D${record.sourceRow}`
    : `=VLOOKUP(D${record.sourceRow},'Methodology'!$A$13:$B$25,2,FALSE)`;
  sourceSheet.getRange(`F${record.sourceRow}`).formulas = [[formula]];
}
const sourceTable = sourceSheet.tables.add(`A5:F${5 + sourceValues.length}`, true, "SourceGradesTable");
sourceTable.style = "TableStyleMedium2";
sourceSheet.getRange(`D6:D${5 + sourceValues.length}`).format.horizontalAlignment = "center";
sourceSheet.getRange(`E6:E${5 + sourceValues.length}`).format = { numberFormat: "0", horizontalAlignment: "center" };
sourceSheet.getRange(`F6:F${5 + sourceValues.length}`).format = { numberFormat: "0.0", horizontalAlignment: "center" };
addRankGradient(sourceSheet.getRange(`E6:E${5 + sourceValues.length}`));
addScoreGradient(sourceSheet.getRange(`F6:F${5 + sourceValues.length}`));
sourceSheet.freezePanes.freezeRows(5);

function gradeFormula(scoreCell) {
  return `=VLOOKUP(${scoreCell},'Methodology'!$D$13:$E$25,2,TRUE)`;
}

function buildLeagueSheet(sheet, league) {
  const { sites, teams } = summaries[league];
  const siteStart = 3;
  const avgRankCol = siteStart + sites.length * 2;
  const spreadCol = avgRankCol + 1;
  const avgScoreCol = spreadCol + 1;
  const consensusGradeCol = avgScoreCol + 1;
  const notesCol = consensusGradeCol + 1;
  const lastCol = notesCol;
  const colLetter = number => {
    let n = number, result = "";
    while (n > 0) { n--; result = String.fromCharCode(65 + (n % 26)) + result; n = Math.floor(n / 26); }
    return result;
  };
  const lastLetter = colLetter(lastCol);
  const widths = { A: 105, B: 135 };
  for (let i = 0; i < sites.length; i++) { widths[colLetter(siteStart + i * 2)] = 80; widths[colLetter(siteStart + i * 2 + 1)] = 62; }
  widths[colLetter(avgRankCol)] = 100; widths[colLetter(spreadCol)] = 86; widths[colLetter(avgScoreCol)] = 108;
  widths[colLetter(consensusGradeCol)] = 112; widths[colLetter(notesCol)] = 270;
  applyBase(sheet, sheet.getRange(`A1:${lastLetter}1`), `${league} draft consensus grades`, `${sites.length} sources · original grades retained · consensus ordered by average published rank`, widths);

  sheet.getRange("A4:A4").merge(); sheet.getRange("B4:B4").merge();
  sheet.getRange("A4:B4").values = [["Consensus", ""]];
  sheet.getRange("A4:B4").format = { fill: navy, font: { bold: true, color: white }, horizontalAlignment: "center" };
  sites.forEach((site, index) => {
    const left = colLetter(siteStart + index * 2), right = colLetter(siteStart + index * 2 + 1);
    sheet.getRange(`${left}4:${right}4`).merge();
    sheet.getRange(`${left}4:${right}4`).values = [[site]];
    sheet.getRange(`${left}4:${right}4`).format = { fill: blue, font: { bold: true, color: white }, horizontalAlignment: "center" };
  });
  const metricsLeft = colLetter(avgRankCol), metricsRight = colLetter(notesCol);
  sheet.getRange(`${metricsLeft}4:${metricsRight}4`).merge();
  sheet.getRange(`${metricsLeft}4:${metricsRight}4`).values = [["Cross-site consensus"]];
  sheet.getRange(`${metricsLeft}4:${metricsRight}4`).format = { fill: "#516B84", font: { bold: true, color: white }, horizontalAlignment: "center" };

  const headersRow = ["Consensus Rank", "Team"];
  sites.forEach(() => headersRow.push("Grade", "Rank"));
  headersRow.push("Average Rank", "Rank Spread", "Avg Grade Score", "Consensus Grade", "Notes");
  sheet.getRange(`A5:${lastLetter}5`).values = [headersRow];
  sheet.getRange(`A5:${lastLetter}5`).format = { wrapText: true, verticalAlignment: "center", horizontalAlignment: "center" };
  sheet.getRange(`A5:${lastLetter}5`).format.rowHeightPx = 38;

  teams.forEach((team, index) => {
    const row = 6 + index;
    const rankCells = [];
    const scoreRefs = [];
    sheet.getRange(`B${row}`).values = [[team.team]];
    sites.forEach((site, siteIndex) => {
      const record = team.siteMap[site];
      const gradeCol = colLetter(siteStart + siteIndex * 2), rankCol = colLetter(siteStart + siteIndex * 2 + 1);
      sheet.getRange(`${gradeCol}${row}`).formulas = [[`='Source Grades'!$D$${record.sourceRow}`]];
      sheet.getRange(`${rankCol}${row}`).formulas = [[`='Source Grades'!$E$${record.sourceRow}`]];
      sheet.getRange(`${gradeCol}${row}`).format.fill = scoreColor(record.normalizedScore);
      rankCells.push(`${rankCol}${row}`);
      scoreRefs.push(`'Source Grades'!$F$${record.sourceRow}`);
    });
    const avgRankCell = `${colLetter(avgRankCol)}${row}`;
    const spreadCell = `${colLetter(spreadCol)}${row}`;
    const avgScoreCell = `${colLetter(avgScoreCol)}${row}`;
    const consensusGradeCell = `${colLetter(consensusGradeCol)}${row}`;
    sheet.getRange(avgRankCell).formulas = [[`=AVERAGE(${rankCells.join(",")})`]];
    sheet.getRange(spreadCell).formulas = [[`=MAX(${rankCells.join(",")})-MIN(${rankCells.join(",")})`]];
    sheet.getRange(avgScoreCell).formulas = [[`=AVERAGE(${scoreRefs.join(",")})`]];
    sheet.getRange(consensusGradeCell).formulas = [[gradeFormula(avgScoreCell)]];
    sheet.getRange(`A${row}`).formulas = [[
      `=RANK(${avgRankCell},$${colLetter(avgRankCol)}$6:$${colLetter(avgRankCol)}$17,1)+COUNTIFS($${colLetter(avgRankCol)}$6:$${colLetter(avgRankCol)}$17,${avgRankCell},$${colLetter(avgScoreCol)}$6:$${colLetter(avgScoreCol)}$17,">"&${avgScoreCell})`
    ]];
    sheet.getRange(`${colLetter(notesCol)}${row}`).formulas = [[
      `=IF(${spreadCell}>=7,"Polarizing — sites span "&TEXT(${spreadCell},"0")&" places",IF(${avgRankCell}<=3.5,"Strong consensus — top tier",IF(${avgRankCell}>=9.5,"Consensus lower tier",IF(${spreadCell}<=3,"Sites largely agree","Mixed evaluations across sites"))))`
    ]];
    sheet.getRange(consensusGradeCell).format.fill = scoreColor(team.averageScore);
  });

  const lastRow = 5 + teams.length;
  const table = sheet.tables.add(`A5:${lastLetter}${lastRow}`, true, `${league}ConsensusTable`);
  table.style = "TableStyleMedium2";
  sheet.getRange(`A6:A${lastRow}`).format = { numberFormat: "0", horizontalAlignment: "center", font: { bold: true } };
  for (let i = 0; i < sites.length; i++) {
    sheet.getRange(`${colLetter(siteStart + i * 2)}6:${colLetter(siteStart + i * 2)}${lastRow}`).format.horizontalAlignment = "center";
    const rankRange = sheet.getRange(`${colLetter(siteStart + i * 2 + 1)}6:${colLetter(siteStart + i * 2 + 1)}${lastRow}`);
    rankRange.format = { numberFormat: "0", horizontalAlignment: "center" };
    addRankGradient(rankRange);
  }
  const consensusRankRange = sheet.getRange(`A6:A${lastRow}`); addRankGradient(consensusRankRange);
  const avgRankRange = sheet.getRange(`${colLetter(avgRankCol)}6:${colLetter(avgRankCol)}${lastRow}`);
  avgRankRange.format = { numberFormat: "0.00", horizontalAlignment: "center", font: { bold: true } }; addRankGradient(avgRankRange);
  sheet.getRange(`${colLetter(spreadCol)}6:${colLetter(spreadCol)}${lastRow}`).format = { numberFormat: "0", horizontalAlignment: "center" };
  const scoreRange = sheet.getRange(`${colLetter(avgScoreCol)}6:${colLetter(avgScoreCol)}${lastRow}`);
  scoreRange.format = { numberFormat: "0.0", horizontalAlignment: "center" }; addScoreGradient(scoreRange);
  sheet.getRange(`${colLetter(consensusGradeCol)}6:${colLetter(consensusGradeCol)}${lastRow}`).format = { horizontalAlignment: "center", font: { bold: true } };
  sheet.getRange(`${colLetter(notesCol)}6:${colLetter(notesCol)}${lastRow}`).format = { wrapText: true, font: { color: ink } };
  sheet.getRange(`A4:${lastLetter}${lastRow}`).format.borders = { preset: "outside", style: "medium", color: "#93A4B5" };
  sheet.getRange(`A6:${lastLetter}${lastRow}`).format.rowHeightPx = 27;
  sheet.freezePanes.freezeRows(5); sheet.freezePanes.freezeColumns(2);
  return { avgRankCol, consensusGradeCol, teams };
}

const snakeLayout = buildLeagueSheet(snakeSheet, "Snake");
const auctionLayout = buildLeagueSheet(auctionSheet, "Auction");

// Overall summary across formats.
applyBase(overallSheet, overallSheet.getRange("A1:K1"), "2026 overall draft-grade consensus", "Cross-format owner view · average ranks use only drafts entered", { A: 95, B: 115, C: 80, D: 90, E: 105, F: 80, G: 90, H: 105, I: 115, J: 78, K: 250 });
overallSheet.getRange("A4:B4").merge(); overallSheet.getRange("A4:B4").values = [["Owner"]];
overallSheet.getRange("C4:E4").merge(); overallSheet.getRange("C4:E4").values = [["Snake"]];
overallSheet.getRange("F4:H4").merge(); overallSheet.getRange("F4:H4").values = [["Auction"]];
overallSheet.getRange("I4:K4").merge(); overallSheet.getRange("I4:K4").values = [["Combined"]];
overallSheet.getRange("A4:K4").format = { fill: navy, font: { bold: true, color: white }, horizontalAlignment: "center" };
overallSheet.getRange("A5:K5").values = [["Overall Rank", "Owner", "Grade", "Avg Rank", "Consensus Rank", "Grade", "Avg Rank", "Consensus Rank", "Combined Avg Rank", "Formats", "Note"]];
overallSheet.getRange("A5:K5").format = { wrapText: true, verticalAlignment: "center", horizontalAlignment: "center" };
overallSheet.getRange("A5:K5").format.rowHeightPx = 38;

const snakeRowByTeam = new Map(summaries.Snake.teams.map((team, index) => [team.team, 6 + index]));
const auctionRowByTeam = new Map(summaries.Auction.teams.map((team, index) => [team.team, 6 + index]));
for (let index = 0; index < ownerRows.length; index++) {
  const owner = ownerRows[index], row = 6 + index;
  overallSheet.getRange(`B${row}`).values = [[owner.owner]];
  if (owner.snake) {
    const sourceRow = snakeRowByTeam.get(owner.owner);
    overallSheet.getRange(`C${row}:E${row}`).formulas = [[`='Snake Consensus'!$N$${sourceRow}`, `='Snake Consensus'!$K$${sourceRow}`, `='Snake Consensus'!$A$${sourceRow}`]];
    overallSheet.getRange(`C${row}`).format.fill = scoreColor(owner.snake.averageScore);
  }
  if (owner.auction) {
    const sourceRow = auctionRowByTeam.get(owner.owner);
    overallSheet.getRange(`F${row}:H${row}`).formulas = [[`='Auction Consensus'!$L$${sourceRow}`, `='Auction Consensus'!$I$${sourceRow}`, `='Auction Consensus'!$A$${sourceRow}`]];
    overallSheet.getRange(`F${row}`).format.fill = scoreColor(owner.auction.averageScore);
  }
  overallSheet.getRange(`I${row}`).formulas = [[`=AVERAGE(D${row},G${row})`]];
  overallSheet.getRange(`J${row}`).values = [[owner.formats]];
  overallSheet.getRange(`K${row}`).formulas = [[
    owner.formats === "Both"
      ? `=IF(ABS(D${row}-G${row})>=4,"Very different results by format","Consistent across both drafts")`
      : `=J${row}&" only"`
  ]];
  overallSheet.getRange(`A${row}`).formulas = [[`=RANK(I${row},$I$6:$I$${5 + ownerRows.length},1)`]];
}
const overallLastRow = 5 + ownerRows.length;
const overallTable = overallSheet.tables.add(`A5:K${overallLastRow}`, true, "OverallConsensusTable"); overallTable.style = "TableStyleMedium2";
overallSheet.getRange(`A6:A${overallLastRow}`).format = { numberFormat: "0", horizontalAlignment: "center", font: { bold: true } };
overallSheet.getRange(`C6:J${overallLastRow}`).format.horizontalAlignment = "center";
overallSheet.getRange(`D6:D${overallLastRow}`).format.numberFormat = "0.00";
overallSheet.getRange(`G6:G${overallLastRow}`).format.numberFormat = "0.00";
overallSheet.getRange(`I6:I${overallLastRow}`).format = { numberFormat: "0.00", horizontalAlignment: "center", font: { bold: true } };
addRankGradient(overallSheet.getRange(`A6:A${overallLastRow}`)); addRankGradient(overallSheet.getRange(`D6:D${overallLastRow}`));
addRankGradient(overallSheet.getRange(`G6:G${overallLastRow}`)); addRankGradient(overallSheet.getRange(`I6:I${overallLastRow}`));
overallSheet.getRange(`K6:K${overallLastRow}`).format = { wrapText: true, font: { color: ink } };
overallSheet.getRange(`A6:K${overallLastRow}`).format.rowHeightPx = 27;
overallSheet.freezePanes.freezeRows(5); overallSheet.freezePanes.freezeColumns(2);

const checks = [];
checks.push((await workbook.inspect({ kind: "table", range: "Snake Consensus!A1:O17", include: "values,formulas", tableMaxRows: 20, tableMaxCols: 16 })).ndjson);
checks.push((await workbook.inspect({ kind: "table", range: "Auction Consensus!A1:M17", include: "values,formulas", tableMaxRows: 20, tableMaxCols: 14 })).ndjson);
const errors = await workbook.inspect({ kind: "match", searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A", options: { useRegex: true, maxResults: 300 }, summary: "final formula error scan" });

const renderSpecs = [
  ["Snake Consensus", "snake_consensus.png", "A1:O17"],
  ["Auction Consensus", "auction_consensus.png", "A1:M17"],
  ["Overall Summary", "overall_summary.png", `A1:K${overallLastRow}`],
  ["Source Grades", "source_grades.png", "A1:F24"],
  ["Methodology", "methodology.png", "A1:F28"],
];
for (const [sheetName, fileName, range] of renderSpecs) {
  const preview = await workbook.render({ sheetName, range, scale: 1.4, format: "png" });
  await fs.writeFile(path.join(outputDir, fileName), new Uint8Array(await preview.arrayBuffer()));
}

const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(outputPath);
await fs.writeFile(path.join(outputDir, "verification.txt"), checks.join("\n---\n") + "\nERRORS\n" + errors.ndjson, "utf8");
console.log(JSON.stringify({ outputPath, sheets: renderSpecs.map(row => row[0]), records: records.length, errorScan: errors.ndjson }, null, 2));
