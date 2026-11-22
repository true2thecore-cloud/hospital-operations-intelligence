/** Portable readiness rules. Bundled into Office Scripts and the offline setup page.
 * No Python, network access, model calls, credentials, or automatic source discovery.
 */
                                       
                                                                                                                                                  
                                                                                                                                                                                          
                                                                                                                                                                                                                                                             
                                                         
                                                                                                                                                           
                                                                                                                                                                               
                                                                                                                                                                                                                                                                                                            
                                                                                                                                                                                                                                                                                         
                                                                                                                                                                                              
                                                                        
                                                                                                                                                   
                                                                                                                                     
                                                                                                       
                                                                                                                                                                                            
                                                                         
                                                                                           
                                                                      
                                                                                                                  

function check(ok         , message        )       { if (!ok) throw new Error(message); }
function isoDay(day        )         {
  check(typeof day === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(day) && Number.isFinite(Date.parse(day)) && new Date(day).toISOString().slice(0,10) === day, 'Invalid calendar date.'); return day;
}
function instantOf(value        )         {
  check(typeof value === 'string' && /T.*(?:Z|[+-]\d{2}:\d{2})$/.test(value) && Number.isFinite(Date.parse(value)), 'Timestamp needs an explicit UTC offset.'); return Date.parse(value);
}
function dayOffset(day        , offset        )         { return new Date(Date.parse(isoDay(day)) + offset * 86400000).toISOString().slice(0,10); }
function localStamp(ms        , zone        )         {
  const parts = new Intl.DateTimeFormat('en-GB', { timeZone: zone, year:'numeric', month:'2-digit', day:'2-digit', hour:'2-digit', minute:'2-digit', second:'2-digit', hour12:false }).formatToParts(new Date(ms));
  const get = (key        )         => parts.find(p => p.type === key)?.value || '';
  return get('year')+'-'+get('month')+'-'+get('day')+'T'+(get('hour')==='24'?'00':get('hour'))+':'+get('minute')+':'+get('second');
}
function wallTime(day        , clock        , zone        )         {
  isoDay(day); check(/^([01]\d|2[0-3]):[0-5]\d$/.test(clock), 'Invalid local clock time.');
  const target = day+'T'+clock+':00'; const guess = Date.parse(target+'Z');
  // Test offsets on both sides of a DST transition. Repeated clocks choose the later instant;
  // a nonexistent clock fails explicitly instead of silently moving a closing gate.
  const candidates           = [];
  for (const hours of [-36,0,36]) {
    const sample = guess + hours*3600000;
    const offset = Date.parse(localStamp(sample,zone)+'Z') - sample;
    const candidate = guess - offset;
    if (localStamp(candidate,zone) === target) candidates.push(candidate);
  }
  check(candidates.length > 0, 'Local clock does not exist on this date. Adjust the DST-day schedule explicitly.'); return Math.max(...candidates);
}
function canonical(text        )         {
  // JSON.stringify replacer sorts keys at every object level, including nested objects.
  const value = JSON.parse(text)          ;
  return JSON.stringify(value, (_key, entry        ) => {
    if (entry && typeof entry === 'object' && !Array.isArray(entry)) {
      return Object.keys(entry).sort().reduce((result                           , key) => { result[key] = (entry                             )[key]; return result; }, Object.create(null)                             );
    }
    return entry;
  });
}
function fingerprint(text        )         {
  // SHA-256 over UTF-8. No crypto service or external dependency in Office Scripts.
  const bytes           = [];
  for (const char of Array.from(text)) {
    const n=char.codePointAt(0) || 0;
    if(n<128) bytes.push(n); else if(n<2048) bytes.push(192|(n>>6),128|(n&63));
    else if(n<65536) bytes.push(224|(n>>12),128|((n>>6)&63),128|(n&63));
    else bytes.push(240|(n>>18),128|((n>>12)&63),128|((n>>6)&63),128|(n&63));
  }
  const size=bytes.length*8; bytes.push(128); while(bytes.length%64!==56) bytes.push(0);
  for(let i=7;i>=0;i--) bytes.push(i>=4?0:(size>>>(i*8))&255);
  const h=[0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19];
  const k=[0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2];
  const rr=(n       ,b       )       =>(n>>>b)|(n<<(32-b));
  for(let o=0;o<bytes.length;o+=64){
    const w         =[]; for(let i=0;i<16;i++) w[i]=(bytes[o+i*4]<<24)|(bytes[o+i*4+1]<<16)|(bytes[o+i*4+2]<<8)|bytes[o+i*4+3];
    for(let i=16;i<64;i++){ const a=w[i-15],b=w[i-2]; w[i]=((rr(a,7)^rr(a,18)^(a>>>3))+w[i-16]+(rr(b,17)^rr(b,19)^(b>>>10))+w[i-7])|0; }
    let [a,b,c,d,e,f,g,j]=h;
    for(let i=0;i<64;i++){const t1=(j+(rr(e,6)^rr(e,11)^rr(e,25))+((e&f)^(~e&g))+k[i]+w[i])|0; const t2=((rr(a,2)^rr(a,13)^rr(a,22))+((a&b)^(a&c)^(b&c)))|0; j=g;g=f;f=e;e=(d+t1)|0;d=c;c=b;b=a;a=(t1+t2)|0;}
    [a,b,c,d,e,f,g,j].forEach((n,i)=>{h[i]=(h[i]+n)|0;});
  }
  return h.map(n=>(n>>>0).toString(16).padStart(8,'0')).join('');
}
function hashJson(text        )         { return fingerprint(canonical(text)); }
function validateProfile(p         )          {
  check(p.version===2 && ['synthetic','operational'].includes(p.datasetMode), 'Use readiness version 2 and a dataset mode.');
  check(/^[a-z][a-z0-9_]{0,47}$/.test(p.siteKey) && !!p.siteLabel, 'Set a stable site key and label.');
  localStamp(Date.now(),p.timezone);
  check(/^([01]\d|2[0-3]):[0-5]\d$/.test(p.closingTime), 'Invalid closing time.');
  check(Number.isInteger(p.transcriptDelayMinutes) && p.transcriptDelayMinutes>=0 && p.transcriptDelayMinutes<=1440, 'Invalid transcript delay.');
  check(Array.isArray(p.fields) && p.fields.length>0 && p.fields.length<=100 && Array.isArray(p.meetings) && p.meetings.length>0, 'Configure 1-100 fields and at least one meeting.');
  for(const keys of [p.fields.map(f=>f.key),p.meetings.map(m=>m.key)]) check(new Set(keys).size===keys.length && keys.every(k=>/^[a-z][a-z0-9_]{0,47}$/.test(k)), 'Invalid or duplicate keys.');
  p.fields.forEach(f=>check(['number','text','boolean'].includes(f.type) && !!f.label && (f.min===undefined || Number.isFinite(f.min)) && (f.max===undefined || Number.isFinite(f.max)) && !(f.min!==undefined && f.max!==undefined && f.min>f.max), 'Invalid field definition.'));
  p.meetings.forEach(m=>check(/^([01]\d|2[0-3]):[0-5]\d$/.test(m.end) && m.weekdays.length>0 && m.weekdays.every(d=>Number.isInteger(d)&&d>=0&&d<=6) && m.fields.every(k=>p.fields.some(f=>f.key===k)), 'Invalid meeting schedule or mapping.'));
  Object.keys(p.scheduleOverrides||{}).forEach(d=>{isoDay(d);check((p.scheduleOverrides||{})[d].every(k=>p.meetings.some(m=>m.key===k)), 'Unknown override meeting.');});
  return p;
}
function schemaOf(p         )         { return hashJson(JSON.stringify(p.fields.map(f=>({key:f.key,type:f.type,unit:f.unit||'',definition:f.definition||''})))); }
function emptyState(p         )        { return {version:1,siteKey:p.siteKey,datasetMode:p.datasetMode,schema:schemaOf(p),records:[],closes:[]}; }
function validateOwner(s       ,p         )       {
  check(s.version===1 && s.siteKey===p.siteKey && s.datasetMode===p.datasetMode, 'Journal belongs to another site or mode.');
  check(s.schema===schemaOf(p), 'Historical field meaning/order changed. Use a new workbook or a reviewed migration.');
}
function evidenceCheck(items            ,sources          )       { check(Array.isArray(items)&&items.length>0&&items.every(e=>!!e.locator?.trim()&&sources.some(s=>s.id===e.sourceId&&s.status==='available')), 'Every fact needs an available source and exact locator.'); }
function validateReviewer(role        , mode        )       {
  const normalized=typeof role==='string'?role.trim().toLowerCase().replace(/[_-]+/g,' ').replace(/\s+/g,' '):'';
  check(!!normalized && !/^replace\b/.test(normalized) && !/^(draft|unreviewed|not reviewed|not stated|pending|unknown|tbd|n\/a)$/.test(normalized), 'A reviewer must confirm this record; replace the unreviewed placeholder after review.');
  // Demonstration labels are permitted only in an isolated synthetic workbook.
  // A role string is an attestation, not authentication. The approved queue controls admission.
  check(mode==='synthetic' || !/^(example|sample|synthetic|test)(?:\s|$)/.test(normalized), 'Example or synthetic reviewer labels cannot approve an operational record.');
}
function ingestRecord(s       ,p         ,input               ,now        )                {
  const r=JSON.parse(JSON.stringify(input))                 ; const nowMs=instantOf(now); validateOwner(s,p);
  check(r.receivedAt===undefined && r.profileHash===undefined, 'Intake timestamps are assigned by the runtime, not the extractor.');
  check(r.version===2 && typeof r.id==='string' && /^[A-Za-z0-9_.-]{1,160}$/.test(r.id), 'Record needs a stable simple revision ID.');
  validateReviewer(r.reviewerRole,p.datasetMode);
  const day=isoDay(r.date); const meeting=p.meetings.find(m=>m.key===r.meetingKey); check(!!meeting, 'Unknown meeting key.');
  check(instantOf(r.endsAt)>=instantOf(r.startsAt) && instantOf(r.endsAt)<=nowMs, 'Meeting must have ended before intake.');
  check(localStamp(instantOf(r.startsAt),p.timezone).slice(0,10)===day, 'Meeting date must match local start date.');
  check(['processed','unavailable','not_held'].includes(r.status), 'Invalid meeting status.');
  r.sources=r.sources||[];r.metrics=r.metrics||[];r.issues=r.issues||[];
  check(r.status==='processed' || (!r.metrics.length&&!r.issues.length&&!!r.statusNote?.trim()), 'Unavailable/not-held records need a reason and no facts.');
  check(new Set(r.sources.map(x=>x.id)).size===r.sources.length && r.sources.every(x=>/^[A-Za-z0-9_.-]{1,160}$/.test(x.id)&&!!x.type&&['available','pending','denied','missing','not_applicable'].includes(x.status)&&(x.status!=='available'||!!x.reference)), 'Invalid or duplicate sources.');
  r.sources.forEach(x=>{if(x.capturedAt)check(instantOf(x.capturedAt)<=nowMs,'Source capture time is in the future.');if(x.confidence)check(['HIGH','MEDIUM','LOW','UNKNOWN'].includes(x.confidence),'Invalid reviewed source confidence.');});
  check(new Set(r.metrics.map(m=>m.field+'|'+m.appliesToDate)).size===r.metrics.length, 'Duplicate metric/date.');
  r.metrics.forEach(m=>{
    const f=p.fields.find(f=>f.key===m.field);check(!!f && !!meeting?.fields.includes(m.field), 'Unmapped metric.');
    check(typeof m.value===f?.type && (f.type!=='number'||(Number.isFinite(m.value)&&Number(m.value)>=(f.min??-Infinity)&&Number(m.value)<=(f.max??Infinity))), 'Metric type or bounds mismatch.');
    isoDay(m.appliesToDate);check(instantOf(m.observedAt)<=nowMs, 'Observation is in the future.');evidenceCheck(m.evidence,r.sources);
  });
  check(new Set(r.issues.map(i=>i.issueId)).size===r.issues.length, 'Duplicate issue.');
  r.issues.forEach(i=>{
    check(/^[A-Za-z0-9_.-]{1,160}$/.test(i.issueId)&&!!i.summary&&['HIGH','MEDIUM','LOW','UNKNOWN'].includes(i.severity)&&['active','cleared','unknown'].includes(i.state), 'Invalid issue.');
    check(isoDay(i.eventDate)<=day, 'Event date cannot be in the future.');
    s.records.forEach(old=>old.issues.filter(x=>x.issueId===i.issueId).forEach(x=>check(x.eventDate===i.eventDate, 'An issue cannot reset its event date.')));
    i.owner=i.owner||'Not stated';i.action=i.action||'Not stated';i.due=i.due||'Not stated';evidenceCheck(i.evidence,r.sources);
  });
  const prior=s.records.find(x=>x.id===r.id);
  if(prior){const compare=JSON.parse(JSON.stringify(prior))                 ;delete compare.receivedAt;delete compare.profileHash;check(canonical(JSON.stringify(compare))===canonical(JSON.stringify(r)), 'Changed record requires a new revision ID.');return prior;}
  r.receivedAt=new Date(nowMs).toISOString();r.profileHash=hashJson(JSON.stringify(p));s.records.push(r);return r;
}
function sortRecords(a               ,b               )         { return instantOf(a.endsAt)-instantOf(b.endsAt)||instantOf(a.receivedAt||'')-instantOf(b.receivedAt||'')||a.id.localeCompare(b.id); }
function visibleRecords(s       ,cutoff        )                  { return s.records.filter(r=>instantOf(r.receivedAt||'')<=instantOf(cutoff)).sort((a,b)=>sortRecords(a,b)); }
function currentRecords(s       ,cutoff        )                  {
  const chosen=Object.create(null)                                ;
  visibleRecords(s,cutoff).sort((a,b)=>instantOf(a.receivedAt||'')-instantOf(b.receivedAt||'')||a.id.localeCompare(b.id)).forEach(r=>{chosen[r.date+'|'+r.meetingKey+'|'+new Date(r.startsAt).toISOString()]=r;});
  return Object.values(chosen).sort((a,b)=>sortRecords(a,b));
}
function makeSnapshot(s       ,p         ,day        ,cutoff        )           {
  isoDay(day);const start=dayOffset(day,-6);const metrics=Object.create(null)                         ;const issues=Object.create(null)                        ;const peak=Object.create(null)                         ;const future         =[];
  const rank                      ={UNKNOWN:0,LOW:1,MEDIUM:2,HIGH:3};
  currentRecords(s,cutoff).filter(r=>r.date<=day).forEach(r=>{
    r.metrics.forEach(m=>{const item={...m,recordId:r.id,meetingKey:r.meetingKey};if(m.appliesToDate>day){future.push(item);return;}
      const old=metrics[m.field];const newer=!old||m.appliesToDate>old.appliesToDate||(m.appliesToDate===old.appliesToDate&&(instantOf(m.observedAt)>instantOf(old.observedAt)||(instantOf(m.observedAt)===instantOf(old.observedAt)&&instantOf(r.receivedAt||'')>=instantOf(old.receivedAt||''))));if(newer)metrics[m.field]={...item,receivedAt:r.receivedAt};
    });
    r.issues.forEach(i=>{if(!peak[i.issueId]||rank[i.severity]>rank[peak[i.issueId]])peak[i.issueId]=i.severity;issues[i.issueId]={...i,recordId:r.id,meetingKey:r.meetingKey,updatedAt:r.endsAt};});
  });
  const all=Object.values(issues);
  return {date:day,asOfUtc:new Date(cutoff).toISOString(),metrics,sevenDayConcerns:all.filter(i=>i.eventDate>=start&&i.eventDate<=day&&rank[peak[i.issueId]]>=2).map(i=>({...i,trackedSeverity:peak[i.issueId]})).sort((a,b)=>b.eventDate.localeCompare(a.eventDate)||b.issueId.localeCompare(a.issueId)),dailyConcerns:all.filter(i=>i.eventDate===day||localStamp(instantOf(i.updatedAt||''),p.timezone).slice(0,10)===day||i.state!=='cleared'),openIssues:all.filter(i=>i.state!=='cleared'),upcomingMetrics:future};
}
function closeDay(s       ,p         ,day        ,now        )        {
  isoDay(day);const existing=s.closes.find(c=>c.date===day);if(existing)return existing;
  const weekday=(new Date(day).getUTCDay()+6)%7;
  const keys=(p.scheduleOverrides||{})[day]??p.meetings.filter(m=>m.weekdays.includes(weekday)).map(m=>m.key);
  const records=currentRecords(s,now).filter(r=>r.date===day);let due=wallTime(day,p.closingTime,p.timezone);
  p.meetings.filter(m=>keys.includes(m.key)).forEach(m=>{due=Math.max(due,wallTime(day,m.end,p.timezone)+p.transcriptDelayMinutes*60000);check(records.some(r=>r.meetingKey===m.key), 'Closing waits for processed/unavailable/not-held record: '+m.key);});
  records.forEach(r=>{due=Math.max(due,instantOf(r.endsAt)+p.transcriptDelayMinutes*60000);check(!r.sources.some(x=>x.status==='pending'), 'Closing waits for pending sources.');});
  check(instantOf(now)>=due, 'Closing time/transcript window has not passed.');
  const result      ={id:day,date:day,closedAt:new Date(now).toISOString(),profileHash:hashJson(JSON.stringify(p)),snapshot:makeSnapshot(s,p,day,now),recordIds:records.map(r=>r.id),coverage:records.map(r=>({meetingKey:r.meetingKey,status:r.status,note:r.statusNote||''}))};s.closes.push(result);return result;
}
function evidenceText(items            )         { return items.map(e=>e.sourceId+' @ '+e.locator).join('; '); }
function makePayload(s       ,p         ,day        ,cutoff        )          {
  const snapshot=makeSnapshot(s,p,day,cutoff);const sheets            =[];
  const add=(name       ,mode       ,headers         ,rows          )     =>{sheets.push({name,mode,headers,rows,keys:mode==='append'?rows.map(r=>String(r[0])):[]});};
  const rows          =p.fields.filter(f=>f.executive!==false).map(f=>{const m=snapshot.metrics[f.key];return [f.label,m?m.value:'Not stated',f.unit||'',m?.appliesToDate||'',m?.observedAt||'',m?evidenceText(m.evidence):'No validated observation'];});
  rows.push(['','','','','',''],['SEVEN-DAY HIGH / MEDIUM EVENTS','','','','',''],['Event date','Concern','Severity','Status','Owner / action','Evidence']);
  snapshot.sevenDayConcerns.forEach(i=>rows.push([i.eventDate,i.summary,i.trackedSeverity||i.severity,i.state,i.owner+' / '+i.action,i.recordId+' | '+evidenceText(i.evidence)]));
  add('Executive Snapshot','refresh',['Metric','Known value','Unit','Applies to','Observed at','Evidence'],rows);
  const closed=s.closes.filter(c=>instantOf(c.closedAt)<=instantOf(cutoff)).sort((a,b)=>a.date.localeCompare(b.date));
  add('Master Table','append',['Date',...p.fields.map(f=>f.key),'Concerns at close','Closed at','Source records','Metric provenance','Source coverage','Record hash'],closed.map(c=>[c.date,...p.fields.map(f=>c.snapshot.metrics[f.key]?.value??'Not stated'),c.snapshot.dailyConcerns.map(i=>i.summary+' ['+i.state+']').join('; '),c.closedAt,c.recordIds.join('; '),JSON.stringify(c.snapshot.metrics),JSON.stringify(c.coverage),hashJson(JSON.stringify(c))]));
  add('Hand-Off Review','refresh',['Issue ID','Event date','Concern','Severity','State','Owner','Action','Due','Evidence'],snapshot.openIssues.map(i=>[i.issueId,i.eventDate,i.summary,i.severity,i.state,i.owner||'',i.action||'',i.due||'',i.recordId||'']));
  const all=visibleRecords(s,cutoff);
  add('Source Audit Log','append',['Audit ID','Date','Meeting','Source type','Status','Reference','Received','Reviewer','Source name','Captured at','Reviewed confidence','Notes'],all.flatMap(r=>r.sources.map(x=>[r.id+':'+x.id,r.date,r.meetingKey,x.type,x.status,x.reference||'',r.receivedAt||'',r.reviewerRole,x.name||'',x.capturedAt||'Not stated',x.confidence||'UNKNOWN',x.notes||''])));
  add('Issue History','append',['Revision key','Event date','Meeting date','Meeting','Issue ID','Concern','Severity','State','Owner','Action','Evidence'],all.flatMap(r=>r.issues.map(i=>[r.id+':'+i.issueId,i.eventDate,r.date,r.meetingKey,i.issueId,i.summary,i.severity,i.state,i.owner||'',i.action||'',evidenceText(i.evidence)])));
  currentRecords(s,cutoff).forEach(r=>{
    const name=(r.date+' '+r.meetingKey.slice(0,10)+' '+hashJson(JSON.stringify([r.meetingKey,new Date(r.startsAt).toISOString()])).slice(0,8)).slice(0,31);
    const rs          =[['Meeting',r.meetingKey,r.startsAt,r.status,r.id,r.statusNote||'']];
    r.metrics.forEach(m=>rs.push([m.field,m.value,m.appliesToDate,m.observedAt,'',evidenceText(m.evidence)]));r.issues.forEach(i=>rs.push([i.issueId,i.summary,i.eventDate,i.severity+' / '+i.state,i.owner+' / '+i.action,evidenceText(i.evidence)]));
    add(name,'refresh',['Field / issue','Value / concern','Date / start','Observed / status','Record / action','Evidence / note'],rs);
  });
  return {version:2,siteKey:p.siteKey,siteLabel:p.siteLabel,datasetMode:p.datasetMode,date:day,asOfUtc:new Date(cutoff).toISOString(),profileHash:hashJson(JSON.stringify(p)),snapshot,sheets};
}
function blockLookback(s      ,p        ,day       ,schedule              ,cutoff       )               {
  isoDay(day);check(schedule.version===1,'Unsupported block schedule.');const versions=schedule.versions.slice().sort((a,b)=>a.effectiveFrom.localeCompare(b.effectiveFrom));
  versions.forEach((v,index)=>{check(isoDay(v.effectiveFrom)<=isoDay(v.effectiveTo)&&(!index||versions[index-1].effectiveTo<v.effectiveFrom),'Overlapping or invalid block versions.');v.sessions.forEach(x=>check(isoDay(x.date)>=v.effectiveFrom&&x.date<=v.effectiveTo&&!!x.surgeonKey&&!!x.blockKey,'Invalid block session.'));});
  const current=versions.filter(v=>v.effectiveFrom<=day&&v.effectiveTo>=day);check(current.length===1,'One block version must cover target date.');
  const sessions=versions.flatMap(v=>v.sessions);const findings               =[];const previousMonth=dayOffset(day.slice(0,8)+'01',-1).slice(0,7);const ordinal=Math.floor((Number(day.slice(8))-1)/7);
  current[0].sessions.filter(x=>x.date===day).forEach(target=>{
    const previous=sessions.filter(x=>x.date<day&&x.surgeonKey===target.surgeonKey).sort((a,b)=>a.date.localeCompare(b.date));
    const monthly=previous.filter(x=>x.blockKey===target.blockKey&&x.date.slice(0,7)===previousMonth&&new Date(x.date).getUTCDay()===new Date(day).getUTCDay()&&Math.floor((Number(x.date.slice(8))-1)/7)===ordinal);
    [{mode:'previous_session',matches:previous.slice(-1)},{mode:'previous_month_block',matches:monthly.slice(-1)}].forEach(group=>group.matches.forEach(prior=>findings.push({mode:group.mode,target,prior,issues:currentRecords(s,cutoff).filter(r=>r.date===prior.date).flatMap(r=>r.issues.filter(i=>i.surgeonKey===target.surgeonKey||i.blockKey===target.blockKey).map(i=>({...i,recordId:r.id}))),interpretation:'Historical context only; no causal or predictive conclusion.'})));
  });return findings;
}
