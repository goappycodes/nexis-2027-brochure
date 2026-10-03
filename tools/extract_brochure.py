"""Recover Figma's outlined glyphs as local fonts and its artwork as SVG.

The original PDF has vector outlines plus invisible Type3 text. Combining
the two lets us retain the original glyph shapes while producing real text.
Run with Python with PyMuPDF, pypdf, fontTools, Pillow, and lxml installed.
"""
from pathlib import Path
from collections import defaultdict
import base64
import html
import json
import math
import re
import sys

import fitz
from lxml import etree as ET
from pypdf import PdfReader
from fontTools.svgLib.path import parse_path
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.fontBuilder import FontBuilder
from fontTools.misc.transform import Transform

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'assets'
NS = {'s': 'http://www.w3.org/2000/svg'}
XLINK = '{http://www.w3.org/1999/xlink}href'
sys.stdout.reconfigure(encoding='utf-8')


def matrix(value):
    if not value:
        return Transform()
    nums = [float(x) for x in re.findall(r'[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?', value)]
    if value.startswith('matrix'):
        return Transform(*nums)
    if value.startswith('translate'):
        return Transform().translate(*nums)
    raise ValueError(value)


def world_matrix(element):
    result = Transform()
    for el in reversed([element, *element.iterancestors()]):
        result = result.transform(matrix(el.get('transform')))
    return result


def contours(d, transform):
    pen = RecordingPen()
    parse_path(d, TransformPen(pen, transform))
    parts = []
    current = []
    for item in pen.value:
        if item[0] == 'moveTo' and current:
            parts.append(current)
            current = []
        current.append(item)
        if item[0] in ('closePath', 'endPath'):
            parts.append(current)
            current = []
    if current:
        parts.append(current)
    return parts


def bounds(ops):
    pen = BoundsPen(None)
    for op, args in ops:
        getattr(pen, op)(*args)
    return pen.bounds


def normalized(ops, char):
    pen = RecordingPen()
    k=1000/char['size'];dx,dy=char['dir'];x,y=char['x'],char['y']
    t = Transform(dx*k,dy*k,dy*k,-dx*k,-(dx*x+dy*y)*k,(-dy*x+dx*y)*k)
    target = TransformPen(pen, t)
    for op, args in ops:
        getattr(target, op)(*args)
    return pen.value


def similar(a, b):
    if len(a) != len(b):
        return False
    for (op1, args1), (op2, args2) in zip(a, b):
        if op1 != op2 or len(args1) != len(args2):
            return False
        if any(abs(x-y) > 1.5 for p1, p2 in zip(args1, args2) for x,y in zip(p1,p2)):
            return False
    return True


def make_font(group, index):
    family = f'NexisOriginal{index:02}'
    cmap = group['glyphs']
    fb = FontBuilder(1000, isTTF=False)
    order = ['.notdef'] + [f'u{ord(c):04x}' for c in sorted(cmap)]
    fb.setupGlyphOrder(order)
    fb.setupCharacterMap({ord(c): f'u{ord(c):04x}' for c in cmap})
    glyphs = {}
    metrics = {}
    pen = T2CharStringPen(500, None)
    glyphs['.notdef'] = pen.getCharString()
    metrics['.notdef'] = (500, 0)
    for c, info in cmap.items():
        width = info['width']
        pen = T2CharStringPen(width, None)
        for op, args in info['ops']:
            getattr(pen, op)(*args)
        name = f'u{ord(c):04x}'
        glyphs[name] = pen.getCharString()
        box = bounds(info['ops'])
        metrics[name] = (round(width), round(box[0]) if box else 0)
    fb.setupCFF(family, {'FullName': family, 'FamilyName': family, 'Weight': 'Regular'}, glyphs, {})
    fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader(ascent=1000, descent=-300)
    fb.setupNameTable({'familyName': family, 'styleName': 'Regular', 'uniqueFontIdentifier': family,
                       'fullName': family, 'psName': family})
    fb.setupOS2(version=4, sTypoAscender=1000, sTypoDescender=-300, sTypoLineGap=0, usWinAscent=1000, usWinDescent=300, fsSelection=128)
    fb.setupPost()
    fb.save(ASSETS / 'fonts' / f'original-{index:02}.otf')
    group['family'] = family
    return family


def main():
    for folder in ['fonts', 'artwork', 'images']:
        (ASSETS / folder).mkdir(parents=True, exist_ok=True)
    doc = fitz.open(ROOT / 'brochure.pdf')
    reader = PdfReader(ROOT / 'brochure.pdf')
    font_metrics = {}
    pages = []
    path_groups = []
    image_files = {}
    audit = []
    for page_index, page in enumerate(doc):
        for ref in reader.pages[page_index]['/Resources']['/Font'].values():
            f = ref.get_object()
            if ref.idnum not in font_metrics:
                widths = {}
                for key, proc in f['/CharProcs'].items():
                    vals = [float(v) for v in proc.get_object().get_data().split()[:6]]
                    widths[int(key[2:])] = vals
                font_metrics[ref.idnum] = widths
        chars = []
        for trace_index, trace in enumerate(page.get_texttrace()):
            xref = int(re.search(r'\((\d+)', trace['font']).group(1))
            for cp, code, origin, _ in trace['chars']:
                if code < 0 or cp in [10, 13]:
                    continue
                width, _, xmin, ymin, xmax, ymax = font_metrics[xref][code]
                size = trace['size']; x,y = origin;dx,dy=trace['dir']
                if ymin>ymax:
                    ymin,ymax=-.3,1
                points=[(x+dx*u*size+dy*v*size,y+dy*u*size-dx*v*size) for u in [xmin,xmax] for v in [ymin,ymax]]
                bbox=(min(p[0] for p in points),min(p[1] for p in points),max(p[0] for p in points),max(p[1] for p in points))
                chars.append({'text':chr(cp), 'code':code, 'font':xref, 'size':size, 'x':x, 'y':y,
                    'width':width*1000, 'bbox':bbox, 'dir':(dx,dy),
                    'trace':trace_index, 'contours':[], 'paths':[], 'color':'#000000'})
        svg = ET.fromstring(page.get_svg_image(text_as_path=False).encode())
        paths=svg.xpath('.//s:path[not(ancestor::s:defs)]',namespaces=NS)
        all_parts=[]
        contour_boxes=[]
        for element in paths:
            parts=contours(element.get('d'),world_matrix(element)) if not element.get('stroke') else []
            all_parts.append(parts)
            contour_boxes.extend(b for b in (bounds(part) for part in parts) if b and b[2]-b[0]>.01 and b[3]-b[1]>.01)
        # Figma's accessibility text can start a bulleted paragraph before its
        # visible text inset. Recover that first-line inset from matching outlines.
        traced_lines=defaultdict(list)
        for char in chars:
            if char['dir']==(1.0,0.0):
                traced_lines[(char['trace'],round(char['y'],2))].append(char)
        for line_chars in traced_lines.values():
            first=next((c for c in line_chars if not c['text'].isspace()),None)
            if not first:continue
            cb=first['bbox'];size=first['size'];w=cb[2]-cb[0];h=cb[3]-cb[1]
            candidates=[]
            for box in contour_boxes:
                shift=box[0]-cb[0]
                if abs(shift)<size*.6 and abs((box[2]-box[0])-w)<.15 and abs(box[3]-cb[3])<.25 and abs((box[3]-box[1])-h)<size*.17:
                    candidates.append((abs(shift),shift))
            if candidates:
                _,shift=min(candidates)
                if abs(shift)>size*.07:
                    confirmed=0
                    for char in line_chars[:7]:
                        if char['text'].isspace():continue
                        b=char['bbox'];cw=b[2]-b[0]
                        if any(abs(box[0]-b[0]-shift)<.25 and abs(box[2]-box[0]-cw)<.2 and abs(box[3]-b[3])<.3 for box in contour_boxes):confirmed+=1
                    if confirmed>=2:
                        for char in line_chars:
                            char['x']+=shift
                            b=char['bbox'];char['bbox']=(b[0]+shift,b[1],b[2]+shift,b[3])
        matched_contours = 0
        residual=[]
        for path_index, element in enumerate(paths):
            if element.get('stroke'):
                continue
            t = world_matrix(element)
            parts = all_parts[path_index]
            remaining = []
            assigned = []
            for part in parts:
                box = bounds(part)
                # Empty Figma text-origin markers are safe to discard.
                if not box or (box[2]-box[0] < .01 and box[3]-box[1] < .01):
                    remaining.append(part)
                    continue
                candidates = []
                for ci, char in enumerate(chars):
                    if char['text'].isspace():
                        continue
                    cb = char['bbox']; tolerance=max(.7,char['size']*.05)
                    if box[0] >= cb[0]-tolerance and box[1] >= cb[1]-tolerance and box[2] <= cb[2]+tolerance and box[3] <= cb[3]+tolerance:
                        # Prefer the smallest surrounding glyph rectangle.
                        score=(cb[2]-cb[0])*(cb[3]-cb[1])
                        candidates.append((score,ci))
                if candidates:
                    _,ci=min(candidates)
                    chars[ci]['contours'].append(part)
                    chars[ci]['paths'].append(path_index)
                    chars[ci]['color']=element.get('fill','#000000')
                    assigned.append(ci); matched_contours+=1
                else:
                    remaining.append(part)
                    residual.append({'path':path_index,'bbox':box})
            if assigned:
                used=set(assigned)
                # Include spaces that lie between glyphs of the same original text path.
                traces={chars[ci]['trace'] for ci in used}
                for ci,char in enumerate(chars):
                    if char['text'].isspace() and char['trace'] in traces:
                        char['paths'].append(path_index)
                        char['color']=element.get('fill','#000000')
                        used.add(ci)
                path_groups.append({'page':page_index,'path':path_index,'chars':used})
                if remaining:
                    pen = SVGPathPen(None)
                    inverse = t.inverse()
                    target = TransformPen(pen, inverse)
                    for part in remaining:
                        for op,args in part:
                            getattr(target,op)(*args)
                    element.set('d',pen.getCommands())
                else:
                    element.getparent().remove(element)
        # Invisible Type3 text is replaced by the real HTML text layer.
        for text in svg.xpath('.//s:text',namespaces=NS):
            text.getparent().remove(text)
        for im in svg.xpath('.//s:image',namespaces=NS):
            data = im.get(XLINK) or im.get('href')
            if data and data.startswith('data:'):
                import hashlib
                payload=base64.b64decode(data.split(',',1)[1])
                digest=hashlib.sha256(payload).hexdigest()[:16]
                ext = 'png' if 'image/png' in data[:30] else 'jpg'
                filename=f'image-{digest}.{ext}'
                if filename not in image_files:
                    (ASSETS/'images'/filename).write_bytes(payload)
                    image_files[filename]=len(payload)
                im.set(XLINK,f'../images/{filename}')
                im.attrib.pop('href',None)
        (ASSETS/'artwork'/f'page-{page_index+1:02}.svg').write_bytes(ET.tostring(svg,encoding='utf-8',xml_declaration=True))
        missing=[c['text'] for c in chars if not c['text'].isspace() and not c['contours']]
        (ROOT/'tmp'/f'debug-{page_index+1}.json').write_text(json.dumps({'missing':[c for c in chars if not c['text'].isspace() and not c['contours']],'residual':residual},indent=2),encoding='utf-8')
        audit.append({'page':page_index+1,'characters':len(chars),'matched_contours':matched_contours,'missing':''.join(missing)})
        print(audit[-1],flush=True)
        pages.append({'width':page.rect.width,'height':page.rect.height,'chars':chars})

    # Combine compatible glyph maps so headings and body copy use a small set of fonts.
    groups=[]
    for path_info in path_groups:
        page=pages[path_info['page']]
        charmap={}
        for ci in sorted(path_info['chars']):
            char=page['chars'][ci]
            ops=[op for contour in char['contours'] for op in normalized(contour,char)]
            if char['text'] not in charmap or (not charmap[char['text']]['ops'] and ops):
                charmap[char['text']]={'ops':ops,'width':char['width'],'source':(char['font'],char['code'])}
        choice=None
        for gi, group in enumerate(groups):
            common=set(charmap)&set(group['glyphs'])-{' '}
            if common and all(similar(charmap[c]['ops'],group['glyphs'][c]['ops']) for c in common):
                choice=gi; break
        if choice is None:
            choice=len(groups);groups.append({'glyphs':{}})
        groups[choice]['glyphs'].update({c:v for c,v in charmap.items() if c not in groups[choice]['glyphs']})
        for ci in path_info['chars']:
            page['chars'][ci]['group']=choice
    for gi,group in enumerate(groups):
        # Spaces must be present even if a particular heading has no spaces.
        group['glyphs'].setdefault(' ',{'ops':[],'width':250,'source':None})
        make_font(group,gi)
    print('Recovered fonts:',len(groups),'images:',len(image_files),flush=True)
    css=[]
    for gi,group in enumerate(groups):
        css.append(f'@font-face {{ font-family: "{group["family"]}"; src: url("assets/fonts/original-{gi:02}.otf") format("opentype"); font-display: block; }}')
    (ROOT/'fonts.css').write_text('\n'.join(css)+'\n',encoding='utf-8')
    output=[]
    data=[]
    titles=['Cover','Undergraduate courses','Your faculty','Business Management curriculum','Marketing and Computer Science curriculum','Internships and achievements','Campus life','Degree and admissions']
    for pi,page in enumerate(pages):
        output.append(f'    <!-- PAGE {pi+1}: {titles[pi]} -->\n    <section class="page-frame" aria-label="Page {pi+1}: {titles[pi]}" data-page="{pi+1}" style="--page-width:{page["width"]};--page-height:{page["height"]}">\n      <div class="brochure-page" id="page-{pi+1}">\n        <object class="page-artwork" data="assets/artwork/page-{pi+1:02}.svg" type="image/svg+xml" aria-hidden="true" tabindex="-1"></object>\n        <div class="text-layer">')
        lines=defaultdict(list)
        for ci,char in enumerate(page['chars']):
            if 'group' in char:
                lines[(round(char['x'] if abs(char['dir'][1])>.5 else char['y'],2),char['trace'])].append(char)
        line_records=[]
        for line_index,(_,chars) in enumerate(sorted(lines.items(),key=lambda kv:(kv[0][0],min(c['x'] for c in kv[1])))):
            chars.sort(key=lambda c:c['x']*c['dir'][0]+c['y']*c['dir'][1])
            # Preserve font/color changes within each line as independent editable runs.
            runs=[]
            for char in chars:
                key=(char['group'],char['color'],char['size'])
                if not runs or runs[-1]['key']!=key:
                    runs.append({'key':key,'chars':[]})
                runs[-1]['chars'].append(char)
            for ri,run in enumerate(runs):
                cs=run['chars']; first=cs[0];group,color,size=run['key']
                text=''.join(c['text'] for c in cs)
                # Exact PDF advance at the final glyph; horizontal fit preserves Figma kerning.
                dx,dy=first['dir']
                target=(cs[-1]['x']-first['x'])*dx+(cs[-1]['y']-first['y'])*dy+cs[-1]['width']*size/1000
                rid=f'p{pi+1}-text-{line_index+1:03}-{ri+1}'
                angle=math.degrees(math.atan2(dy,dx))
                style=f'left:{first["x"]+dy*size:.5f}px;top:{first["y"]-dx*size:.5f}px;font-size:{size:g}px;font-family:{groups[group]["family"]};color:{color};--rotation:{angle:g}deg;--text-width:{target:.5f}px'
                output.append(f'          <div class="text-run" id="{rid}" style="{style}" data-width="{target:.5f}">{html.escape(text)}</div>')
                line_records.append({'id':rid,'text':text,'x':first['x'],'baseline':first['y'],'size':size,'font':group,'color':color,'width':target})
        output.append('        </div>\n      </div>\n    </section>')
        data.append({'page':pi+1,'title':titles[pi],'width':page['width'],'height':page['height'],'text':line_records})
    (ROOT/'tmp'/'brochure-pages.html').write_text('\n'.join(output),encoding='utf-8')
    (ROOT/'tmp'/'extraction-audit.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
    (ROOT/'tmp'/'layout.json').write_text(json.dumps(data,indent=2,ensure_ascii=False),encoding='utf-8')


if __name__=='__main__':
    main()
