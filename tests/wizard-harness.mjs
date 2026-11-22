// Unit harness for the shipped offline wizard. No browser, account or network access.
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
const root=new URL('../',import.meta.url),read=p=>readFileSync(new URL(p,root),'utf8');
export function wizardHarness(){
 const nodes=new Map(),downloads=[];
 const element=id=>{if(!nodes.has(id))nodes.set(id,{value:'',innerHTML:'',textContent:'',checked:false,classList:{remove(){}},click(){}});return nodes.get(id);};
 const document={getElementById:element,querySelectorAll:()=>[],createElement:()=>({click(){}})};
 const packageFiles=JSON.parse(read('setup/index.html').match(/const packageFiles=(.*);\n/)[1]);
 const context=vm.createContext({Date,Intl,document,window:{},packageFiles,Blob,TextEncoder,Uint8Array,DataView,atob,URL:{createObjectURL:b=>{downloads.push(b);return 'blob:local-test';},revokeObjectURL(){}},setTimeout:()=>0});
 vm.runInContext(read('setup/runtime.js'),context);
 vm.runInContext(read('setup/wizard.js'),context);
 return {context,element,downloads,run:code=>vm.runInContext(code,context),set:(name,value)=>{context.__testValue=value;vm.runInContext(name+'=JSON.parse(JSON.stringify(__testValue))',context);delete context.__testValue;}};
}
