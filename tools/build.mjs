import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const output=path.join(root,'dist');
await fs.mkdir(output,{recursive:true});
for(const file of ['index.html','brochure.css','flipbook.css','fonts.css','brochure.js']) await fs.copyFile(path.join(root,file),path.join(output,file));
await fs.cp(path.join(root,'assets'),path.join(output,'assets'),{recursive:true});
for(const edition of ['digital-marketing-commerce','business-management','computer-science-ai'])
  await fs.cp(path.join(root,edition),path.join(output,edition),{recursive:true});
// Cached styles and scripts must always match the HTML from this build.
const versions=new Map();
for(const file of ['brochure.css','flipbook.css','brochure.js'])
  versions.set(file,createHash('sha256').update(await fs.readFile(path.join(output,file))).digest('hex').slice(0,12));
for(const edition of ['', 'digital-marketing-commerce','business-management','computer-science-ai']) {
  const file=path.join(output,edition,'index.html');
  const html=await fs.readFile(file,'utf8');
  await fs.writeFile(file,html.replace(/(href|src)="((?:\.\.\/)?(brochure\.css|flipbook\.css|brochure\.js))"/g,
    (_,attribute,url,name)=>`${attribute}="${url}?v=${versions.get(name)}"`));
}
console.log('Static brochure built in dist/');
