# v4 Epic — Landing, Cover Letter, Multi-Job, PDF Report, Animated Background

Date: 2026-06-18
Status: Approved (animated mesh-gradient background; all four features)

## Goal

Make Resume_Helper look and feel like a polished professional product: a bold
animated mesh-gradient background app-wide, a marketing landing page, and three new
career tools — cover-letter generator, multi-job comparison, and a shareable PDF report.
All analysis stays pure-Python (no external AI).

## Visual: animated mesh-gradient background

- Replace the static radial `body::before` with slowly drifting, blurred gradient
  "blobs" (3–4 layers) that animate position/scale over ~20–30s — premium, alive,
  still professional. Works in both themes via existing vars + `--backdrop-opacity`.
- Respect `prefers-reduced-motion` (freeze animation).
- Keep glassmorphism cards readable on top.

## Features

1. **Animated landing page** (`GET /landing`, public; `/` now redirects here).
   Animated hero headline, subcopy, primary CTA → `/register`, secondary → `/login`,
   a feature showcase grid, all on the new background. No auth.
2. **Cover-letter generator** (`GET/POST /cover-letter`, auth + uploaded resume).
   Pure `analysis.generate_cover_letter(resume_text, role, company) -> str`: pulls the
   candidate name (first plausible line) + top detected skills, fills a professional
   3-paragraph template. Page has role/company inputs, generated letter in an editable
   box, copy + download buttons.
3. **Multi-job comparison** (`GET /compare`, `POST /compare-jobs` JSON, auth).
   Pure `analysis.rank_jobs(resume_text, jobs) -> list` (reuses `match_job_description`),
   returns entries sorted by score with matched/missing. UI: one textarea, jobs split on
   a line of `---`; renders a ranked list, best-fit highlighted.
4. **Shareable PDF report** (dashboard button). Builds a clean print DOM (score, sub-scores,
   sections, skills, timeline, suggestions) and exports via html2pdf.js (already a dep).

## Architecture

- `analysis.py`: add `generate_cover_letter`, `rank_jobs` (pure, unit-tested).
- `app.py`: add routes `/landing`, `/cover-letter` (GET+POST), `/compare`, `/compare-jobs`;
  make `/` → `/landing`; add `/landing` to AuthMiddleware public paths.
- Templates: `landing.html`, `cover_letter.html`, `compare.html` (extend `base.html`);
  dashboard gets nav buttons to the new tools + a "Download report" button.
- `static/css/app.css`: animated mesh background + any shared styles for the new pages.

## Testing (TDD)

`tests/test_analysis.py`: cover-letter contains role/company + a detected skill and is
non-trivial length; empty-resume safe. `rank_jobs` returns sorted-by-score list, best
match first, each with matched/missing; empty jobs → [].

## Out of scope

- AI chat fix (separate plan), real-time collaborative editing, accounts beyond current.
