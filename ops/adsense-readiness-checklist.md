# MALT Tech Blog AdSense Readiness Checklist

Last updated: 2026-07-17

## Current review status

- [x] AdSense returned a second `low value content` rejection on 2026-07-17
- [x] Reclassified paper-only lab reviews as review notes and applied `noindex,follow`
- [x] Disabled scheduled weekly review-note publication; workflow is manual-only
- [x] Published the first code-and-data-backed MALT experiment with 1,200 simulations
- [x] Added reproducibility signals to the content quality gate
- [x] Rebuilt the sitemap from indexable pages so noindex posts are excluded automatically
- [x] Publish at least two more code/data-backed experiments or field-oriented original guides
- [ ] Confirm the new experiment and refreshed hubs are crawled in Search Console
- [ ] Do not request another AdSense review before 2026-07-31 unless crawling completes and the two original assets above are already live

## 1. Public trust pages

- [x] About page exists
- [x] Contact page exists
- [x] Privacy policy exists
- [x] Editorial standards / AI disclosure page exists
- [x] Contact route should remain monitored and visible

## 2. Search and indexing

- [x] `robots.txt` exists
- [x] `sitemap.xml` exists
- [x] Google site verification file exists
- [x] `ads.txt` exists
- [x] Google Search Console weekly checklist exists (`ops/search-console-weekly-checklist.md`)
- [ ] Google Search Console performance should be checked weekly after re-review

## 3. Content quality before applying

- [x] Prioritize evergreen guides and strong railway/PHM analysis on home and archive pages
- [x] Increase ratio of deep-dive / problem-solving posts versus short summaries
- [x] For each auto-published paper post, keep these sections:
  - why this matters now
  - who should read this
  - operational checklist
  - limitations
- [x] Reduce pages that look like thin summaries or duplicate archive material
- [x] Temporarily remove low-value or off-topic posts from hubs and apply `noindex,follow`

## 4. Monetization safety checks

- [x] Keep AI involvement openly disclosed
- [x] Avoid fake author personas or hidden automation claims
- [x] Avoid excessive ad density on first screen
- [x] Keep navigation, archive, and policy pages easy to find

## 5. Re-review gate after low-value-content rejection

- [x] Home page starts with pillar guides before daily posts
- [x] Posts page starts with evergreen guides and curated recent analysis
- [x] `content_quality_report.json` reports zero thin/weak candidates
- [x] `sitemap.xml` points to curated canonical pages, not legacy `/MALT-tech-blog/` paths
- [x] `robots.txt` blocks generated artifacts and internal ops/archive folders
- [x] Confirm the deployed GitHub Pages version contains this cleanup
- [ ] Wait for Search Console recrawl and a material original-content expansion before requesting AdSense review

## 6. Recommended next build steps

1. Add two more reproducible experiments with code, raw/summary data, charts, and explicit limitations.
2. Check Search Console indexing for the lab post, LAB hub, and flagship guides.
3. Keep paper-summary automation conservative and keep review-only lab generation manual.
4. Request review only after the 2026-07-31 readiness gate passes.
