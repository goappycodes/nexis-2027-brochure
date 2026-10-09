import {createRequire} from 'node:module';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {spawnSync} from 'node:child_process';
const require=createRequire(process.env.PLAYWRIGHT_PACKAGE_PATH||'C:/Users/rites/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/package.json');
const {chromium}=require('playwright');
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const edition=process.env.BROCHURE_EDITION;
if(edition && edition!=='digital-marketing-commerce')throw Error('Unknown brochure edition');
const name=edition?`nexis-2027-${edition}-print`:'nexis-2027-print';
const raw=path.join(root,'tmp','pdfs',`${name}-chromium.pdf`),output=path.join(root,'output','pdf',`${name}.pdf`);
fs.mkdirSync(path.dirname(raw),{recursive:true});
const browser=await chromium.launch({executablePath:process.env.CHROME_PATH||'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});
try {
 const page=await browser.newPage({viewport:{width:1440,height:1200}});
 await page.goto(process.env.BROCHURE_URL||`http://127.0.0.1:4173/${edition?edition+'/':''}`,{waitUntil:'domcontentloaded'});
 await page.waitForSelector('html[data-ready=true]');
 await page.evaluate(()=>document.documentElement.dataset.view='pages');
 await page.waitForFunction(()=>[...document.querySelectorAll('object')].every(o=>o.contentDocument?.readyState==='complete'),null,{timeout:120000});
 const count=await page.locator('object:not(.page-artwork)').count();
 for(let index=0;index<count;index++) {
  await page.locator('object:not(.page-artwork)').first().evaluate(async object=>{
   const root=object.contentDocument.documentElement.cloneNode(true),base=object.data;
   for(const image of root.querySelectorAll('image')) {
    const href=image.getAttributeNS('http://www.w3.org/1999/xlink','href')||image.getAttribute('href');
    if(!href||href.startsWith('data:')||href.startsWith('#'))continue;
    const response=await fetch(new URL(href,base));if(!response.ok)throw Error(`Image failed: ${href}`);
    const blob=await response.blob(),url=await new Promise(resolve=>{const reader=new FileReader();reader.onload=()=>resolve(reader.result);reader.readAsDataURL(blob);});
    image.setAttributeNS('http://www.w3.org/1999/xlink','xlink:href',url);
    image.removeAttribute('href');
   }
   const bounds=object.getBoundingClientRect(),style=getComputedStyle(object),width=parseFloat(style.width)-parseFloat(style.paddingLeft)-parseFloat(style.paddingRight),height=parseFloat(style.height)-parseFloat(style.paddingTop)-parseFloat(style.paddingBottom);
   root.setAttribute('width',width);root.setAttribute('height',height);
   const svgUrl=URL.createObjectURL(new Blob([new XMLSerializer().serializeToString(root)],{type:'image/svg+xml'}));
   const source=new Image();source.src=svgUrl;await source.decode();
   const canvas=document.createElement('canvas'),scale=300/72;
   canvas.width=Math.ceil(width*scale);canvas.height=Math.ceil(height*scale);
   canvas.getContext('2d').drawImage(source,0,0,canvas.width,canvas.height);
   const replacement=document.createElement('img');
   for(const attribute of object.attributes)if(!['data','type'].includes(attribute.name))replacement.setAttribute(attribute.name,attribute.value);
   // Tag-specific object rules must survive replacement with a print image.
   for(const property of ['width','height','display','padding','border','border-radius','object-fit','box-sizing','position','top','left','right','bottom','vertical-align'])replacement.style.setProperty(property,style.getPropertyValue(property));
   replacement.alt='';replacement.src=canvas.toDataURL('image/png');await replacement.decode();
   object.replaceWith(replacement);URL.revokeObjectURL(svgUrl);canvas.width=canvas.height=0;
   const result=replacement.getBoundingClientRect();
   if(['width','height','left','top'].some(key=>Math.abs(result[key]-bounds[key])>.3))throw Error(`Artwork moved during print preparation: ${base}`);
  });
  if((index+1)%20===0)console.log(`Prepared ${index+1} / ${count} artwork panels at 300 dpi`);
 }
 await page.emulateMedia({media:'print'});
 await page.pdf({path:raw,preferCSSPageSize:true,printBackground:true,displayHeaderFooter:false});
 const result=spawnSync(process.env.PYTHON_PATH||'python',[path.join(root,'tools','normalize-print.py'),raw,output,await page.title()],{stdio:'inherit'});
 if(result.error)throw result.error;if(result.status!==0)throw Error('Print page normalization failed');
} finally {await browser.close();}
