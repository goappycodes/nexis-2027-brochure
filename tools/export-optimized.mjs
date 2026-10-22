// Create one sharing PDF per edition from the current print masters.
import {spawnSync} from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const editions=[
  ['', 'General Brochure'],
  ['business-management', 'Business Management'],
  ['computer-science-ai', 'Computer Science and AI'],
  ['digital-marketing-commerce', 'Digital Marketing and Commerce']
];
// Check all inputs before starting any exports.
for(const [edition] of editions) {
  const name=edition?`nexis-2027-${edition}`:'nexis-2027';
  const source=path.join(root,'output/pdf/Print versions',`${name}-print.pdf`);
  if(!fs.existsSync(source))throw Error(`Print master missing: ${source}`);
}
for(const [edition,title] of editions) {
  const name=edition?`nexis-2027-${edition}`:'nexis-2027';
  console.log(`Optimizing ${title}`);
  const result=spawnSync(process.env.PYTHON_PATH||'python',[
    path.join(root,'tools/export-mobile.py'),
    '--source',path.join(root,'output/pdf/Print versions',`${name}-print.pdf`),
    '--output',path.join(root,'output/pdf/Optimized versions',`${name}-optimized.pdf`),
    '--title',`NEXIS 2027 - ${title} - Digital Sharing`,
    '--review-dir',path.join(root,'tmp/pdfs/optimized-review',edition||'general')
  ],{stdio:'inherit'});
  if(result.error)throw result.error;
  if(result.status!==0)throw Error(`Sharing export failed: ${title}`);
}
