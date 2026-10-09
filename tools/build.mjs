import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const output=path.join(root,'dist');
await fs.mkdir(output,{recursive:true});
for(const file of ['index.html','brochure.css','flipbook.css','fonts.css','brochure.js']) await fs.copyFile(path.join(root,file),path.join(output,file));
await fs.cp(path.join(root,'assets'),path.join(output,'assets'),{recursive:true});
for(const edition of ['digital-marketing-commerce','business-management','computer-science-ai'])
  await fs.cp(path.join(root,edition),path.join(output,edition),{recursive:true});
console.log('Static brochure built in dist/');
