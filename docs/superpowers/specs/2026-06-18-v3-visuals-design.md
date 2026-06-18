# v3 — Radar Chart, Career Timeline, Theme Toggle — Design Spec

Date: 2026-06-18
Status: Shipped (commit 9a58adf). Backfilled spec.

## Goal

Add net-new visualizations and a cooler/flexible look on top of the existing Aurora
dashboard — without re-editing the existing widgets.

## Features

1. **Sub-score radar chart** — Chart.js radar of the 5 sub-scores (Impact,
   Completeness, Brevity, Clarity, Keywords). Re-renders with theme-correct grid/label
   colors when the theme toggles. Canvas can't read CSS vars, so colors are chosen in JS
   from the current `data-theme`.
2. **Career timeline** — new pure function `analysis.extract_timeline(text)` parses
   dated ranges (`Jan 2020 - Present`, `2017 - 2020`, `06/2016 - 12/2016`), returns
   `[{label, start_year, end_year, end}]` sorted most-recent-first. Ignores single-year
   mentions (requires a start→end range). Rendered as a styled vertical timeline.
3. **Light/dark theme toggle** — floating button in `base.html`, persisted in
   `localStorage`, applied by a pre-paint `<head>` script (no flash). New light palette
   via `:root[data-theme="light"]`. Introduced shared vars (`--track`, `--tile`,
   `--input-bg`, `--chip-accent-text`, `--backdrop-opacity`) so dashboard + editor adapt.

## Testing (TDD)

4 new tests in `tests/test_analysis.py` for `extract_timeline` (ranges, labels,
single-year exclusion, empty); `analyze()` now returns a `timeline` key. 24 tests pass.

## Verification

Live in both themes (screenshots), no console errors; fixed two light-mode contrast
issues found in review (dark textarea, faded accent chips) by moving them to vars.
