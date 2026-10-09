import {createRequire} from 'node:module';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import assert from 'node:assert/strict';
const require=createRequire(process.env.PLAYWRIGHT_PACKAGE_PATH||'C:/Users/rites/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/package.json');
const {chromium}=require('playwright');
const edition=process.env.BROCHURE_EDITION||'';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..'),output=path.join(root,'tmp','verification',edition);
const browser=await chromium.launch({executablePath:process.env.CHROME_PATH||'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});
const report={},errors=[];
fs.mkdirSync(output,{recursive:true});
try{
 const page=await browser.newPage({viewport:{width:1440,height:1200},hasTouch:true});
 const waitForFit=()=>page.waitForFunction(()=>{
  const columns=innerWidth>=900?2:1, main=document.querySelector('.brochure'), layout=getComputedStyle(main);
  const width=(innerWidth-(columns===2?120:24)-(columns===2?parseFloat(layout.columnGap):0))/(1485*columns);
  const height=(innerHeight-document.querySelector('.viewer-toolbar').getBoundingClientRect().height-parseFloat(layout.paddingTop)-parseFloat(layout.paddingBottom))/2235;
  return document.querySelectorAll('.page-frame.is-active').length===columns&&Math.abs(document.querySelector('.page-frame').getBoundingClientRect().width/1485-Math.min(width,columns===2?height:Infinity))<.00002;
 });
 page.on('pageerror',e=>errors.push(e.message));page.on('response',r=>{if(r.status()>=400)errors.push(`${r.status()} ${r.url()}`);});
 await page.goto(process.env.BROCHURE_URL||`http://127.0.0.1:4173/${edition?edition+'/':''}`,{waitUntil:'domcontentloaded'});await page.waitForSelector('html[data-ready=true]');
 const dimensions=await page.locator('.brochure-page').evaluateAll(pages=>pages.map(p=>({width:p.offsetWidth,height:p.offsetHeight})));
 assert.equal(dimensions.length,8);assert.ok(dimensions.every(p=>p.width===1485&&p.height===2235));
 report.dimensions=dimensions;
 report.fit=[];
 for(const viewport of [{width:1366,height:768},{width:1920,height:1080},{width:900,height:600}]){
  await page.setViewportSize(viewport);
  await waitForFit();
  const fit=await page.evaluate(()=>({width:innerWidth,height:innerHeight,documentHeight:document.documentElement.scrollHeight,toolbarBottom:document.querySelector('.viewer-toolbar').getBoundingClientRect().bottom,pages:[...document.querySelectorAll('.page-frame.is-active')].map(p=>{const r=p.getBoundingClientRect();return {left:r.left,right:r.right,top:r.top,bottom:r.bottom,width:r.width,height:r.height};})}));
  assert.equal(fit.pages.length,2);assert.ok(fit.documentHeight<=fit.height+1);
  assert.ok(fit.pages.every(p=>p.left>=0&&p.right<=fit.width&&p.top>=fit.toolbarBottom&&p.bottom<=fit.height));
  assert.equal(fit.pages[0].height,fit.pages[1].height);report.fit.push(fit);
 }
 await page.selectOption('#zoom','0.75');
 assert.equal(await page.locator('.page-frame').first().evaluate(p=>p.getBoundingClientRect().width),1485*.75);
 await page.selectOption('#zoom','fit');
 await page.setViewportSize({width:1440,height:1200});
 await waitForFit();
 assert.equal(await page.locator('#view-mode').count(),0);
 assert.equal(await page.locator('.page-frame:visible').count(),2);
 assert.equal(await page.locator('#spread-counter').innerText(),'1–2 / 8');
 await page.locator('#next-page').click();assert.equal(await page.locator('#spread-counter').innerText(),'3–4 / 8');
 await page.locator('#previous-page').click();assert.equal(await page.locator('#spread-counter').innerText(),'1–2 / 8');
 await page.evaluate(()=>document.activeElement.blur());await page.keyboard.press('ArrowRight');assert.equal(await page.locator('#spread-counter').innerText(),'3–4 / 8');
 await page.selectOption('#page-select','8');assert.equal(await page.locator('#spread-counter').innerText(),'7–8 / 8');assert.equal(await page.locator('#next-page').isDisabled(),true);
 await page.selectOption('#page-select','1');await page.waitForLoadState('networkidle');
 await page.screenshot({path:path.join(output,'desktop-spread.png'),animations:'disabled'});
 report.desktop='Two-page spreads, arrows, page picker, keyboard, and boundaries passed';
 for(const width of [320,390,430,768,900,1440]){
  await page.setViewportSize({width,height:844});
  await waitForFit();
  const check=await page.evaluate(()=>({width:innerWidth,documentWidth:document.documentElement.scrollWidth,pages:[...document.querySelectorAll('.page-frame.is-active')].map(p=>p.dataset.page),touchAction:getComputedStyle(document.querySelector('.brochure')).touchAction}));
  assert.equal(check.pages.length,width>=900?2:1);assert.equal(check.documentWidth,width);
  report[width]=check;
  if(width===390)await page.screenshot({path:path.join(output,'mobile-flipbook.png')});
 }
 await page.setViewportSize({width:390,height:844});await page.selectOption('#page-select','1');
 const swipe=async()=>{
  await page.evaluate(()=>{
   const target=document.querySelector('.brochure');
   const start=new Touch({identifier:0,target,clientX:300,clientY:300}),end=new Touch({identifier:0,target,clientX:100,clientY:300});
   target.dispatchEvent(new TouchEvent('touchstart',{touches:[start],bubbles:true}));
   target.dispatchEvent(new TouchEvent('touchend',{changedTouches:[end],bubbles:true}));
  });
 };
 await swipe();assert.equal(await page.locator('#page-select').inputValue(),'2');
 const session=await page.context().newCDPSession(page);await session.send('Emulation.setPageScaleFactor',{pageScaleFactor:2});
 assert.equal(await page.evaluate(()=>visualViewport.scale),2);
 await swipe();assert.equal(await page.locator('#page-select').inputValue(),'2');
 await session.send('Emulation.setPageScaleFactor',{pageScaleFactor:1});
 const viewport=await page.locator('meta[name=viewport]').getAttribute('content');assert.equal(/maximum-scale|user-scalable\s*=\s*no/.test(viewport),false);
 report.mobile='One page, swipe navigation, and zoomed swipe guard passed; native pinch zoom enabled';
 report.errors=errors;assert.deepEqual(errors,[]);
 fs.writeFileSync(path.join(output,'flipbook-report.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));
}finally{await browser.close();}
