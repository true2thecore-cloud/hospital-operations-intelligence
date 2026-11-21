import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync,existsSync} from 'node:fs';
import {createHash} from 'node:crypto';
import vm from 'node:vm';
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
