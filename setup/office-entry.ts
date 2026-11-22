/** Single writer only. Append-only journal commits precede view publication so a
 * retry reuses frozen rows and intake timestamps after a partial workbook failure.
 * Hidden sheets are storage, not a security boundary. Use approved workbook access.
 */
const journalName='_Readiness Journal';
interface JournalItem { kind: string; id: string; json: string; }
interface JournalLoad { state: State; rowCount: number; ignoredTransactions: number; }
interface CloseStatus { date: string; status: string; detail: string; }

function journalLoad(workbook: ExcelScript.Workbook,p: Profile): JournalLoad {
  const sheet=workbook.getWorksheet(journalName);const state=emptyState(p);
  if(!sheet||!sheet.getUsedRange(true)){
    // Importing a Python-produced workbook would change frozen-row serialization.
    // Require a fresh workbook; never silently rebuild its historical journal.
    const master=workbook.getWorksheet('Master Table');
    check(!master||!master.getUsedRange(true)||master.getUsedRange(true).getRowCount()<=3,'Existing history has no no-Python journal. Use a new workbook; preserve the original archive.');
    return {state,rowCount:0,ignoredTransactions:0};
  }
  const rows=sheet.getUsedRange(true).getValues();
  check(rows.length<=20000 && rows[0][0]==='READINESS JOURNAL / v1' && rows[0][1]===p.siteKey && rows[0][2]===p.datasetMode && rows[0][3]===schemaOf(p),'Journal ownership/schema mismatch or journal exceeds supported size.');
  const groups:{[id:string]:Value[][]}={};const committed=new Set<string>();let ignored=0;
  rows.slice(2).forEach(row=>{
    if(!row[0])return;const tx=String(row[0]);check(!committed.has(tx),'Unexpected rows after a committed transaction.');
    if(row[1]==='commit'){
      const group=groups[tx]||[];check(group.length>0 && group.length===Number(row[4]) && fingerprint(JSON.stringify(group))===row[5],'Committed journal transaction is damaged. Restore an approved workbook version.');
      const items:{[key:string]:Value[][]}={};group.forEach(r=>{const key=String(r[1])+':'+String(r[2]);(items[key]||=[]).push(r);});
      Object.values(items).forEach(parts=>{
        parts.sort((a,b)=>Number(a[3])-Number(b[3]));const count=Number(parts[0][4]);
        check(parts.length===count && parts.every((r,i)=>r[3]===i+1&&r[4]===count&&r[5]===parts[0][5]),'Journal chunks missing or duplicated.');
        const json=parts.map(r=>String(r[6])).join('');check(fingerprint(json)===parts[0][5],'Journal checksum mismatch.');
        if(parts[0][1]==='record'){
          const r=JSON.parse(json) as MeetingRecord;check(!state.records.some(old=>old.id===r.id),'Duplicate committed record.');state.records.push(r);
        }else if(parts[0][1]==='close'){
          const c=JSON.parse(json) as Close;check(!state.closes.some(old=>old.date===c.date),'Duplicate committed day.');state.closes.push(c);
        }else throw new Error('Unknown journal entry.');
      });
      committed.add(tx);delete groups[tx];
    }else (groups[tx]||=[]).push(row.slice(0,7));
  });
  ignored=Object.keys(groups).length;
  check(JSON.stringify(state).length<=2000000,'Journal exceeds 2 million characters. Archive by reviewed migration; do not truncate history.');
  return {state,rowCount:rows.length,ignoredTransactions:ignored};
}
function journalRows(items:JournalItem[],tx:string):Value[][]{
  const rows:Value[][]=[];
  items.forEach(item=>{
    const chunks:string[]=[];let part='';for(const char of Array.from(item.json)){part+=char;if(part.length>=12000){chunks.push(part);part='';}}if(part)chunks.push(part);
    const hash=fingerprint(item.json);chunks.forEach((chunk,i)=>rows.push([tx,item.kind,item.id,i+1,chunks.length,hash,chunk]));
  });return rows;
}
function journalAppend(workbook:ExcelScript.Workbook,p:Profile,load:JournalLoad,rows:Value[][]):void{
  if(!rows.length)return;
  const sheet=workbook.getWorksheet(journalName)||workbook.addWorksheet(journalName);
  if(load.rowCount===0){sheet.getRange('A1:G2').setNumberFormat('@');sheet.getRange('A1:G2').setValues([['READINESS JOURNAL / v1',p.siteKey,p.datasetMode,schemaOf(p),'Do not edit journal','',''],['Transaction','Kind','ID','Part','Parts','SHA256','JSON chunk']]);}
  const start=Math.max(2,load.rowCount);
  sheet.getRangeByIndexes(start,0,rows.length,7).setNumberFormat('@');sheet.getRangeByIndexes(start,0,rows.length,7).setValues(rows);
  // The separate final write is the commit marker. Interrupted pre-commit rows are retained and ignored.
  sheet.getRangeByIndexes(start+rows.length,0,1,7).setValues([[rows[0][0],'commit','',0,rows.length,fingerprint(JSON.stringify(rows)),'']]);
  sheet.setVisibility(ExcelScript.SheetVisibility.hidden);
}

function main(workbook:ExcelScript.Workbook,profileJson:string,reviewedRecordsJson:string='[]',reportDate:string='',closeDatesJson:string='[]',blockScheduleJson:string='',readOnly:boolean=false):string{
  check(profileJson.length<=250000 && reviewedRecordsJson.length<=500000 && blockScheduleJson.length<=500000,'Input too large. Split reviewed intake into smaller batches.');
  const p=validateProfile(JSON.parse(profileJson) as Profile);const now=new Date().toISOString();const today=localStamp(instantOf(now),p.timezone).slice(0,10);const day=isoDay(reportDate||today);
  const incoming=JSON.parse(reviewedRecordsJson) as MeetingRecord[];const closeDates=JSON.parse(closeDatesJson) as string[];
  check(Array.isArray(incoming)&&incoming.length<=50&&Array.isArray(closeDates)&&closeDates.length<=31,'Use arrays, at most 50 records and 31 closing dates per run.');
  check(day<=today,'Do not publish a future operational snapshot. Request upcoming metrics in the briefing instead.');
  const load=journalLoad(workbook,p);const s=load.state;const oldRecords=s.records.length;const oldCloses=s.closes.length;
  incoming.forEach(r=>{ingestRecord(s,p,r,now);});
  const statuses:CloseStatus[]=[];
  Array.from(new Set(closeDates)).sort().forEach(date=>{
    isoDay(date);check(date<=today,'Cannot close a future date.');
    try{const c=closeDay(s,p,date,now);statuses.push({date,status:'closed',detail:c.closedAt});}
    catch(error){statuses.push({date,status:'waiting',detail:String(error)});}
  });
  const payload=makePayload(s,p,day,now);const text=JSON.stringify(payload);
  const lookback=blockScheduleJson?blockLookback(s,p,day,JSON.parse(blockScheduleJson) as BlockSchedule,now):[];
  // Full publisher preflight without mutation. Includes immutable row and ownership checks.
  publishReadiness(workbook,text,true);
  const items:JournalItem[]=[...s.records.slice(oldRecords).map(r=>({kind:'record',id:r.id,json:JSON.stringify(r)})),...s.closes.slice(oldCloses).map(c=>({kind:'close',id:c.id,json:JSON.stringify(c)}))];
  const tx=fingerprint(now+'|'+load.rowCount+'|'+JSON.stringify(items));const rows=journalRows(items,tx);
  check(load.rowCount+rows.length+3<=20000&&JSON.stringify(s).length<=2000000,'Journal capacity reached. Arrange an archive/migration; no history was discarded.');
  if(readOnly)return JSON.stringify({status:'validated_only',date:day,newRecords:s.records.length-oldRecords,closing:statuses,snapshot:payload.snapshot,lookback,ignoredIncompleteTransactions:load.ignoredTransactions});
  journalAppend(workbook,p,load,rows);
  const publication=publishReadiness(workbook,text,false);
  return JSON.stringify({status:'updated',date:day,asOfUtc:now,newRecords:s.records.length-oldRecords,closing:statuses,publication:JSON.parse(publication) as object,lookback,ignoredIncompleteTransactions:load.ignoredTransactions});
}
