const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const path = require('node:path');
const elements = new Map();
function element(id) {
  if (!elements.has(id)) elements.set(id, {value:'10',textContent:'',hidden:false,
    addEventListener(){},querySelectorAll(){return [];},classList:{add(){},remove(){}},rows:[]});
  return elements.get(id);
}
let gets = 0, resolveFirst;
const context = vm.createContext({
  document:{hidden:false,getElementById:element,querySelectorAll:()=>[],addEventListener(){}},
  AbortController, AbortSignal, setTimeout, clearTimeout, queueMicrotask,
  setInterval:()=>0,clearInterval(){},confirm:()=>true,alert(){},
  fetch:async (url, options)=>{
    if(options.method==='POST') return {ok:true,json:async()=>({message:'ok'})};
    gets++;
    if(gets===1) return new Promise(resolve=>{resolveFirst=resolve;});
    return {ok:false,json:async()=>({error:'test failure'})};
  }
});
vm.runInContext(fs.readFileSync(path.join(__dirname,'static/app.js'),'utf8'),context);
const items=[{name:'B',memory_usage:1},{name:'A',memory_usage:20}];
assert.equal(context.sortComponents(items,'memory_usage',-1)[0].name,'A');
assert.equal(context.sortComponents(items,'memory_usage',1)[0].name,'B');
assert.equal(context.sortComponents(items,'name',1)[0].name,'A');
assert.equal(items[0].name,'B');
(async()=>{
  await context.stopApp({name:'Test',slug:'test'},element('button'));
  assert.equal(gets,1);
  resolveFirst({ok:true,json:async()=>({})});
  await new Promise(resolve=>setImmediate(resolve));
  await new Promise(resolve=>setImmediate(resolve));
  assert.equal(gets,2,'New read must run immediately after in-flight read, without interval');
  console.log('Sorting and stop/read race tests passed');
})().catch(error=>{console.error(error);process.exitCode=1;});
