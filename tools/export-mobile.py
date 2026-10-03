"""Export eight flattened pages within a mobile-sharing size budget."""
import argparse
import hashlib
import io
import json
import math
from pathlib import Path
import struct

import fitz
from PIL import Image, ImageChops
from pypdf import PdfReader, PdfWriter
from pypdf.generic import (
    ArrayObject, BooleanObject, DecodedStreamObject, DictionaryObject,
    EncodedStreamObject, NameObject, NumberObject,
)

ROOT = Path(__file__).resolve().parent.parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source', type=Path, default=ROOT / 'output/pdf/nexis-2027-print.pdf')
parser.add_argument('--output', type=Path, default=ROOT / 'output/pdf/nexis-2027-mobile.pdf')
parser.add_argument('--dpi', type=int, default=240)
parser.add_argument('--compression', choices=('sharing', 'lossless'), default='sharing')
parser.add_argument('--max-mb', type=float, default=25, help='Decimal MB limit; 0 disables the limit.')
args = parser.parse_args()
if not args.source.is_file():
    parser.error('Print master missing. Run npm run export:print first.')
if args.dpi < 144 or args.dpi % 24:
    parser.error('Use a multiple of 24 dpi, at least 144, for an exact page pixel grid.')
if args.max_mb < 0 or not math.isfinite(args.max_mb):
    parser.error('The file size limit must be a finite, non-negative number.')
if args.source.resolve() == args.output.resolve():
    parser.error('The mobile copy must not overwrite the print master.')

review = ROOT / 'tmp/pdfs/mobile-review'
review.mkdir(parents=True, exist_ok=True)
source = fitz.open(args.source)
assert len(source) == 8
qualities = list(range(98, 89, -1)) if args.compression == 'sharing' else [None]
encoded, hashes, dimensions = [], [], []

for index, page in enumerate(source):
    assert tuple(page.mediabox) == (0, 0, 1485, 2235)
    pixels = page.get_pixmap(dpi=args.dpi, colorspace=fitz.csRGB, alpha=False, annots=True)
    hashes.append(hashlib.sha256(pixels.samples).hexdigest())
    dimensions.append([pixels.width, pixels.height])
    image = Image.frombytes('RGB', (pixels.width, pixels.height), pixels.samples)
    variants = {}
    for quality in qualities:
        buffer = io.BytesIO()
        if quality is not None:
            # Preserve full RGB detail: no chroma subsampling or resizing.
            image.save(buffer, format='JPEG', quality=quality, subsampling=0, optimize=True)
            variants[quality] = buffer.getvalue()
        else:
            image.save(buffer, format='PNG', optimize=True, compress_level=9)
            data, offset, compressed = buffer.getvalue(), 8, bytearray()
            while offset < len(data):
                length = struct.unpack('>I', data[offset:offset + 4])[0]
                if data[offset + 4:offset + 8] == b'IDAT':
                    compressed.extend(data[offset + 8:offset + 8 + length])
                offset += 12 + length
            variants[quality] = bytes(compressed)
    encoded.append(variants)
    image.close()
    del pixels, image
    print(f'Encoded page {index + 1}/8 at {args.dpi} dpi', flush=True)


def make_pdf(quality):
    writer = PdfWriter()
    for variants, (width, height) in zip(encoded, dimensions):
        graphic = EncodedStreamObject()
        graphic._data = variants[quality]
        graphic.update({
            NameObject('/Type'): NameObject('/XObject'),
            NameObject('/Subtype'): NameObject('/Image'),
            NameObject('/Width'): NumberObject(width),
            NameObject('/Height'): NumberObject(height),
            NameObject('/ColorSpace'): NameObject('/DeviceRGB'),
            NameObject('/BitsPerComponent'): NumberObject(8),
            NameObject('/Filter'): NameObject('/DCTDecode' if quality is not None else '/FlateDecode'),
            NameObject('/Interpolate'): BooleanObject(False),
        })
        if quality is None:
            graphic[NameObject('/DecodeParms')] = DictionaryObject({
                NameObject('/Predictor'): NumberObject(15),
                NameObject('/Colors'): NumberObject(3),
                NameObject('/BitsPerComponent'): NumberObject(8),
                NameObject('/Columns'): NumberObject(width),
            })
        page = writer.add_blank_page(width=1485, height=2235)
        page[NameObject('/Resources')] = DictionaryObject({
            NameObject('/XObject'): DictionaryObject({NameObject('/PageImage'): writer._add_object(graphic)})
        })
        content = DecodedStreamObject()
        content.set_data(b'q\n1485 0 0 2235 0 0 cm\n/PageImage Do\nQ\n')
        page[NameObject('/Contents')] = writer._add_object(content)
        page.cropbox = page.trimbox = page.mediabox
    compression = 'lossless RGB' if quality is None else f'JPEG quality {quality}, full RGB'
    writer.add_metadata({'/Title': 'NEXIS 2027 - Mobile Brochure',
                         '/Subject': f'Flattened pages, {compression}, {args.dpi} dpi'})
    writer._root_object[NameObject('/PageLayout')] = NameObject('/SinglePage')
    writer._root_object[NameObject('/PageMode')] = NameObject('/UseNone')
    writer._root_object[NameObject('/OpenAction')] = ArrayObject([writer.pages[0].indirect_reference, NameObject('/Fit')])
    buffer = io.BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


limit = int(args.max_mb * 1_000_000)
for quality in qualities:
    data = make_pdf(quality)
    if not limit or len(data) <= limit:
        break
else:
    parser.error('The size limit cannot be met at this resolution and quality. '
                 'Use --dpi 192 or increase --max-mb; the previous PDF is unchanged.')
print(f'Selected {args.compression}, quality {quality}: {len(data) / 1_000_000:.2f} MB', flush=True)
encoded.clear()

# Verify the actual exported PDF before replacing the previous sharing copy.
result = fitz.open(stream=data, filetype='pdf')
reader = PdfReader(io.BytesIO(data))
assert len(result) == len(reader.pages) == 8
assert '/AcroForm' not in reader.trailer['/Root']
assert not result.get_ocgs()
scores = []
for index, page in enumerate(result):
    assert tuple(page.mediabox) == tuple(page.cropbox) == tuple(page.trimbox) == (0, 0, 1485, 2235)
    assert len(page.get_images()) == 1
    assert not page.get_fonts() and not page.get_text() and not list(page.annots() or [])
    pixels = page.get_pixmap(dpi=args.dpi, colorspace=fitz.csRGB, alpha=False)
    assert [pixels.width, pixels.height] == dimensions[index]
    exported = Image.frombytes('RGB', (pixels.width, pixels.height), pixels.samples)
    exported.resize((743, 1118), Image.Resampling.LANCZOS).save(review / f'page-{index + 1}.png')
    if quality is None:
        assert hashlib.sha256(pixels.samples).hexdigest() == hashes[index], f'Pixel mismatch on page {index + 1}'
    else:
        original_pixels = source[index].get_pixmap(dpi=args.dpi, colorspace=fitz.csRGB, alpha=False, annots=True)
        original = Image.frombytes('RGB', (pixels.width, pixels.height), original_pixels.samples)
        histogram = ImageChops.difference(exported, original).histogram()
        mse = sum((value % 256) ** 2 * count for value, count in enumerate(histogram)) / (pixels.width * pixels.height * 3)
        psnr = 10 * math.log10(255 ** 2 / mse) if mse else 100.0
        assert psnr >= 38, f'Compression quality too low on page {index + 1}: {psnr:.2f} dB'
        scores.append(round(psnr, 2))
        original.close()
        del original_pixels
    exported.close()
    del pixels
    print(f'Verified page {index + 1}/8', flush=True)

args.output.parent.mkdir(parents=True, exist_ok=True)
temporary = args.output.with_suffix('.pending.pdf')
temporary.write_bytes(data)
temporary.replace(args.output)
report = {'source_bytes': args.source.stat().st_size, 'output_bytes': len(data),
          'max_bytes': limit or None, 'dpi': args.dpi, 'page_pixels': dimensions, 'pages': 8,
          'lossy_compression': quality is not None, 'jpeg_quality': quality,
          'chroma_subsampling': False, 'page_psnr_db': scores,
          'pixel_identical_at_export_resolution': quality is None}
(review / 'verification.json').write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
