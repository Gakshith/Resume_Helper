# Resume Intelligence Dashboard — Design Spec

Date: 2026-06-17
Status: Approved (theme: Aurora dark; scope: full dashboard)

## Goal

Transform the post-upload experience from a bare PDF+chat view into a **Resume
Intelligence Dashboard** with rich, accurate, server-computed analysis and a fresh,
premium "Aurora" dark visual identity. No external AI is required for any analysis
feature (the LLM chat remains optional and degrades gracefully).

## Visual identity — "Aurora" (dark)

- Background: deep ink-navy `#070b16` with subtle aurora radial glows.
- Surfaces: glassmorphism cards (`rgba` + backdrop blur, hairline borders).
- Accent flow: indigo `#6366f1` → cyan `#22d3ee` → fuchsia `#d946ef`.
- Typography: Inter. Animated counters, meters, and rings.
- Shared design system in `static/css/app.css`; pages extend `templates/base.html`
  (removes ~250 lines of duplicated CSS per template).

## New features (all pure-Python, in `analysis.py`)

1. **Overall Resume Score (0–100)** — weighted composite of the sub-scores below.
2. **Sub-scores** — Impact, Completeness, Brevity, Clarity, Keyword strength (0–100 each).
3. **Section detection** — Summary, Experience, Education, Skills, Projects,
   Certifications → present/missing.
4. **Skills extraction** — curated keyword dictionary grouped into Languages,
   Frameworks, Tools, Data/ML, Soft skills.
5. **Resume stats** — word count, reading time, bullet count, action-verb count,
   quantified-achievement count, avg words/bullet.
6. **Job-Description Matcher** — paste a JD → TF-IDF cosine match % + matched/missing
   keywords. Endpoint `POST /match-jd`.
7. **Smart suggestions** — rule-based, actionable tips derived from the metrics.
8. **Kept & restyled** — top-3 role prediction + confidence ring, Quill editor,
   Export PDF, original PDF viewer.

## Architecture

- `analysis.py` — pure functions, no FastAPI/IO. Each independently unit-testable:
  - `compute_stats(text) -> dict`
  - `detect_sections(text) -> dict[str, bool]`
  - `extract_skills(text) -> dict[str, list[str]]`
  - `readability(text) -> float`  (Flesch reading ease)
  - `resume_score(text) -> dict`  (overall + subscores)
  - `suggestions(text) -> list[str]`
  - `match_job_description(resume_text, jd_text) -> dict` (score, matched, missing)
  - `analyze(text) -> dict`  (one call returning everything for the template)
- `app.py` — thin handlers:
  - `POST /upload-pdf` → save, extract, classify, `analyze()`, store per-session, render `dashboard.html`.
  - `GET /editor` → render Quill editor + PDF view from stored session data.
  - `POST /match-jd` → JSON `{score, matched, missing}` from stored resume text + posted JD.
  - Per-session store `analysis_store[token] = {text, pdf_url, filename, prediction, confidence, top_roles, analysis}`.
- Templates: `base.html`, `login.html`, `register.html`, `home.html`, `dashboard.html`, `editor.html`.

## Testing (TDD)

`pytest` suite `tests/test_analysis.py` covering every pure function with known inputs:
sections detected/missed, skills found, stats counts, score bounds [0,100], JD match
overlap, suggestions firing on weak resumes. Written test-first (RED → GREEN).

## Out of scope

- Fixing the langchain/Python-3.12 chat incompatibility (separate task); chat stays
  gracefully degraded.
- Real PDF.js rendering (keep iframe; headless preview can't show it but real browsers can).
- Auth/password hashing changes (tracked separately as security debt).
