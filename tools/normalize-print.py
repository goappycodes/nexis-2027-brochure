"""Trim Chromium's sub-point sheet rounding without rescaling the artwork."""
from pathlib import Path
import sys
from pypdf import PdfReader, PdfWriter
from pypdf.generic import RectangleObject

source, target = map(Path, sys.argv[1:3])
reader = PdfReader(source)
assert len(reader.pages) == 8, 'The print brochure must contain eight pages'
writer = PdfWriter()
writer.clone_document_from_reader(reader)
for page in writer.pages:
    assert abs(float(page.mediabox.width) - 1485) < 0.5
    assert abs(float(page.mediabox.height) - 2235) < 0.5
    page.mediabox = RectangleObject([0, 0, 1485, 2235])
    page.cropbox = RectangleObject([0, 0, 1485, 2235])
    page.trimbox = RectangleObject([0, 0, 1485, 2235])
writer.add_metadata({'/Title': 'NEXIS 2027 Brochure', '/Subject': 'Eight pages at 1485 x 2235 points'})
target.parent.mkdir(parents=True, exist_ok=True)
with target.open('wb') as stream:
    writer.write(stream)
final = PdfReader(target)
assert len(final.pages) == 8
assert all(list(page.mediabox) == list(page.cropbox) == list(page.trimbox) == [0, 0, 1485, 2235] for page in final.pages)
print(f'Created {target}: eight pages, each exactly 1485 x 2235 points')
