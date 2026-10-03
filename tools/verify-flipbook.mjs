import {createRequire} from 'node:module';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import assert from 'node:assert/strict';
const require=createRequire(process.env.PLAYWRIGHT_PACKAGE_PATH||'C:/Users/rites/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/package.json');
const {chromium}=require('playwright');
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..'),output=path.join(root,'tmp','verification');
const browser=await chromium.launch({executablePath:process.env.CHROME_PATH||'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});
const report={},errors=[];
try{
 const page=await browser.newPage({viewport:{width:1440,height:1200},hasTouch:true});
 page.on('pageerror',e=>errors.push(e.message));page.on('response',r=>{if(r.status()>=400)errors.push(`${r.status()} ${r.url()}`);});
 await page.goto('http://127.0.0.1:4173',{waitUntil:'networkidle'});await page.waitForSelector('html[data-ready=true]');
 assert.equal(await page.locator('#view-mode').count(),0);
 assert.equal(await page.locator('.page-frame:visible').count(),2);
 assert.equal(await page.locator('#spread-counter').innerText(),'1–2 / 8');
 await page.locator('#next-page').click();assert.equal(await page.locator('#spread-counter').innerText(),'3–4 / 8');
 await page.locator('#previous-page').click();assert.equal(await page.locator('#spread-counter').innerText(),'1–2 / 8');
 await page.evaluate(()=>document.activeElement.blur());await page.keyboard.press('ArrowRight');assert.equal(await page.locator('#spread-counter').innerText(),'3–4 / 8');
 await page.selectOption('#page-select','8');assert.equal(await page.locator('#spread-counter').innerText(),'7–8 / 8');assert.equal(await page.locator('#next-page').isDisabled(),true);
 await page.selectOption('#page-select','1');await page.waitForLoadState('networkidle');
 await page.screenshot({path:path.join(output,'desktop-spread.png')});
 report.desktop='Two-page spreads, arrows, page picker, keyboard, and boundaries passed';
 for(const width of [320,390,430,768,900,1440]){
  await page.setViewportSize({width,height:844});
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
