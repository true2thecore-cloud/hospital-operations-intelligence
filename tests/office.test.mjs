import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { stripTypeScriptTypes } from 'node:module';
import vm from 'node:vm';

const source = readFileSync(new URL('../scripts/ImportOperationsBrief.ts', import.meta.url), 'utf8');
const ctx = vm.createContext({ ExcelScript: { ClearApplyTo: { all: 'all' }, VerticalAlignment: { top: 'top' } } });
vm.runInContext(stripTypeScriptTypes(source), ctx);

function workbook(marker = '', previous = '') {
  const writes = [], cleared = [];
  const fmt = new Proxy({}, {get:(_,key)=>key.startsWith('get')?()=>fmt:()=>{}});
  const sheet = {
    getUsedRange:()=>marker ? {} : undefined,
    getRange:address=>({getText:()=>address==='A1'?marker:address==='B3'?previous:'',unmerge:()=>{},clear:()=>cleared.push(address),setNumberFormat:()=>{},getFormat:()=>fmt}),
    getRangeByIndexes:(r,c,n,m)=>({setValues:rows=>writes.push({r,c,n,m,rows}),getFormat:()=>fmt}),
    setShowGridlines:()=>{},getFreezePanes:()=>({freezeRows:()=>{}})
  };
  return {getWorksheet:()=>sheet,addWorksheet:()=>sheet,writes,cleared};
}
function report(){return {version:1,datasetMode:'synthetic',siteLabel:'Example',date:'2027-01-22',asOfUtc:'2027-01-22T14:30:00Z',generatedUtc:'2027-01-22T14:30:00Z',meetings:[],issues:[{issueId:'one',state:'active',summary:'=TEST()',owner:'Role',action:'Review plan',due:'Today',date:'2027-01-22',meetingId:'am',evidence:[{cueId:'c1',start:'00:00:01.000',text:'Coverage gap.'}]}],warnings:[],missingMeetings:['Afternoon']};}

test('writes only dedicated fixed area, preserving text and evidence',()=>{
  const book=workbook();
  const result=JSON.parse(ctx.main(book,JSON.stringify(report())));
  assert.equal(result.status,'updated');
  assert.deepEqual(book.cleared,['A1:F500']);
  assert.equal(book.writes[0].rows[2][1],'2027-01-22T14:30:00Z');
  assert.ok(book.writes[0].rows.some(row=>row[0]==="'=TEST()"));
  assert.ok(book.writes[0].rows.some(row=>row[5].includes('Coverage gap.')));
});
test('refuses unrelated existing worksheet before clearing',()=>{
  const book=workbook('Private existing content');
  assert.throws(()=>ctx.main(book,JSON.stringify(report())),/not an operations view/);
  assert.equal(book.cleared.length,0);
});
test('rejects stale reports before changing cells',()=>{
  const book=workbook('HOSPITAL OPERATIONS INTELLIGENCE / v1','2027-01-22T16:00:00Z');
  assert.throws(()=>ctx.main(book,JSON.stringify(report())),/Older report/);
  assert.equal(book.cleared.length,0);
});
test('rejects source dashboard destination and oversized report',()=>{
  assert.throws(()=>ctx.main(workbook(),JSON.stringify(report()),'Charge Nurse Dashboard'),/dedicated/);
  const p=report();p.issues=Array(500).fill(p.issues[0]);
  const book=workbook();
  assert.throws(()=>ctx.main(book,JSON.stringify(p)),/500 rows/);
  assert.equal(book.cleared.length,0);
});
