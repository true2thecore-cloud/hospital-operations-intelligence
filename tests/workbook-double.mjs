export function book(){
 const sheets=new Map();let writes=0;
 function add(name){
  const cells=[],styles=new Map(),heights=new Map(),widths=new Map();
  function range(r,c,n,m){
   const set=(k,v)=>{for(let i=r;i<r+n;i++)for(let j=c;j<c+m;j++){const key=i+','+j;styles.set(key,{...styles.get(key),[k]:v});}};
   const fmt={setWrapText:v=>set('wrap',v),setVerticalAlignment:v=>set('vertical',v),setColumnWidth:v=>{for(let j=c;j<c+m;j++)widths.set(j,v);},setRowHeight:v=>{for(let i=r;i<r+n;i++)heights.set(i,v);},getRowHeight:()=>heights.get(r)??15,autofitRows:()=>{for(let i=r;i<r+n;i++)heights.set(i,15);},getFill:()=>({setColor:v=>set('fill',v)}),getFont:()=>({setName:v=>set('font',v),setSize:v=>set('size',v),setBold:v=>set('bold',v),setColor:v=>set('color',v)})};
   return {getRowCount:()=>n,getValues:()=>Array.from({length:n},(_,i)=>Array.from({length:m},(_,j)=>cells[r+i]?.[c+j]??'')),getText:()=>String(cells[r]?.[c]??''),setValues:rows=>{writes++;rows.forEach((row,i)=>{cells[r+i]??=[];row.forEach((v,j)=>cells[r+i][c+j]=v);});},setNumberFormat:v=>set('numberFormat',v),getFormat:()=>fmt,unmerge:()=>{},clear:()=>{writes++;cells.length=0;styles.clear();heights.clear();}};
  }
  const s={cells,styles,heights,widths,getRangeByIndexes:range,getRange:a=>{const match=a.match(/^([A-Z]+)(\d+)(?::([A-Z]+)(\d+))?$/);if(!match)return range(0,0,1,1);const col=x=>[...x].reduce((n,c)=>n*26+c.charCodeAt(0)-64,0)-1;const r=+match[2]-1,c=col(match[1]);return range(r,c,match[4]?+match[4]-r:1,match[3]?col(match[3])-c+1:1);},getUsedRange:()=>cells.length?range(0,0,cells.length,Math.max(...cells.map(x=>x.length))):undefined,setVisibility:()=>{},setShowGridlines:()=>{},getFreezePanes:()=>({freezeRows:()=>{}})};
  sheets.set(name,s);return s;
 }
 return {sheets,get writes(){return writes;},getWorksheet:n=>sheets.get(n),addWorksheet:add};
}

