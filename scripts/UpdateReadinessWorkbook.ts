/** Version-2 readiness publisher. Configure one writer per workbook. No external calls. */
type Cell = string | number | boolean;
interface View { name: string; mode: string; headers: string[]; rows: Cell[][]; keys: string[]; }
interface ReadinessPayload { version: number; siteKey: string; siteLabel: string; datasetMode: string; date: string; asOfUtc: string; sheets: View[]; }
interface Plan { view: View; rows: Cell[][]; allRows: Cell[][]; start: number; existing: ExcelScript.Worksheet | undefined; }

const detailSheet = 'Audit Details';
const detailFormat = '0;-0;0;"Full text: Audit Details"';
function needsDetail(value: Cell): boolean {
  return typeof value === 'string' && (value.length > 320 || value.split('\n').length > 6);
}
// Preserve every character, including newlines, in bounded readable continuation rows.
function detailParts(text: string): string[] {
  const parts: string[] = []; let part = ''; let lines = 1;
  for (const char of Array.from(text)) {
    part += char; if (char === '\n') lines++;
    if (part.length >= 300 || lines >= 6) { parts.push(part); part = ''; lines = 1; }
  }
  if (part) parts.push(part);
  return parts;
}
function columnName(index: number): string {
  let name = ''; for (let n = index + 1; n > 0; n = Math.floor((n - 1) / 26)) name = String.fromCharCode(65 + (n - 1) % 26) + name;
  return name;
}
function layout(sheet: ExcelScript.Worksheet, v: View, rows: Cell[][]): void {
  const width = Math.max(4, v.headers.length);
  const area = sheet.getRangeByIndexes(0,0,Math.max(3,rows.length+3),width);
  const format = area.getFormat();
  format.setWrapText(true); format.setVerticalAlignment(ExcelScript.VerticalAlignment.top);
  format.getFont().setName('Aptos'); format.getFont().setSize(11);
  format.getFont().setColor('#203346'); format.getFont().setBold(false);
  format.setColumnWidth(140);
  v.headers.forEach((header,c)=>{
    let points = c === 0 ? 190 : 140;
    if (/Concern|concern|Reference|Evidence|Action|Value|provenance|coverage/i.test(header)) points = 280;
    if (v.name === 'Executive Snapshot') points = [190,280,105,125,210,280][c] || 140;
    if (v.name === detailSheet) points = [180,105,180,60,450][c] || 140;
    sheet.getRangeByIndexes(0,c,Math.max(3,rows.length+3),1).getFormat().setColumnWidth(points);
  });
  rows.forEach((row,i)=>{
    const line = sheet.getRangeByIndexes(i+3,0,1,width);
    line.getFormat().getFill().setColor(row.includes('HIGH')?'#FCE4E4':row.includes('MEDIUM')?'#FFF1CC':i%2?'#EFF4F8':'#FFFFFF');
    row.forEach((value,c)=>{
      const cell = sheet.getRangeByIndexes(i+3,c,1,1);
      cell.setNumberFormat(typeof value === 'number' ? (Number.isInteger(value) ? '#,##0' : 'General') : '@');
      if (v.name !== detailSheet && needsDetail(value)) cell.setNumberFormat(detailFormat);
    });
    // Fit displayed text after widths and numeric formats are final. No fixed 48-point clipping.
    line.getFormat().autofitRows();
    line.getFormat().setRowHeight(Math.max(32,line.getFormat().getRowHeight()+6));
    if (v.name === 'Executive Snapshot') {
      if (row.every(x=>x==='')) line.getFormat().setRowHeight(14);
      if (row[0] === 'SEVEN-DAY HIGH / MEDIUM EVENTS') {
        line.getFormat().getFill().setColor('#397BB0'); line.getFormat().getFont().setColor('#FFFFFF');
        line.getFormat().getFont().setBold(true); line.getFormat().setRowHeight(40);
      }
      if (row[0] === 'Event date' && row[1] === 'Concern') {
        line.getFormat().getFill().setColor('#D9E5F0'); line.getFormat().getFont().setBold(true);
      }
    }
  });
  const top = sheet.getRangeByIndexes(0,0,3,width);
  top.getFormat().getFill().setColor('#214F78'); top.getFormat().getFont().setColor('#FFFFFF');
  top.getFormat().getFont().setBold(true); top.getFormat().setRowHeight(36);
  sheet.getRange('B2').getFormat().getFont().setSize(9);
  top.getFormat().autofitRows();
  for (let r=0;r<3;r++) {
    const line = sheet.getRangeByIndexes(r,0,1,width);
    line.getFormat().setRowHeight(Math.max(32,line.getFormat().getRowHeight()+6));
  }
  sheet.setShowGridlines(false); sheet.getFreezePanes().freezeRows(3);
}

function main(workbook: ExcelScript.Workbook, payloadJson: string): string {
  if (payloadJson.length > 2000000) throw new Error('Payload exceeds 2 million characters. Archive by approved process; do not truncate history.');
  const p = JSON.parse(payloadJson) as ReadinessPayload;
  const marker = 'READINESS / v2';
  if (p.version !== 2 || !p.siteKey || !['synthetic','operational'].includes(p.datasetMode) || !/^\d{4}-\d{2}-\d{2}$/.test(p.date) || !Number.isFinite(Date.parse(p.asOfUtc)) || !Array.isArray(p.sheets)) throw new Error('Invalid readiness payload.');
  const names: string[] = [];
  const plans: Plan[] = [];
  const safe = (value: Cell): Cell => {
    if (!['string','number','boolean'].includes(typeof value) || (typeof value === 'number' && !Number.isFinite(value))) throw new Error('Invalid cell type.');
    if (typeof value !== 'string') return value;
    if (value.length > 32000) throw new Error('Cell too long; split the source record before publishing.');
    return /^[\s]*[=+\-@]/.test(value) ? "'" + value : value;
  };
  if (p.sheets.some(v=>v.name.toLowerCase()===detailSheet.toLowerCase())) throw new Error('Audit Details is reserved for the generated full-text view.');
  // Complete structural and collision checks, including the derived detail view, before writing.
  const prepare = (v: View): void => {
    if (!v.name || v.name.length > 31 || /[\\/?*\[\]:]/.test(v.name) || names.includes(v.name.toLowerCase())) throw new Error('Invalid/duplicate worksheet name.');
    names.push(v.name.toLowerCase());
    if (!['refresh','append'].includes(v.mode) || !Array.isArray(v.rows) || !v.headers.length || v.headers.length > 110 || v.rows.length > 20000) throw new Error('Invalid view dimensions.');
    if (new Set(v.headers).size !== v.headers.length || v.rows.some(r => r.length !== v.headers.length)) throw new Error('Field mapping mismatch.');
    const rows = v.rows.map(r => r.map(safe));
    const existing = workbook.getWorksheet(v.name);
    let start = 3;
    let appendRows = rows;
    let allRows = rows;
    if (v.mode === 'append' && (v.keys.length !== rows.length || new Set(v.keys).size !== v.keys.length || v.keys.some((k,i) => k !== String(rows[i][0])))) throw new Error('Append keys must be unique first-column identities.');
    if (existing && existing.getUsedRange(true)) {
      if (existing.getRange('A1').getText() !== marker) throw new Error('Refusing unrelated worksheet: ' + v.name);
      const site = existing.getRange('B1').getText();
      if (site && site !== p.siteKey) throw new Error('Workbook belongs to another site.');
      const mode = existing.getRange('C2').getText();
      if (mode && mode !== p.datasetMode) throw new Error('Do not mix synthetic and operational workbooks.');
      const previous = existing.getRange('B2').getText();
      if (previous && Date.parse(previous) > Date.parse(p.asOfUtc)) throw new Error('Older publication rejected.');
      if (v.mode === 'append') {
        const old = existing.getUsedRange(true).getValues();
        const oldHeaders = old[2] || [];
        if (JSON.stringify(oldHeaders.slice(0,v.headers.length)) !== JSON.stringify(v.headers) || oldHeaders.slice(v.headers.length).some(x=>x!=='')) throw new Error('Historical column schema changed; use an explicit migration/new workbook.');
        const known = new Map<string, Cell[]>();
        for (let i=3;i<old.length;i++) {
          if (old[i][0] === '') continue;
          const key = String(old[i][0]);
          if (known.has(key)) throw new Error('Duplicate historical key already in workbook.');
          known.set(key,old[i].slice(0,v.headers.length));
        }
        appendRows = rows.filter((r,i) => {
          const prior = known.get(v.keys[i]);
          if (!prior) return true;
          // Excel can return escaped text without its leading apostrophe.
          const normalized = (a: Cell[]) => a.map(x=>typeof x==='string' && /^'[\s]*[=+\-@]/.test(x)?x.slice(1):x);
          if (JSON.stringify(normalized(prior)) !== JSON.stringify(normalized(r))) throw new Error('Immutable historical row differs: ' + v.keys[i]);
          return false;
        });
        start = Math.max(3,old.length);
        allRows = old.slice(3).map(r=>r.slice(0,v.headers.length)).concat(appendRows);
      }
    }
    plans.push({view:v,rows:appendRows,allRows,start,existing});
  };
  p.sheets.forEach(prepare);
  const detailRows: Cell[][] = [];
  plans.forEach(plan=>plan.allRows.forEach((row,r)=>row.forEach((value,c)=>{
    if (!needsDetail(value)) return;
    const text = String(value).replace(/^'(?=[\s]*[=+\-@])/,'');
    const parts = detailParts(text);
    parts.forEach((part,i)=>detailRows.push([plan.view.name,columnName(c)+(r+4),plan.view.headers[c],`${i+1} / ${parts.length}`,part]));
  })));
  prepare({name:detailSheet,mode:'refresh',headers:['Source sheet','Cell','Field','Part','Full text'],rows:detailRows,keys:[]});
  for (const plan of plans) {
    const v = plan.view;
    const sheet = plan.existing || workbook.addWorksheet(v.name);
    if (v.mode === 'refresh') {
      const used = sheet.getUsedRange();
      if (used) { used.unmerge(); used.clear(ExcelScript.ClearApplyTo.all); }
    }
    sheet.getRange('A1:D2').setNumberFormat('@');
    sheet.getRange('A1:D2').setValues([[marker,p.siteKey,'',p.siteLabel],[p.date,p.asOfUtc,p.datasetMode,'Long text: Audit Details']]);
    sheet.getRangeByIndexes(2,0,1,v.headers.length).setValues([v.headers]);
    if (plan.rows.length) {
      const output = sheet.getRangeByIndexes(plan.start,0,plan.rows.length,v.headers.length);
      output.setNumberFormat('@'); output.setValues(plan.rows);
    }
    // Reapply to all stored rows as well, repairing formatting in previously published workbooks.
    layout(sheet,v,plan.allRows);
  }
  return JSON.stringify({status:'updated',date:p.date,asOfUtc:p.asOfUtc,sheets:plans.map(x=>x.view.name),appendedRows:plans.filter(x=>x.view.mode==='append').reduce((n,x)=>n+x.rows.length,0)});
}
