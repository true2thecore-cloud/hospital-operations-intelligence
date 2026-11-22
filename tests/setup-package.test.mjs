import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync,existsSync} from 'node:fs';
import {createHash} from 'node:crypto';
import vm from 'node:vm';
import {wizardHarness} from './wizard-harness.mjs';
const root=new URL('../',import.meta.url),read=p=>readFileSync(new URL(p,root),'utf8');
const hash=bytes=>createHash('sha256').update(bytes).digest('hex');
test('original canonical files preserved against base manifest',()=>{
 const baseline=JSON.parse(read('tests/fixtures/preserved-base.json'));
 for(const entry of baseline){if(['README.md','.github/workflows/test.yml'].includes(entry.path))continue;assert.equal(hash(readFileSync(new URL(entry.path,root))),entry.sha256,entry.path);}
});
test('browser package embeds all canonical operational assets with exact bytes',()=>{
 const html=read('setup/index.html'),match=html.match(/const packageFiles=(.*);\n/);assert.ok(match);
 const files=JSON.parse(match[1]),manifest=JSON.parse(read('setup/bundle-manifest.json'));
 for(const item of manifest){assert.ok(files[item.path],item.path);const f=files[item.path];assert.equal(hash(f.encoding==='base64'?Buffer.from(f.content,'base64'):Buffer.from(f.content)),item.sha256,item.path);if(item.path!=='README.md')assert.equal(hash(readFileSync(new URL(item.path,root))),item.sha256,item.path);}
 for(const entry of JSON.parse(read('tests/fixtures/preserved-base.json')).filter(x=>/^(prompts|skills|agents|templates)\//.test(x.path)))assert.ok(files[entry.path],entry.path);
});
test('offline page has no network actions and contains real generated runtime',()=>{
 const html=read('setup/index.html');assert.match(html,/connect-src 'none'/);assert.doesNotMatch(read('setup/wizard.js'),/\b(fetch|XMLHttpRequest|WebSocket)\s*\(/);
 assert.match(html,/function closeDay/);assert.match(html,/function meetingPrompt/);assert.match(html,/function zipFiles/);assert.match(html,/not an importable Power Platform solution/);
});
test('perioperative profile includes original morning and afternoon question detail',()=>{
 const p=JSON.parse(read('config/readiness.perioperative-no-python.json'));
 const c=vm.createContext({Date,Intl});vm.runInContext(read('setup/runtime.js'),c);c.validateProfile(p);
 const am=p.meetings.find(m=>m.key==='plan_am'),pm=p.meetings.find(m=>m.key==='plan_pm');
 for(const term of ['Biomed','SPD','Supply chain','Assistant managers','PACU'])assert.ok(am.focus.includes(term),term);
 for(const key of ['anesthesia_tomorrow','remaining_preop','remaining_pacu','or_rn_available','or_cst_available','preop_staff','pacu_staff','phase2_staff','escalation_flag','source_confidence'])assert.ok(pm.fields.includes(key),key);
 assert.match(pm.focus,/Do not turn it into a universal clinical protocol/);
});
test('generated Office Script uses supported arrow callbacks and no external calls',()=>{
 const ts=read('scripts/RunReadinessNoPython.ts');assert.doesNotMatch(ts,/\.(?:map|forEach|filter|sort)\([A-Za-z_$][\w$]*\)/);assert.doesNotMatch(ts,/\bfetch\s*\(|:\s*any\b/);assert.equal((ts.match(/function main\(/g)||[]).length,1);
});

test('each exported prompt has its own unreviewed skeleton with no sample facts',()=>{
 const w=wizardHarness(),p=JSON.parse(JSON.stringify(w.run('profile')));
 p.siteLabel='Test Facility';p.meetings.push({...p.meetings[0],key:'new_huddle',label:'New local huddle',focus:'',reportOrder:[],fields:['census']});w.set('profile',p);
 const files=w.run('kitFiles()');
 for(const m of p.meetings){
  const prompt=files['organization/prompts/'+m.key+'.md'].content;
  const skeleton=JSON.parse(prompt.slice(prompt.indexOf('\n{',prompt.indexOf('## Draft record')),prompt.indexOf('\n\nPopulate arrays')));
  assert.equal(skeleton.meetingKey,m.key);assert.equal(skeleton.reviewerRole,'REPLACE_WITH_ROLE');
  for(const key of ['metrics','issues','sources'])assert.deepEqual(skeleton[key],[]);
  assert.equal(skeleton.date,'REPLACE_WITH_MEETING_DATE');assert.ok(prompt.includes('Meeting name: '+m.label));assert.ok(prompt.includes('Organization: Test Facility'));
  const marker='Mapped fields (do not rename their keys):\n',start=prompt.indexOf(marker)+marker.length;
  const fields=JSON.parse(prompt.slice(start,prompt.indexOf('\n\n## Draft record',start)));
  assert.deepEqual(fields.map(f=>f.key),m.fields);assert.doesNotMatch(prompt,/"value": 28|example-plan-am-2027|"reviewerRole": "Example reviewer"/);
 }
 assert.match(files['CONNECTION-SETUP-NOTES.md'].content,/New local huddle: questions or report-out order are blank/);
});

test('download saves organization edits and includes all prompts without preview',async()=>{
 const w=wizardHarness();w.element('org').value='Export Test';w.element('site-key').value='export_test';w.element('book-name').value='Export Test.xlsx';w.element('assistant').value='copilot';
 w.run('go(7)');w.element('next').onclick();assert.equal(w.downloads.length,1);
 const before=await w.downloads[0].arrayBuffer();const files=w.run('kitFiles()');
 assert.equal(JSON.parse(files['organization/readiness-profile.json'].content).siteLabel,'Export Test');
 assert.match(files['START-HERE-YOUR-SETUP.md'].content,/Organization: Export Test/);
 assert.equal(Object.keys(files).filter(k=>/^organization\/prompts\//.test(k)).length,6);
 w.element('show-prompt').onclick();w.element('next').onclick();assert.equal(w.downloads.length,2);
 assert.deepEqual(Buffer.from(await w.downloads[1].arrayBuffer()),Buffer.from(before));
});

test('email address and browser URL cannot be exported as mailbox folder names',()=>{
 for(const folders of ['https://mail.example.com/folders/inbox','person@example.com','mailto:person@example.com','Inbox; https://mail.example.com/sent']){
  const w=wizardHarness(),o=JSON.parse(JSON.stringify(w.run('options')));o.emailFolder=folders;w.set('options',o);
  assert.throws(()=>w.run('kitFiles()'),/folder names/);
  w.run('step=7;exportKit()');assert.equal(w.downloads.length,0);assert.match(w.element('error').textContent,/folder names/);
 }
 const w=wizardHarness();w.run("options.emailFolder='Inbox; Sent Items; Operations/Transcripts'");assert.doesNotThrow(()=>w.run('kitFiles()'));
});

test('business transcript folder is mapped separately and pending choices stay unverified',()=>{
 const w=wizardHarness();w.run("options.sourceFolder='https://example-my.sharepoint.com/my?id=%2Fpersonal%2Fsample%2FDocuments%2FMeetings';profile.workbookLocation='https://1drv.ms/f/c/example';options.brief=true");
 const files=w.run('kitFiles()'),connections=JSON.parse(files['organization/connections.json'].content),checks=JSON.parse(files['organization/setup-checks.json'].content);
 assert.equal(connections.rawSources,w.run('options.sourceFolder'));assert.equal(connections.transcriptEmail.folders,'Inbox; Sent Items');assert.equal(connections.verified,false);assert.equal(checks.connectionsVerified,false);
 assert.equal(checks.configurationValid,true);assert.ok(checks.pending.some(x=>x.includes('actual .xlsx')));assert.ok(checks.pending.some(x=>x.includes('Reviewed Records')));assert.ok(checks.pending.some(x=>x.includes('on demand')));
 assert.ok(!checks.pending.some(x=>x.includes('Choose a raw-source')));
});
