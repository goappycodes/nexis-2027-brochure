// Export the dedicated edition without replacing the general brochure PDF.
process.env.BROCHURE_EDITION='digital-marketing-commerce';
await import('./export-print.mjs');
