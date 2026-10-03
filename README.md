# NEXIS 2027 brochure

An editable, eight-page HTML brochure. The Figma PDF supplies the artwork and
layout reference; typography uses the exact Fraunces and Poppins font files
from the website's `/ug/2027` page.

## Open the brochure

Run `npm run dev`, then open <http://127.0.0.1:4173>.
There is no installation or build step. The viewer includes page navigation,
zoom, and Print / PDF. All assets and fonts are local.

Desktop shows two pages per view; phones show one. Subtle side arrows, a page
picker, and arrow keys turn pages. Phones support horizontal swipes and native
pinch-to-zoom. The viewer keeps the brochure's original layout on every device.
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
- **Positioning:** `.placed` blocks use `--x`, `--y`, and `--w` on a 1485-unit
  canvas. The shared text margin is 120 units. Move blocks as a whole.
- **Artwork:** `assets/artwork/page-01.svg` through `page-08.svg` retain the
  photos, brand logos, gradients, and decorative graphics. Their image files
  live in `assets/images/`. Admission cards and the contact section use HTML/CSS.
- **Faculty:** page 3 has four rows of four cards. Row 4 is a placeholder copy
  of row 2. Its separate `faculty-13.svg` through `faculty-16.svg` artwork files
  can be replaced independently; update the names and roles in `index.html`.
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

## Print

Use **Print / PDF** and enable background graphics in your browser if requested.
All eight pages share a 1485 x 2235-point canvas (523.875 x 788.458 mm), the common
interior size in the original PDF. The original cover was 40.5 points taller;
its footer has been brought up to the common trim size. Screen and print use
the same page proportions. Print styles hide the viewer and keep one brochure
page per printed sheet, with no margins.


Brand assets added from the website repository: boAt, Bombay Shaving Company,
and Snitch. Stable Money uses its official local SVG, sourced from
https://assets.stablemoney.in/web-frontend/v1/stablemoney-black-textlogo.svg.

Perfora and Salty wordmarks are from their official stores:
https://perforacare.com/ and https://salty.co.in/.
Curriculum tool icons use Simple Icons 11.14.0 from
https://github.com/simple-icons/simple-icons/tree/11.14.0/icons.
These tools illustrate the semester projects.
