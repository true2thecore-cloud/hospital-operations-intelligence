/** Version-2 readiness publisher. Configure one writer per workbook. No external calls. */
type Cell = string | number | boolean;
interface View { name: string; mode: string; headers: string[]; rows: Cell[][]; keys: string[]; }
interface ReadinessPayload { version: number; siteKey: string; siteLabel: string; datasetMode: string; date: string; asOfUtc: string; sheets: View[]; }
interface Plan { view: View; rows: Cell[][]; start: number; existing: ExcelScript.Worksheet | undefined; }

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
  // Complete structural and collision checks before writing any sheet.
  for (const v of p.sheets) {
    if (!v.name || v.name.length > 31 || /[\\/?*\[\]:]/.test(v.name) || names.includes(v.name.toLowerCase())) throw new Error('Invalid/duplicate worksheet name.');
    names.push(v.name.toLowerCase());
    if (!['refresh','append'].includes(v.mode) || !Array.isArray(v.rows) || !v.headers.length || v.headers.length > 110 || v.rows.length > 20000) throw new Error('Invalid view dimensions.');
    if (new Set(v.headers).size !== v.headers.length || v.rows.some(r => r.length !== v.headers.length)) throw new Error('Field mapping mismatch.');
    const rows = v.rows.map(r => r.map(safe));
    const existing = workbook.getWorksheet(v.name);
    let start = 3;
    let appendRows = rows;
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
      }
    }
    plans.push({view:v,rows:appendRows,start,existing});
  }
  for (const plan of plans) {
    const v = plan.view;
    const sheet = plan.existing || workbook.addWorksheet(v.name);
    if (v.mode === 'refresh') {
      const used = sheet.getUsedRange();
      if (used) { used.unmerge(); used.clear(ExcelScript.ClearApplyTo.all); }
    }
    sheet.getRange('A1:D2').setNumberFormat('@');
    sheet.getRange('A1:D2').setValues([[marker,p.siteKey,'',p.siteLabel],[p.date,p.asOfUtc,p.datasetMode,'Updated from reviewed sources']]);
    sheet.getRangeByIndexes(2,0,1,v.headers.length).setValues([v.headers]);
    if (plan.rows.length) {
      const output = sheet.getRangeByIndexes(plan.start,0,plan.rows.length,v.headers.length);
      output.setNumberFormat('@'); output.setValues(plan.rows);
      output.getFormat().setWrapText(true);
      output.getFormat().setVerticalAlignment(ExcelScript.VerticalAlignment.top);
      output.getFormat().setRowHeight(48);
      output.getFormat().getFont().setName('Aptos'); output.getFormat().getFont().setSize(11);
      plan.rows.forEach((r,i)=>{
        r.forEach((value,j)=>{if(typeof value === 'number') sheet.getRangeByIndexes(plan.start+i,j,1,1).setNumberFormat('0.############');});
        const line = sheet.getRangeByIndexes(plan.start+i,0,1,v.headers.length);
        line.getFormat().getFill().setColor(r.includes('HIGH')?'#FCE4E4':r.includes('MEDIUM')?'#FFF1CC':i%2?'#F0F5F9':'#FFFFFF');
      });
    }
    const top = sheet.getRangeByIndexes(0,0,3,Math.max(4,v.headers.length));
    top.getFormat().getFill().setColor('#214F78'); top.getFormat().getFont().setColor('#FFFFFF');
    top.getFormat().getFont().setBold(true); top.getFormat().setRowHeight(28);
    sheet.getUsedRange().getFormat().setColumnWidth(150);
    if (v.name === 'Executive Snapshot') {
      sheet.getRange('A:A').getFormat().setColumnWidth(235);
      sheet.getRange('B:B').getFormat().setColumnWidth(340);
      sheet.getRange('E:F').getFormat().setColumnWidth(260);
    }
    sheet.setShowGridlines(false); sheet.getFreezePanes().freezeRows(3);
  }
  return JSON.stringify({status:'updated',date:p.date,asOfUtc:p.asOfUtc,sheets:plans.map(x=>x.view.name),appendedRows:plans.filter(x=>x.view.mode==='append').reduce((n,x)=>n+x.rows.length,0)});
}
