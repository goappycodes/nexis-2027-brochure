"""Flatten the print master to high-resolution pages using lossless PNG data."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import struct

import fitz
from PIL import Image
from pypdf import PdfReader, PdfWriter
from pypdf.generic import ArrayObject, BooleanObject, DecodedStreamObject, DictionaryObject, EncodedStreamObject, NameObject, NumberObject

ROOT = Path(__file__).resolve().parent.parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source', type=Path, default=ROOT / 'output/pdf/nexis-2027-print.pdf')
parser.add_argument('--output', type=Path, default=ROOT / 'output/pdf/nexis-2027-mobile.pdf')
parser.add_argument('--dpi', type=int, default=240)
args = parser.parse_args()
if not args.source.is_file():
    parser.error('Print master missing. Run npm run export:print first.')
if args.dpi < 144:
    parser.error('Use at least 144 dpi for readable flattened text.')
if args.dpi % 24:
    parser.error('Use a multiple of 24 dpi to preserve the exact page pixel grid.')
if args.source.resolve() == args.output.resolve():
    parser.error('The mobile copy must not overwrite the print master.')

source = fitz.open(args.source)
assert len(source) == 8
writer = PdfWriter()
hashes, dimensions = [], []
review = ROOT / 'tmp/pdfs/mobile-review'
review.mkdir(parents=True, exist_ok=True)

for index, page in enumerate(source):
    assert tuple(page.mediabox) == (0, 0, 1485, 2235)
    pixels = page.get_pixmap(dpi=args.dpi, colorspace=fitz.csRGB, alpha=False, annots=True)
    hashes.append(hashlib.sha256(pixels.samples).hexdigest())
    dimensions.append([pixels.width, pixels.height])
    image = Image.frombytes('RGB', (pixels.width, pixels.height), pixels.samples)
    image.copy().resize((743, 1118), Image.Resampling.LANCZOS).save(review / f'page-{index + 1}.png')
    buffer = io.BytesIO()
    image.save(buffer, format='PNG', optimize=True, compress_level=9)
    data, offset, compressed = buffer.getvalue(), 8, bytearray()
    while offset < len(data):
        length = struct.unpack('>I', data[offset:offset + 4])[0]
        kind = data[offset + 4:offset + 8]
        if kind == b'IDAT':
            compressed.extend(data[offset + 8:offset + 8 + length])
        offset += 12 + length
    # Preserve the PNG's adaptive scanline filters and compressed RGB bytes.
    # There is no JPEG encoding, color quantization, or image resampling here.
    graphic = EncodedStreamObject()
    graphic._data = bytes(compressed)
    graphic.update({
        NameObject('/Type'): NameObject('/XObject'),
        NameObject('/Subtype'): NameObject('/Image'),
        NameObject('/Width'): NumberObject(pixels.width),
        NameObject('/Height'): NumberObject(pixels.height),
        NameObject('/ColorSpace'): NameObject('/DeviceRGB'),
        NameObject('/BitsPerComponent'): NumberObject(8),
        NameObject('/Filter'): NameObject('/FlateDecode'),
        NameObject('/Interpolate'): BooleanObject(False),
        NameObject('/DecodeParms'): DictionaryObject({
            NameObject('/Predictor'): NumberObject(15),
            NameObject('/Colors'): NumberObject(3),
            NameObject('/BitsPerComponent'): NumberObject(8),
            NameObject('/Columns'): NumberObject(pixels.width),
        }),
    })
    output = writer.add_blank_page(width=1485, height=2235)
    output[NameObject('/Resources')] = DictionaryObject({
        NameObject('/XObject'): DictionaryObject({NameObject('/PageImage'): writer._add_object(graphic)})
    })
    content = DecodedStreamObject()
    content.set_data(b'q\n1485 0 0 2235 0 0 cm\n/PageImage Do\nQ\n')
    output[NameObject('/Contents')] = writer._add_object(content)
    output.cropbox = output.mediabox
    output.trimbox = output.mediabox
    print(f'Flattened page {index + 1}/8: {pixels.width} x {pixels.height}, {len(compressed)/1_000_000:.2f} MB lossless', flush=True)
    image.close()
    del pixels, data, compressed, image, buffer

writer.add_metadata({'/Title': 'NEXIS 2027 - Mobile Brochure', '/Subject': f'Flattened pages, lossless RGB compression, {args.dpi} dpi'})
writer._root_object[NameObject('/PageLayout')] = NameObject('/SinglePage')
writer._root_object[NameObject('/PageMode')] = NameObject('/UseNone')
writer._root_object[NameObject('/OpenAction')] = ArrayObject([writer.pages[0].indirect_reference, NameObject('/Fit')])
args.output.parent.mkdir(parents=True, exist_ok=True)
with args.output.open('wb') as stream:
    writer.write(stream)

result = fitz.open(args.output)
reader = PdfReader(args.output)
assert len(result) == len(reader.pages) == 8
assert '/AcroForm' not in reader.trailer['/Root']
assert not result.get_ocgs()
for index, page in enumerate(result):
    assert tuple(page.mediabox) == tuple(page.cropbox) == tuple(page.trimbox) == (0, 0, 1485, 2235)
    assert len(page.get_images()) == 1
    assert not page.get_fonts() and not page.get_text() and not list(page.annots() or [])
    pixels = page.get_pixmap(dpi=args.dpi, colorspace=fitz.csRGB, alpha=False)
    assert hashlib.sha256(pixels.samples).hexdigest() == hashes[index], f'Pixel mismatch on page {index + 1}'
    print(f'Verified page {index + 1}/8: pixel-identical at {args.dpi} dpi', flush=True)
    del pixels
report = {'source_bytes': args.source.stat().st_size, 'output_bytes': args.output.stat().st_size,
          'dpi': args.dpi, 'page_pixels': dimensions, 'pages': 8, 'lossy_compression': False,
          'pixel_identical_at_export_resolution': True, 'source_pixel_hashes': hashes}
(review / 'verification.json').write_text(json.dumps(report, indent=2))
print(json.dumps({key: value for key, value in report.items() if key not in ['source_pixel_hashes', 'page_pixels']}, indent=2))
