import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {stripTypeScriptTypes} from 'node:module';
import vm from 'node:vm';
const ctx=vm.createContext({ExcelScript:{ClearApplyTo:{all:'all'},VerticalAlignment:{top:'top'}}});
vm.runInContext(stripTypeScriptTypes(readFileSync(new URL('../scripts/UpdateReadinessWorkbook.ts',import.meta.url),'utf8')),ctx);
function book(){
 const sheets=new Map();let writes=0;
 function add(name){
  const cells=[],styles=new Map(),heights=new Map(),widths=new Map();
  function range(r,c,n,m){
   const set=(k,v)=>{for(let i=r;i<r+n;i++)for(let j=c;j<c+m;j++){const key=i+','+j;styles.set(key,{...styles.get(key),[k]:v});}};
   const fmt={setWrapText:v=>set('wrap',v),setVerticalAlignment:v=>set('vertical',v),setColumnWidth:v=>{for(let j=c;j<c+m;j++)widths.set(j,v);},setRowHeight:v=>{for(let i=r;i<r+n;i++)heights.set(i,v);},getRowHeight:()=>heights.get(r)??15,autofitRows:()=>{for(let i=r;i<r+n;i++)heights.set(i,15);},getFill:()=>({setColor:v=>set('fill',v)}),getFont:()=>({setName:v=>set('font',v),setSize:v=>set('size',v),setBold:v=>set('bold',v),setColor:v=>set('color',v)})};
   return {getValues:()=>Array.from({length:n},(_,i)=>Array.from({length:m},(_,j)=>cells[r+i]?.[c+j]??'')),getText:()=>String(cells[r]?.[c]??''),setValues:rows=>{writes++;rows.forEach((row,i)=>{cells[r+i]??=[];row.forEach((v,j)=>cells[r+i][c+j]=v);});},setNumberFormat:v=>set('numberFormat',v),getFormat:()=>fmt,unmerge:()=>{},clear:()=>{writes++;cells.length=0;styles.clear();heights.clear();}};
  }
  const s={cells,styles,heights,widths,getRangeByIndexes:range,getRange:a=>{const match=a.match(/^([A-Z]+)(\d+)(?::([A-Z]+)(\d+))?$/);if(!match)return range(0,0,1,1);const col=x=>[...x].reduce((n,c)=>n*26+c.charCodeAt(0)-64,0)-1;const r=+match[2]-1,c=col(match[1]);return range(r,c,match[4]?+match[4]-r:1,match[3]?col(match[3])-c+1:1);},getUsedRange:()=>cells.length?range(0,0,cells.length,Math.max(...cells.map(x=>x.length))):undefined,setShowGridlines:()=>{},getFreezePanes:()=>({freezeRows:()=>{}})};
  sheets.set(name,s);return s;
 }
 return {sheets,get writes(){return writes;},getWorksheet:n=>sheets.get(n),addWorksheet:add};
}
function p(){return {version:2,siteKey:'test',siteLabel:'Test',datasetMode:'synthetic',date:'2027-01-22',asOfUtc:'2027-01-23T04:00:00Z',sheets:[{name:'Executive Snapshot',mode:'refresh',headers:['Metric','Value'],rows:[['Census',250]],keys:[]},{name:'Master Table',mode:'append',headers:['Date','Count','Hash'],rows:[['2027-01-22',250,'hash1']],keys:['2027-01-22']}]};}
test('repeat publication does not append twice and snapshot can refresh',()=>{
 const b=book(),data=p();ctx.main(b,JSON.stringify(data));data.sheets[0].rows[0][1]=256;
 const result=JSON.parse(ctx.main(b,JSON.stringify(data)));
 assert.equal(result.appendedRows,0);assert.equal(b.sheets.get('Master Table').cells.length,4);assert.equal(b.sheets.get('Executive Snapshot').cells[3][1],256);
});
test('changed frozen row fails before any writes',()=>{
 const b=book(),data=p();ctx.main(b,JSON.stringify(data));const before=b.writes;data.sheets[1].rows[0][1]=999;
 assert.throws(()=>ctx.main(b,JSON.stringify(data)),/Immutable/);assert.equal(b.writes,before);
});
test('appends next day and preserves original',()=>{
 const b=book(),data=p();ctx.main(b,JSON.stringify(data));data.sheets[1].rows.push(['2027-01-23',251,'hash2']);data.sheets[1].keys.push('2027-01-23');
 ctx.main(b,JSON.stringify(data));assert.equal(b.sheets.get('Master Table').cells[3][1],250);assert.equal(b.sheets.get('Master Table').cells[4][1],251);
});
test('schema mismatch unrelated sheets and stale publication rejected',()=>{
 const b=book(),data=p();ctx.main(b,JSON.stringify(data));const before=b.writes;
 data.sheets[1].headers[1]='Different';assert.throws(()=>ctx.main(b,JSON.stringify(data)),/schema/);assert.equal(b.writes,before);
 const old=p();old.asOfUtc='2027-01-22T04:00:00Z';assert.throws(()=>ctx.main(b,JSON.stringify(old)),/Older/);
 const other=book();other.addWorksheet('Master Table').getRange('A1').setValues([['Unrelated']]);assert.throws(()=>ctx.main(other,JSON.stringify(p())),/unrelated/);
});
test('escapes formula-like source text and refuses dataset mixing',()=>{
 const b=book(),data=p();data.sheets[0].rows[0][1]='=TEST()';ctx.main(b,JSON.stringify(data));assert.equal(b.sheets.get('Executive Snapshot').cells[3][1],"'=TEST()");
 data.datasetMode='operational';assert.throws(()=>ctx.main(b,JSON.stringify(data)),/mix/);
});
test('refresh restores section styling, widths and number formats without cumulative spacing',()=>{
 const b=book(),data=p();data.sheets[0]={name:'Executive Snapshot',mode:'refresh',headers:['Metric','Value','Unit','Date','Observed','Evidence'],keys:[],rows:[['Census',256,'patients','','',''],['Capacity',83.25,'percent','','',''],['','','','','',''],['SEVEN-DAY HIGH / MEDIUM EVENTS','','','','',''],['Event date','Concern','Severity','Status','Owner / action','Evidence']]};
 ctx.main(b,JSON.stringify(data));const exec=b.sheets.get('Executive Snapshot'),before=JSON.stringify([...exec.heights]);
 assert.equal(exec.styles.get('6,0').fill,'#397BB0');assert.equal(exec.styles.get('6,0').color,'#FFFFFF');
 assert.equal(exec.styles.get('3,1').numberFormat,'#,##0');assert.equal(exec.styles.get('4,1').numberFormat,'General');
 exec.styles.get('6,0').fill='#BADBAD';exec.widths.set(1,999);
 ctx.main(b,JSON.stringify(data));assert.equal(exec.styles.get('6,0').fill,'#397BB0');assert.equal(exec.widths.get(1),280);
 assert.equal(JSON.stringify([...exec.heights]),before);assert.equal(exec.cells[4][1],83.25);
});
test('long audit text remains immutable and has complete bounded continuation rows on repeat',()=>{
 const b=book(),data=p(),text=('First line\n'+ 'source evidence '.repeat(38)+'✅').repeat(5);
 data.sheets[1].headers.push('Metric provenance');data.sheets[1].rows[0].push(text);
 ctx.main(b,JSON.stringify(data));const master=b.sheets.get('Master Table'),before=JSON.stringify(master.cells);
 assert.equal(master.styles.get('3,3').numberFormat,'0;-0;0;"Full text: Audit Details"');
 const detail=b.sheets.get('Audit Details');let parts=detail.cells.slice(3).map(r=>r[4]);
 assert.equal(parts.join(''),text);assert.ok(parts.every(x=>x.length<=301 && x.split('\n').length<=6));
 master.styles.get('3,1').numberFormat='0.############';
 const result=JSON.parse(ctx.main(b,JSON.stringify(data)));
 assert.equal(result.appendedRows,0);assert.equal(JSON.stringify(master.cells),before);assert.equal(master.styles.get('3,1').numberFormat,'#,##0');
 assert.equal(detail.cells.slice(3).map(r=>r[4]).join(''),text);
});
test('unrelated detail sheet blocks publication before changing any output',()=>{
 const b=book();b.addWorksheet('Audit Details').getRange('A1').setValues([['User notes']]);const before=b.writes;
 assert.throws(()=>ctx.main(b,JSON.stringify(p())),/unrelated/);assert.equal(b.writes,before);
});
test('detail view includes historical rows omitted from an incremental payload',()=>{
 const b=book(),data=p(),long='Evidence '.repeat(60);data.sheets[1].rows[0][2]=long;ctx.main(b,JSON.stringify(data));
 data.sheets[1].rows=[['2027-01-23',260,'short']];data.sheets[1].keys=['2027-01-23'];ctx.main(b,JSON.stringify(data));
 assert.equal(b.sheets.get('Audit Details').cells.slice(3).map(r=>r[4]).join(''),long);
 assert.equal(b.sheets.get('Master Table').cells[3][2],long);
});
