# Brochure editing instructions

- Treat `index.html` and `brochure.css` as the source for future edits.
- Keep all eight pages unless the user requests a change.
- Use Fraunces at weight 400 for headings. Preserve the website settings:
  `"opsz" 136, "SOFT" 40, "WONK" 1` and `"kern", "liga", "ss01"`.
- Use Poppins 400 for paragraphs, 500 for captions, and 600 for labels.
  Keep normal letter spacing in sentences and the shared line-height rules.
- Keep complete words and paragraphs in semantic HTML. Do not split words into
  separately positioned spans, stretch text horizontally, or invent manual gaps.
- Use the shared 120-unit text gutters. Preserve the underlying photos and logos.
- The cover tagline "Where You Graduate With Experience" must fit on one line.
- `brochure.pdf` is the original layout reference. Its type weights, tracking,
  and spacing have been superseded by the cleaned website typography.
- Extraction and migration scripts in `tools/` overwrite generated source.
  Do not run them during ordinary edits. Edit the HTML/CSS directly.
- `npm run dev` serves the project at port 4173 without installing dependencies.
- Visually inspect affected pages after layout changes, and check for clipping,
  overlapping copy, and text outside cards.


- Faculty uses four columns and four rows with compact gaps. The fourth row
  intentionally clones the second row until replacement portraits are supplied.

- Programmes 01, 02, and 03 use the shared foundations / semester project card
  design. Do not restore their old individually positioned curriculum copy.
- Three additional student slots intentionally reuse existing portraits and are
  marked `data-placeholder="true"` for future replacement.
- Faculty names use Poppins 700 and sit below the logos without overlap.
- Keep only the Flipbook view: two pages per view on desktop and one on mobile.
  Use subtle side arrows and preserve native mobile pinch-to-zoom. Keep all
  copy in the same semantic HTML and preserve the eight-page print layout.
- `npm run build` creates static Vercel output in `dist/`. Keep generated output
  and temporary verification files out of Git.
- After completing brochure changes, commit and push directly to `main` on
  `origin` (`https://github.com/goappycodes/nexis-2027-brochure`). The user has
  authorized these routine pushes; do not ask for confirmation again.
