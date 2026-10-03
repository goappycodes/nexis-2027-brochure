"""Apply the /ug/2027 website typography to the editable brochure text.

Only reads the website repository. All copied assets and changes belong
to this brochure project. Run after rebuilding HTML from the PDF.
"""
from pathlib import Path
from lxml import etree as ET
import re
import shutil

ROOT=Path(__file__).resolve().parents[1]
WEBSITE=Path(r'C:\Users\rites\Desktop\projects\nexis-2027-website')
MEDIA=WEBSITE/'.next/static/media'
FILES={
    'fraunces-variable.woff2':'cb9f64d62d112b41-s.p.woff2',
    'poppins-regular.woff2':'eafabf029ad39a43-s.p.woff2',
    'poppins-medium.woff2':'8888a3826f4a3af4-s.p.woff2',
    'poppins-semibold.woff2':'0484562807a97172-s.p.woff2',
    'poppins-bold.woff2':'b957ea75a84b6ea7-s.p.woff2',
}


def properties(style):
    return dict(part.split(':',1) for part in style.split(';') if ':' in part)


def typography(page, text, size, font):
    if size>=67.5:
        return 'heading'
    if page==2 and (font==9 or size==52.5):
        return 'heading'
    if page==6 and (font in (46,49,50) or text.strip()=='National Achievements'):
        return 'heading'
    if page in (4,5) and size==31.5:
        return 'subheading'
    if page==8 and size==30 and 58<=font<=61:
        return 'subheading'
    return 'body'


def main():
    for filename,source in FILES.items():
        shutil.copyfile(MEDIA/source,ROOT/'assets/fonts'/filename)
    css='''/* Exact Latin font files from nexis-2027-website /ug/2027.
   Metrics overrides align native HTML text to the brochure's PDF baselines.
   The glyph shapes, weights, OpenType features, and variable axes are original. */
@font-face {
  font-family: "Fraunces";
  src: url("assets/fonts/fraunces-variable.woff2") format("woff2");
  font-style: normal;
  font-weight: 100 900;
  font-display: block;
  ascent-override: 100%;
  descent-override: 30%;
  line-gap-override: 0%;
}
'''
    for weight,name in [(400,'regular'),(500,'medium'),(600,'semibold'),(700,'bold')]:
        css+=f'''@font-face {{
  font-family: "Poppins";
  src: url("assets/fonts/poppins-{name}.woff2") format("woff2");
  font-style: normal;
  font-weight: {weight};
  font-display: block;
  ascent-override: 100%;
  descent-override: 30%;
  line-gap-override: 0%;
}}
'''
    (ROOT/'fonts.css').write_text(css,encoding='utf-8')
    parser=ET.HTMLParser()
    doc=ET.parse(str(ROOT/'index.html'),parser)
    count=0
    for section in doc.xpath('//section[@data-page]'):
        page=int(section.get('data-page'))
        layer=section.find('.//div[@class="text-layer"]')
        runs=[]
        for el in layer:
            props=properties(el.get('style',''))
            text=el.text or ''
            size=float(props['font-size'].rstrip('px'))
            font=int(props['font-family'].replace('NexisOriginal','')) if props['font-family'].startswith('NexisOriginal') else -1
            role=typography(page,text,size,font)
            italic=(font in [8,13,14,31,32,40,48,62] and role=='heading')
            runs.append({'el':el,'props':props,'text':text,'size':size,'role':role,'italic':italic,
                         'left':float(props['left'].rstrip('px')),'top':float(props['top'].rstrip('px')),
                         'rotation':float(props.get('--rotation','0deg').rstrip('deg')),
                         'width':float(el.get('data-width','0'))})
        # Merge adjacent chunks of the same line. PDF accessibility font changes
        # had split even simple words into multiple positioned spans.
        merged=[]
        for run in runs:
            previous=merged[-1] if merged else None
            if previous and abs(run['top']-previous['top'])<.02 and run['rotation']==0 and previous['rotation']==0 and run['role']==previous['role'] and run['size']==previous['size'] and run['props']['color']==previous['props']['color'] and run['italic']==previous['italic'] and abs(run['left']-(previous['left']+previous['width']))<1.2:
                previous['text']+=run['text']
                previous['width']=run['left']+run['width']-previous['left']
            else:
                merged.append(run)
        for el in list(layer):layer.remove(el)
        for run in merged:
            if not run['text'].strip():continue
            el=run['el'];props=run['props'];count+=1
            text=run['text']
            # Repair PDF text extraction errors while preserving the visible copy.
            text=text.replace('Certifcation','Certification').replace('Eligibilty','Eligibility').replace('Visting','Visiting')
            el.text=text
            role=run['role']
            el.set('class','text-run type-'+role+(' type-italic' if run['italic'] else ''))
            props.pop('font-family',None)
            props['--font-size']=props.pop('font-size')
            props['--text-width']=f'{run["width"]:.5f}px'
            # Place the baseline explicitly so shrink-to-fit preserves alignment.
            dx=0 if abs(run['rotation'])==90 else 1
            dy=-1 if run['rotation']==-90 else (1 if run['rotation']==90 else 0)
            props['left']=f'{run["left"]-dy*run["size"]:.5f}px'
            props['top']=f'{run["top"]+dx*run["size"]:.5f}px'
            props['--original-size']=f'{run["size"]:g}px'
            weight=400
            if role=='body':
                # Labels and captions retain the hierarchy of the source layout.
                upper=text.strip().isupper()
                if upper or (run['size']>=30 and len(text.strip())<22):weight=500
                if page==3 and run['size']==25.5:weight=600
            props['font-weight']=str(weight)
            el.set('style',';'.join(f'{k}:{v}' for k,v in props.items()))
            el.set('data-width',f'{run["width"]:.5f}')
            el.set('data-size',f'{run["size"]:g}')
            layer.append(el)
    (ROOT/'index.html').write_bytes(ET.tostring(doc,encoding='utf-8',method='html',doctype='<!doctype html>'))
    print(f'Standardized {count} editable text runs to Fraunces / Poppins.')


if __name__=='__main__':main()
