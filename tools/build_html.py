"""Assemble the editable HTML after re-extracting the original PDF."""
from pathlib import Path
import json

root=Path(__file__).resolve().parents[1]
pages=(root/'tmp/brochure-pages.html').read_text(encoding='utf-8')
layout=json.loads((root/'tmp/layout.json').read_text(encoding='utf-8'))
print_css='\n'.join(f'@page nexis{p["page"]} {{ size: {p["width"]*4/3:g}px {p["height"]*4/3:g}px; margin: 0; }}\n.page-frame[data-page="{p["page"]}"] {{ page: nexis{p["page"]}; }}' for p in layout)
options='\n'.join(f'        <option value="{p["page"]}">{p["page"]} / 8 · {p["title"]}</option>' for p in layout)
head='''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="NEXIS School of Business — 2027 undergraduate programme brochure.">
  <title>NEXIS — 2027 Brochure</title>
  <link rel="icon" href="data:,">
  <link rel="stylesheet" href="brochure.css">
  <style>
'''+print_css+'''
  </style>
  <script src="brochure.js" defer></script>
</head>
<body>
  <header class="viewer-toolbar" aria-label="Brochure viewer">
    <div class="viewer-brand"><strong>NEXIS</strong><span>2027 PROGRAMME BROCHURE</span></div>
    <nav class="viewer-controls" aria-label="View options">
      <select id="page-select" aria-label="Go to page">
'''+options+'''
      </select>
      <select id="zoom" aria-label="Zoom">
        <option value="fit">Fit to screen</option>
        <option value="0.5">50%</option>
        <option value="0.75">75%</option>
        <option value="1">100%</option>
      </select>
      <button class="print-button" id="print" type="button">Print / PDF</button>
    </nav>
  </header>
  <main class="brochure" aria-label="NEXIS 2027 brochure">
'''
(root/'index.html').write_text(head+pages+'\n  </main>\n</body>\n</html>\n',encoding='utf-8')
print('Built index.html')
