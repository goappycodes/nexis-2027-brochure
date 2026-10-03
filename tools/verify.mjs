import { createRequire } from 'node:module';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const require = createRequire('C:/Users/rites/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/package.json');
const { chromium } = require('playwright');
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const output = path.join(root, 'tmp', 'verification');
fs.mkdirSync(output, { recursive: true });
const browser = await chromium.launch({ executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe', headless: true });
const page = await browser.newPage({ viewport: { width: 1100, height: 1450 }, deviceScaleFactor: 1 });
const errors = [];
page.on('pageerror', error => errors.push(error.message));
page.on('console', message => { if (message.type() === 'error') errors.push(message.text()); });
page.on('response', response => { if (response.status() >= 400) errors.push(`${response.status()} ${response.url()}`); });
await page.goto('http://127.0.0.1:4173', { waitUntil: 'networkidle' });
await page.waitForSelector('html[data-ready="true"]');
await page.evaluate(() => document.documentElement.dataset.view='pages');
await page.screenshot({ path: path.join(output, 'viewer.png') });
for (let i = 1; i <= 8; i++) {
  await page.locator(`.page-frame[data-page="${i}"]`).screenshot({ path: path.join(output, `page-${i}.png`) });
}
const summary = await page.evaluate(() => ({
  pages: document.querySelectorAll('.page-frame').length,
  copyBlocks: document.querySelectorAll('.placed').length,
  loadedFonts: [...document.fonts].filter(font => font.status === 'loaded').length,
  unloadedFonts: [...document.fonts].filter(font => font.status !== 'loaded').map(font => font.family),
  emptyText: [...document.querySelectorAll('.placed')].filter(run => !run.innerText.trim()).length,
  outOfBounds: [...document.querySelectorAll('.placed, .admissions-panel, .contact-panel')].filter(run => {
    const r = run.getBoundingClientRect(), p = run.closest('.page-frame').getBoundingClientRect();
    return r.left < p.left - 1 || r.top < p.top - 1 || r.right > p.right + 1 || r.bottom > p.bottom + 1;
  }).map(run => ({ page: run.closest('.page-frame').dataset.page, text: run.innerText.slice(0,100) })),
  typography: [...document.querySelectorAll('.brochure-copy h1, .brochure-copy h2, .brochure-copy .body-copy, .course-list, .eyebrow')].map(el => {
    const style=getComputedStyle(el);
    return { page: el.closest('.page-frame').dataset.page, text: el.textContent.slice(0,45), family: style.fontFamily, weight: style.fontWeight, size: style.fontSize, leading: style.lineHeight, spacing: style.letterSpacing, axes: style.fontVariationSettings };
  }),
  cardOverflow: [...document.querySelectorAll('.admission-card, .business-course-card, .business-project-card, .venture-card, .achievement-card')].filter(el=>el.scrollHeight>el.clientHeight+1).map(el=>({class:el.className,text:el.innerText})),
  overviewOverflow: [...document.querySelectorAll('.overview-course')].filter(el=>el.scrollHeight>el.clientHeight).map(el=>el.innerText),
  coverTagline: (() => {
    const el=document.querySelector('.cover-tagline');
    return { text: el.textContent, fontSize: getComputedStyle(el).fontSize, fits: el.scrollWidth <= el.clientWidth, lines: el.getClientRects().length };
  })(),
  alignment: (() => {
    const selectors='.alumni-panel, .backing-panel, .faculty-grid, .business-header, .business-learning-layout, .dual-programme, .internship-grid, .brand-logos, .achievements-layout, .campus-rows';
    return [...document.querySelectorAll(selectors)].map(el=>{
      const r=el.getBoundingClientRect(), frame=el.closest('.page-frame'), f=frame.getBoundingClientRect(), scale=f.width/1485;
      return { page:frame.dataset.page, container:el.className, left:Math.round((r.left-f.left)/scale), right:Math.round((r.right-f.left)/scale), aligned:Math.abs((r.left-f.left)/scale-120)<1 && Math.abs((r.right-f.left)/scale-1365)<1 };
    });
  })(),
  campusTabCentres: [...document.querySelectorAll('.campus-tab')].map(el=>{
    const box=el.getBoundingClientRect(), text=el.querySelector('span').getBoundingClientRect();
    return { text:el.textContent, dx:Math.round((text.left+text.width/2-box.left-box.width/2)*100)/100, dy:Math.round((text.top+text.height/2-box.top-box.height/2)*100)/100 };
  }),
  projectCopyOverlap: [...document.querySelectorAll('.business-project-card:not(.dual-project-card)')].filter(el=>el.querySelector('p:not(.eyebrow)').getBoundingClientRect().bottom>el.querySelector('.business-project-partners').getBoundingClientRect().top-5).map(el=>el.innerText),
  edits: (() => {
    const note=document.querySelector('.degree-note');
    const grid=document.querySelector('.faculty-grid');
    const cards=[...grid.querySelectorAll('.faculty-card')];
    const lines=el=>Math.round(el.offsetHeight/parseFloat(getComputedStyle(el).lineHeight));
    const internship=document.querySelector('.internship-title');
    return { facultyCards:cards.length, facultyRows:new Set(cards.map(el=>el.offsetTop)).size,
      facultyGap:getComputedStyle(grid).gap, degreeNoteLines:lines(note),
      overviewLines:[...document.querySelectorAll('.compact-copy')].map(lines),
      internshipHeadingFits:internship.scrollWidth<=internship.clientWidth,
      campusIntroLines:lines(document.querySelector('.campus-intro')), brandLogos:document.querySelectorAll('.brand-logo').length, studentSlots:document.querySelectorAll('.internship-card').length, studentPlaceholders:document.querySelectorAll('.internship-card[data-placeholder]').length, backingGap:Math.round((2140.5-1884-document.querySelector('.backing-panel').offsetHeight)/2) };
  })(),
  contactAlignment: (() => {
    const degree=document.querySelector('.degree-title').getBoundingClientRect();
    const admission=document.querySelector('.admissions-title').getBoundingClientRect();
    const contact=document.querySelector('.contact-panel > h2').getBoundingClientRect();
    return { degreeLeft: degree.left, admissionLeft: admission.left, contactLeft: contact.left };
  })(),
}));
await page.selectOption('#zoom', '0.75');
summary.zoomWidth = await page.locator('.page-frame').first().evaluate(el => el.getBoundingClientRect().width);
await page.selectOption('#page-select', '8');
await page.waitForFunction(() => document.querySelector('#page-8').getBoundingClientRect().top < 200);
summary.navigation = 'passed';
await page.setViewportSize({ width: 390, height: 844 });
await page.selectOption('#view-mode', 'reading');
summary.mobile = await page.evaluate(() => ({ scrollWidth: document.documentElement.scrollWidth, viewport: innerWidth, canvasWidth: document.querySelector('.page-frame').getBoundingClientRect().width }));
await page.screenshot({ path: path.join(output, 'mobile.png') });
await page.emulateMedia({ media: 'print' });
summary.print = await page.evaluate(() => ({ toolbarHidden: getComputedStyle(document.querySelector('.viewer-toolbar')).display === 'none', pages: document.querySelectorAll('.page-frame').length, pageWidth: document.querySelector('.page-frame').getBoundingClientRect().width }));
if (!process.argv.includes('--quick')) await page.pdf({ path: path.join(output, 'print-check.pdf'), preferCSSPageSize: true, printBackground: true, displayHeaderFooter: false });
summary.errors = errors;
fs.writeFileSync(path.join(output, 'browser-report.json'), JSON.stringify(summary, null, 2));
console.log(JSON.stringify({ ...summary, typography: `${summary.typography.length} heading, body, and label styles checked` }, null, 2));
await browser.close();
