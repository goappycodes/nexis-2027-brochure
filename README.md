# NEXIS 2027 brochure

An editable, eight-page editorial prospectus with a forest-green, ivory, coral,
and warm-gold palette. The original content, photography, and brand artwork are
preserved. Typography uses the exact Fraunces and Poppins font files from the
website's `/ug/2027` page.

## Open the brochure

Run `npm run dev`, then open <http://127.0.0.1:4173>.
There is no installation or build step. The viewer includes page navigation,
zoom, and Print / PDF. All assets and fonts are local.

Desktop shows two pages per view; phones show one. Subtle side arrows, a page
picker, and arrow keys turn pages. Phones support horizontal swipes and native
pinch-to-zoom. The viewer keeps the brochure's fixed page design on every device.
Desktop opens in Fit to screen, fitting the full spread to both the available
width and height. The zoom selector still supports larger views.

## Deploy on Vercel

Import this repository and select the `main` branch. The included `vercel.json`
sets the static build to `npm run build` and the output directory to `dist`.
There are no application dependencies or environment variables to configure.
The build copies the HTML, styles, scripts, fonts, and artwork; development tools
and the original reference PDF are excluded from the deployed site.

## Make edits

- **Copy and content:** edit `index.html`. Each page has a `PAGE` comment.
  Paragraphs, lists, cards, and captions are normal HTML.
- **Fonts and spacing:** edit `brochure.css`. Typography is shared by role;
  headings use Fraunces 400, body uses Poppins 400, and labels use Poppins 600.
- **Flipbook controls:** edit `flipbook.css` and `brochure.js`. Their screen-only
  rules control spreads, navigation, and touch behaviour.
- **Positioning:** named section classes in `brochure.css` define the layout
  on a 1485 x 2235-unit canvas. The shared text margin is 120 units. Move
  semantic sections as a whole; grids handle courses, people, and projects.
- **Artwork:** original photos live in `assets/images/`. The cover and campus
  gallery use those originals directly. The original page SVGs remain as
  reference assets. New portrait and company SVGs reuse the original artwork
  and transparency masks; logo variants retain the original outlined mark.
- **Faculty:** page 3 has four rows of four cards. Row 4 is a placeholder copy
  of row 2. Replace `faculty-portrait-13.svg` through `faculty-portrait-16.svg`
  and their `faculty-company-*` logos independently; update the names and roles
  in `index.html`. Portraits, affiliation logos, and names occupy separate rows.
- **Student portraits:** page 6 uses a five-column grid. Three extra slots are
  marked `data-placeholder="true"` and reuse existing portraits until replaced.
  Each portrait has a separate `internship-01.svg` through `internship-12.svg` file.
- **Curriculum cards:** pages 4 and 5 share the foundations / semester-project
  layout; all course lists and project copy remain editable HTML.
- **Fonts:** `fonts.css` loads local WOFF2 files. Fraunces uses `opsz 136`,
  `SOFT 40`, and `WONK 1`; OpenType features match the website.

The cover tagline is intentionally a smaller, single line. Paragraphs wrap
naturally; there is no letter-by-letter positioning or horizontal text stretch.

The scripts in `tools/` were used for the initial PDF migration and verification.
Do not rerun the extraction/build/refinement scripts for normal content edits:
they can replace edited HTML. Edit the HTML and CSS directly instead.
The `build`, `export:print`, and `export:mobile` npm scripts only write output
files and do not overwrite the brochure source.

## Print

Use **Print / PDF** and enable background graphics in your browser if requested.
All eight pages share a 1485 x 2235-point canvas (523.875 x 788.458 mm), the common
interior size in the original PDF. Every redesigned page shares this trim
size, including the cover. Screen and print use
the same page proportions. Print styles hide the viewer and keep one brochure
page per printed sheet, with no margins.

For the print PDF, keep the development server running and run
`npm run export:print`. It writes `output/pdf/nexis-2027-print.pdf`, verifies
all eight page boxes at exactly 1485 x 2235 points, and renders transparent
artwork panels at 300 dpi to prevent browser PDF mask artifacts. HTML text
remains vector text. Generated PDFs stay out of Git.

The optional export tooling requires Playwright, Chrome, Python, and `pypdf`;
it uses this workspace's installed runtimes by default. Set
`PLAYWRIGHT_PACKAGE_PATH`, `CHROME_PATH`, and `PYTHON_PATH` for other runtimes,
or `BROCHURE_URL` to export from another local server. These dependencies are
not required by the deployed flipbook or the static build.

## Mobile sharing PDF

After creating the print master, run `npm run export:mobile`. It writes
`output/pdf/nexis-2027-mobile.pdf`, a fully flattened, eight-page PDF that opens
with one page fitted to the viewer. All page dimensions match the print master.

Pages render at 240 dpi (4950 x 7450 pixels). The exporter selects the highest
JPEG quality between 90 and 98 that keeps the complete PDF within 25 MB,
without resizing pages or subsampling color. It checks the actual file size,
page boxes, pixel dimensions, and image quality before replacing the output.
This sharing compression is lossy; the print master retains the source quality.
Photos, logos, and text are baked into each page, with no editable layers or
searchable text. Keep the vector print master for printing or extreme zoom.

For the larger lossless version, run
`npm run export:mobile -- --compression lossless --max-mb 0`.
That mode requires pixel-identical output at the export resolution.

The optional Python exporter requires `PyMuPDF`, `Pillow`, and `pypdf`. It does
not change the HTML flipbook or its deployment. Generated PDFs and review files
stay out of Git.


Brand assets added from the website repository: boAt, Bombay Shaving Company,
and Snitch. Stable Money uses its official local SVG, sourced from
https://assets.stablemoney.in/web-frontend/v1/stablemoney-black-textlogo.svg.

Perfora and Salty wordmarks are from their official stores:
https://perforacare.com/ and https://salty.co.in/.
Curriculum tool icons use Simple Icons 11.14.0 from
https://github.com/simple-icons/simple-icons/tree/11.14.0/icons.
These tools illustrate the semester projects.
