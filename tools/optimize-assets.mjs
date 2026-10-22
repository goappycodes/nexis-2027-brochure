// Run only when adding/changing source photos. The normal build needs no packages.
import {createRequire} from 'node:module';
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {execFileSync} from 'node:child_process';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const require=createRequire(process.env.SHARP_PACKAGE_PATH||'C:/Users/rites/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/package.json');
const sharp=require('sharp');
const output=path.join(root,'assets','web');
await fs.mkdir(output,{recursive:true});
const previous=JSON.parse(await fs.readFile(path.join(output,'manifest.json'),'utf8').catch(error=>{
  if(error.code!=='ENOENT')throw error;return '{}';
}));
const manifest={};
let originalBytes=0,webBytes=0;
async function visit(directory) {
  for(const entry of await fs.readdir(directory,{withFileTypes:true})) {
    const file=path.join(directory,entry.name);
    if(entry.isDirectory()){await visit(file);continue;}
    if(!/\.(?:png|jpe?g|webp)$/i.test(entry.name))continue;
    const original=await fs.readFile(file);
    const key=path.relative(root,file).split(path.sep).join('/');
    const sourceHash=createHash('sha256').update(original).digest('hex');
    originalBytes+=original.length;
    const cached=previous[key];
    if(cached?.sourceHash===sourceHash) {
      const stat=await fs.stat(path.join(root,cached.file)).catch(error=>{if(error.code!=='ENOENT')throw error;return null;});
      if(stat){manifest[key]=cached;webBytes+=stat.size;continue;}
    }
    // Preserve source photos, transparency and proportions. Small logos stay lossless.
    const meta=await sharp(original).metadata();
    const small=Math.max(meta.width,meta.height)<=600;
    const image=await sharp(original).rotate().resize({width:2200,height:2200,fit:'inside',withoutEnlargement:true})
      .webp(small?{lossless:true,effort:6}:{quality:86,alphaQuality:100,effort:6}).toBuffer();
    if(image.length>=original.length){webBytes+=original.length;continue;}
    const name=createHash('sha256').update(image).digest('hex').slice(0,20)+'.webp';
    const target='assets/web/'+name;
    await fs.writeFile(path.join(output,name),image);
    manifest[key]={file:target,sourceHash};
    webBytes+=image.length;
  }
}
await visit(path.join(root,'assets','images'));
await fs.writeFile(path.join(output,'manifest.json'),JSON.stringify(manifest,null,2)+'\n');
console.log(JSON.stringify({optimized:Object.keys(manifest).length,originalBytes,webBytes,savedPercent:Math.round((1-webBytes/originalBytes)*100)}));
execFileSync(process.env.PYTHON_PATH||'python',[path.join(root,'tools/optimize-svg.py')],{stdio:'inherit'});
