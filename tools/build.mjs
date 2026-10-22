import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const output=path.resolve(root,'dist');
// Only this project's generated output may be replaced.
if(path.dirname(output)!==root||path.basename(output)!=='dist')throw Error('Invalid build directory');
await fs.rm(output,{recursive:true,force:true});
await fs.mkdir(output,{recursive:true});
const manifest=JSON.parse(await fs.readFile(path.join(root,'assets/web/manifest.json'),'utf8'));
const editions=['','digital-marketing-commerce','business-management','computer-science-ai'];
const queue=['brochure.css','flipbook.css','fonts.css','brochure.js',...editions.map(edition=>path.posix.join(edition,'index.html'))];
const copied=new Set();
let bytes=0;
function reference(url,from) {
  if(/^(?:[a-z][a-z\d+.-]*:|\/\/|#)/i.test(url))return url;
  const [pathname,suffix='']=url.split(/(?=[?#])/s,2);
  const source=path.posix.normalize(path.posix.join(path.posix.dirname(from),pathname));
  if(source.startsWith('../')||path.posix.isAbsolute(source))throw Error('Asset outside project: '+url);
  const target=manifest[source]?.file||source;
  queue.push(target);
  return path.posix.relative(path.posix.dirname(from),target)+suffix;
}
while(queue.length) {
  const file=queue.shift();
  if(copied.has(file))continue;
  copied.add(file);
  let content=await fs.readFile(path.join(root,file));
  if(/\.(?:html|svg|css)$/.test(file)) {
    let source=content.toString('utf8');
    source=source.replace(/\b((?:data-)?src|data|(?:xlink:)?href)="([^"]+)"/g,(_,attribute,url)=>`${attribute}="${reference(url,file)}"`);
    source=source.replace(/url\(\s*(["']?)([^"')]+)\1\s*\)/g,(_,quote,url)=>`url(${quote}${reference(url,file)}${quote})`);
    content=Buffer.from(source);
  }
  await fs.mkdir(path.dirname(path.join(output,file)),{recursive:true});
  await fs.writeFile(path.join(output,file),content);
  bytes+=content.length;
}
// Fail visibly if a changed original needs a fresh optimized version.
for(const [source,entry] of Object.entries(manifest)) {
  if(!copied.has(entry.file))continue;
  const original=await fs.readFile(path.join(root,source));
  const canonical=source.endsWith('.svg')?original.toString('utf8').replace(/\r\n/g,'\n'):original;
  const hash=createHash('sha256').update(canonical).digest('hex');
  if(hash!==entry.sourceHash)throw Error(`Run node tools/optimize-assets.mjs after changing ${source}`);
}
// Cached styles and scripts must always match the HTML from this build.
const versions=new Map();
for(const file of ['brochure.css','flipbook.css','brochure.js'])
  versions.set(file,createHash('sha256').update(await fs.readFile(path.join(output,file))).digest('hex').slice(0,12));
for(const edition of editions) {
  const file=path.join(output,edition,'index.html');
  const html=await fs.readFile(file,'utf8');
  await fs.writeFile(file,html.replace(/(href|src)="((?:\.\.\/)?(brochure\.css|flipbook\.css|brochure\.js))"/g,
    (_,attribute,url,name)=>`${attribute}="${url}?v=${versions.get(name)}"`));
}
console.log(`Static brochure built in dist/: ${copied.size} referenced files, ${(bytes/1e6).toFixed(2)} MB`);
