/** Import a core report into a dedicated Operations View. No staffing or handoff source cells are changed. */
interface Evidence { cueId: string; start: string; text: string; }
interface Issue { issueId: string; state: string; summary: string; owner: string; action: string; due: string; date: string; meetingId: string; evidence: Evidence[]; }
interface Warning { label: string; status: string; interpretation: string; action: string; history: { events: number; matchedDays: number; baselineEvents: number; baselineDays: number; }; }
interface Meeting { kind: string; startsAt: string; reviewed: boolean; }
interface Report { version: number; datasetMode: string; siteLabel: string; date: string; asOfUtc: string; generatedUtc: string; meetings: Meeting[]; issues: Issue[]; warnings: Warning[]; missingMeetings: string[]; }

function main(workbook: ExcelScript.Workbook, reportJson: string, sheetName: string = "Operations View"): string {
  if (reportJson.length > 2000000) throw new Error("Report exceeds 2 million characters.");
  const p = JSON.parse(reportJson) as Report;
  if (p.version !== 1 || !["synthetic", "operational"].includes(p.datasetMode) || !/^\d{4}-\d{2}-\d{2}$/.test(p.date)) throw new Error("Invalid report version, mode or date.");
  if (!Number.isFinite(Date.parse(p.asOfUtc)) || !Number.isFinite(Date.parse(p.generatedUtc))) throw new Error("Invalid report timestamp.");
  if (!Array.isArray(p.issues) || !Array.isArray(p.meetings) || !Array.isArray(p.warnings) || !Array.isArray(p.missingMeetings)) throw new Error("Report arrays are missing.");
  const marker = "HOSPITAL OPERATIONS INTELLIGENCE / v1";
  if (!sheetName.trim() || ["Charge Nurse Dashboard", "Staffing View", "Hand Off Report", "Setup"].includes(sheetName)) throw new Error("Use a dedicated operations worksheet.");
  let sheet = workbook.getWorksheet(sheetName);
  if (sheet && sheet.getUsedRange(true) && sheet.getRange("A1").getText() !== marker) throw new Error("Existing sheet is not an operations view. Choose a new sheet name.");
  if (sheet) {
    const previous = sheet.getRange("B3").getText();
    if (previous && Date.parse(previous) > Date.parse(p.asOfUtc)) throw new Error("Older report rejected; current evidence is newer.");
  } else sheet = workbook.addWorksheet(sheetName);
  // Validate and prepare all text before clearing the dedicated report area.
  const safe = (v: string): string => {
    const s = String(v ?? "").slice(0, 32000);
    return /^[\s]*[=+\-@]/.test(s) ? "'" + s : s;
  };
  const textRows: string[][] = [];
  textRows.push([marker, "", "", "", "", ""]);
  textRows.push([p.siteLabel + " | " + p.date, p.datasetMode === "synthetic" ? "SYNTHETIC EXAMPLE" : "Operational review", "", "", "", ""]);
  textRows.push(["Evidence through (UTC)", p.asOfUtc, "Generated (UTC)", p.generatedUtc, "", ""]);
  textRows.push(["MEETING SEQUENCE", "Start", "Review status", "", "", ""]);
  p.meetings.forEach(m => textRows.push([m.kind, m.startsAt, m.reviewed ? "Reviewed" : "Awaiting review", "", "", ""]));
  textRows.push(["Not yet imported", p.missingMeetings.join(", "), "", "", "", ""]);
  textRows.push(["PATTERNS TO REVIEW", "Historical events / comparable days", "Interpretation", "Action", "", ""]);
  p.warnings.forEach(w => textRows.push([w.label, `${w.history.events} / ${w.history.matchedDays}`, w.interpretation, w.action, w.status, ""]));
  if (!p.warnings.length) textRows.push(["No configured pattern supported", "Missing evidence is not an all-clear.", "", "", "", ""]);
  textRows.push(["ISSUES AND FOLLOW-THROUGH", "Status", "Owner", "Action", "Due", "Evidence"]);
  p.issues.forEach(i => textRows.push([i.summary, i.state, i.owner, i.action, i.due, `${i.date} | ${i.meetingId} | ${i.evidence.map(e => e.start + ": " + e.text).join(" / ")}`]));
  textRows.push(["Operational decision support", "Historical associations are exploratory. Leaders verify decisions.", "", "", "", ""]);
  if (textRows.length > 500) throw new Error("Report exceeds 500 rows. Archive resolved issues or use the HTML report.");
  const rows = textRows.map(row => row.map(safe));
  const canvas = sheet.getRange("A1:F500");
  canvas.unmerge();
  canvas.clear(ExcelScript.ClearApplyTo.all);
  canvas.setNumberFormat("@");
  const output = sheet.getRangeByIndexes(0, 0, rows.length, 6);
  output.setValues(rows);
  output.getFormat().getFont().setName("Aptos");
  output.getFormat().getFont().setSize(11);
  output.getFormat().setWrapText(true);
  output.getFormat().setVerticalAlignment(ExcelScript.VerticalAlignment.top);
  sheet.getRange("A:A").getFormat().setColumnWidth(240);
  sheet.getRange("B:C").getFormat().setColumnWidth(155);
  sheet.getRange("D:D").getFormat().setColumnWidth(260);
  sheet.getRange("E:E").getFormat().setColumnWidth(140);
  sheet.getRange("F:F").getFormat().setColumnWidth(350);
  for (let r = 0; r < rows.length; r++) {
    const range = sheet.getRangeByIndexes(r, 0, 1, 6);
    if (r === 0 || ["MEETING SEQUENCE", "PATTERNS TO REVIEW", "ISSUES AND FOLLOW-THROUGH"].includes(textRows[r][0])) {
      range.getFormat().getFill().setColor("#17344C");
      range.getFormat().getFont().setColor("#FFFFFF");
      range.getFormat().getFont().setBold(true);
    } else {
      range.getFormat().getFill().setColor(textRows[r][1] === "active" ? "#FFF1CC" : r % 2 ? "#F1F6F9" : "#FFFFFF");
      range.getFormat().getFont().setColor("#20354A");
    }
  }
  output.getFormat().autofitRows();
  sheet.setShowGridlines(false);
  sheet.getFreezePanes().freezeRows(3);
  return JSON.stringify({ status: "updated", sheet: sheetName, reportDate: p.date, rows: rows.length });
}
