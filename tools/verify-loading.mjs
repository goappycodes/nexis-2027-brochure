import {createRequire} from 'node:module';
import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
const require=createRequire(process.env.PLAYWRIGHT_PACKAGE_PATH||'C:/Users/rites/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/package.json');
const {chromium}=require('playwright');
const base=process.env.BROCHURE_URL||'http://127.0.0.1:4173/';
const output='tmp/verification/loading';
await fs.mkdir(output,{recursive:true});
const browser=await chromium.launch({executablePath:process.env.CHROME_PATH||'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});
const report={};
try {
  const page=await browser.newPage({viewport:{width:1440,height:1200},reducedMotion:'reduce'});
  const errors=[],failures=[];
  page.on('pageerror',e=>errors.push(e.message));
  page.on('response',r=>{if(r.status()>=400)failures.push(`${r.status()} ${r.url()}`);});
  // Keep one cover image pending to verify nested SVG images hold the loader.
  const html=await (await fetch(base)).text();
  const artwork=[...html.matchAll(/<object class="page-artwork" data-src="([^"]+)"/g)].map(match=>new URL(match[1],base).href);
  assert.equal(artwork.length,8);
  const svg=await (await fetch(artwork[0])).text();
  const nested=[...svg.matchAll(/<image\b[^>]*\b(?:xlink:)?href="([^"]+)"/g)].at(-1)[1];
  const nestedURL=new URL(nested,artwork[0]).href;
  let release;
  const gate=new Promise(resolve=>release=resolve);
  await page.route(nestedURL,async route=>{await gate;await route.continue();});
  await page.goto(base,{waitUntil:'domcontentloaded'});
  await page.waitForSelector('.page-frame[data-page="1"] .page-loader',{state:'visible'});
  assert.equal(await page.locator('#page-1').evaluate(el=>el.closest('.page-frame').dataset.loadState),'loading');
  assert.equal(await page.locator('#page-1').evaluate(el=>getComputedStyle(el).visibility),'hidden');
  assert.equal(await page.locator('.page-frame[data-page="3"] object[data]').count(),0);
  await page.screenshot({path:output+'/cover-loading.png'});
  release();
  await page.waitForSelector('html[data-ready=true]');
  await page.waitForLoadState('networkidle');
  report.initial=await page.evaluate(()=>({requests:performance.getEntriesByType('resource').length,bytes:performance.getEntriesByType('resource').reduce((sum,r)=>sum+r.encodedBodySize,0),loadedPages:[...document.querySelectorAll('.page-frame[data-load-state=ready]')].map(el=>el.dataset.page)}));
  assert.deepEqual(report.initial.loadedPages,['1','2']);
  await page.screenshot({path:output+'/cover-ready.png'});
  // New pages get their own loader; an already loaded neighbour stays visible.
  let releaseDegree;
  const degreeGate=new Promise(resolve=>releaseDegree=resolve);
  await page.route(artwork[7],async route=>{await degreeGate;await route.continue();});
  await page.selectOption('#page-select','8');
  await page.waitForSelector('.page-frame[data-page="8"][data-load-state=loading]');
  assert.equal(await page.locator('#page-8').evaluate(el=>getComputedStyle(el).visibility),'hidden');
  await page.screenshot({path:output+'/degree-loading.png'});
  releaseDegree();
  await page.waitForSelector('.page-frame[data-page="8"][data-load-state=ready]');
  await page.locator('#page-8').screenshot({path:output+'/degree-ready.png'});
  // A failed asset must offer a retry rather than expose incomplete copy/artwork.
  let fail=true;
  await page.route(artwork[5],route=>{if(fail){fail=false;return route.abort('failed');}return route.continue();});
  await page.selectOption('#page-select','6');
  await page.waitForSelector('.page-frame[data-page="6"][data-load-state=error]');
  await page.locator('.page-frame[data-page="6"] .page-loader button').click();
  await page.waitForSelector('.page-frame[data-page="6"][data-load-state=ready]');
  report.retry='Failed artwork stays covered; retry recovers the page';
  await page.setViewportSize({width:390,height:844});
  await page.selectOption('#page-select','8');
  assert.equal(await page.locator('.page-frame.is-active').count(),1);
  await page.locator('#page-8').screenshot({path:output+'/degree-mobile.png'});
  // The print control must finish deferred pages before opening print preview.
  await page.setViewportSize({width:1440,height:1200});
  await page.evaluate(()=>window.print=()=>window.printedStates=[...document.querySelectorAll('.page-frame')].map(el=>el.dataset.loadState));
  await page.locator('#print').click();
  await page.waitForFunction(()=>window.printedStates?.length===8);
  assert.deepEqual(await page.evaluate(()=>window.printedStates),Array(8).fill('ready'));
  report.print='All eight pages ready before printing';
  const geometry=await page.evaluate(()=>({pages:[...document.querySelectorAll('.brochure-page')].map(el=>({width:el.offsetWidth,height:el.offsetHeight})),degreeOverflow:[...document.querySelectorAll('.degree-pathways article *')].filter(el=>{const r=el.getBoundingClientRect(),article=el.closest('article').getBoundingClientRect();return r.left<article.left-.5||r.right>article.right+.5||r.bottom>article.bottom+.5||el.scrollWidth>el.clientWidth+1;}).map(el=>el.textContent)}));
  assert.equal(geometry.pages.length,8);assert.ok(geometry.pages.every(p=>p.width===1485&&p.height===2235));assert.deepEqual(geometry.degreeOverflow,[]);
  await page.emulateMedia({media:'print'});
  assert.equal(await page.locator('.page-loader:visible').count(),0);
  report.geometry=geometry;
  assert.deepEqual(errors,[]);assert.deepEqual(failures,[]);
  report.editions=[];
  for(const edition of ['business-management','computer-science-ai','digital-marketing-commerce']) {
    await page.emulateMedia({media:'screen'});
    await page.goto(new URL(edition+'/',base).href,{waitUntil:'domcontentloaded'});
    await page.waitForSelector('html[data-ready=true]');
    await page.evaluate(()=>window.prepareBrochure());
    assert.equal(await page.locator('.page-frame[data-load-state=ready]').count(),8);
    report.editions.push(edition);
  }
  assert.deepEqual(errors,[]);assert.deepEqual(failures,[]);
  await fs.writeFile(output+'/report.json',JSON.stringify(report,null,2));
  console.log(JSON.stringify(report,null,2));
} finally {await browser.close();}
