"""Remove unreferenced PDF-extraction definitions; preserve all visible artwork."""
import hashlib
import json
import os
from pathlib import Path
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / 'assets/web'
manifest = json.loads((WEB / 'manifest.json').read_text())
ET.register_namespace('', 'http://www.w3.org/2000/svg')
ET.register_namespace('xlink', 'http://www.w3.org/1999/xlink')
before = after = 0
for source in sorted((ROOT / 'assets/artwork').rglob('*.svg')):
    original = source.read_bytes()
    svg = ET.fromstring(original)
    ids = {el.get('id'): el for el in svg.iter() if el.get('id')}
    active = set()
    queue = [svg]
    while queue:
        el = queue.pop()
        if el in active:
            continue
        active.add(el)
        queue.extend(child for child in el if child.tag.rsplit('}', 1)[-1] != 'defs')
        for value in el.attrib.values():
            refs = re.findall(r'url\([\s\'"]*#([^\s\'"\)]+)', value)
            if value.startswith('#'):
                refs.append(value[1:])
            queue.extend(ids[ref] for ref in refs if ref in ids)
    for defs in list(svg.iter('{http://www.w3.org/2000/svg}defs')):
        for child in list(defs):
            if not any(el in active for el in child.iter()):
                defs.remove(child)
    for el in svg.iter():
        for key, value in list(el.attrib.items()):
            if key.rsplit('}', 1)[-1] != 'href' or value.startswith(('#', 'data:', 'http:', 'https:')):
                continue
            target = (source.parent / value).resolve()
            relative = target.relative_to(ROOT).as_posix()
            # Both artwork/ and web/ sit directly under assets/.
            if relative in manifest:
                el.set(key, Path(manifest[relative]['file']).name)
            else:
                el.set(key, os.path.relpath(target, WEB).replace('\\', '/'))
    content = ET.tostring(svg, encoding='utf-8')
    content = re.sub(rb'>\s+<', b'><', content)
    name = hashlib.sha256(content).hexdigest()[:20] + '.svg'
    (WEB / name).write_bytes(content)
    manifest[source.relative_to(ROOT).as_posix()] = {
        'file': 'assets/web/' + name,
        'sourceHash': hashlib.sha256(original.replace(b'\r\n', b'\n')).hexdigest(),
    }
    before += len(original)
    after += len(content)
(WEB / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
print(json.dumps({'svgOriginalBytes': before, 'svgWebBytes': after}))
