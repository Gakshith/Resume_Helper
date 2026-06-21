# Hume AI Redesign — Design Spec

**Date:** 2026-06-21
**Status:** Approved
**Scope:** Visual redesign only. No backend/feature changes, no AI-chat fix, no new features.

## Goal

Transform the ResumeAI frontend from the current dark "Aurora" glassmorphism design
into the **Hume AI "scientific pastel instrument panel"** aesthetic: a light, flat,
shadowless lab canvas where near-black `#222222` ink measures soft pastel data washes,
with a single Iris-violet accent reserved for data and brand moments.

## Decisions (locked)

- **Redesign only** — leave `app.py`, `analysis.py`, `Models.py`, ML, and routes untouched.
- **Light-only** — drop the dark-theme toggle entirely (remove the button + both scripts).
- **All pages** — landing, login, register, home (upload), dashboard, editor, compare, cover_letter.

## Design system (token source: `static/css/app.css`)

Replace the Aurora dark tokens with the Hume system, keeping **legacy variable names
aliased** so per-template inline styles keep working during the refactor.

### Colors
- `--color-ink #222222` (text, filled buttons, icon strokes — never `#000` for these)
- `--color-paper #ffffff` (base canvas, card surfaces)
- `--color-bone #fff9f3` (warm section wash behind white cards)
- `--color-smoke #7a7876` (muted/help text, secondary button text)
- `--color-iris #c094e4` (sole saturated accent — data bars, links, brand)
- `--gradient-iris linear-gradient(90deg,#c094e4 0%,#f7bbe6 50%,#ffb760 100%)` — **hero gradient text only**
- Pastels (surface washes / category dots only, never text or button fills):
  `--color-blush #fce0ee`, `--color-rose-mist #fdebf7`, `--color-meringue #ffe9cf`,
  `--color-mint #daf7ee`, `--color-seafoam #cef1e1`, plus sky `#ccdff1`.

### Legacy aliases (so templates don't break mid-refactor)
- `--bg` → Paper, `--bg-2` → Bone, `--surface`/`--surface-2` → Paper/Bone,
  `--text` → Ink, `--muted` → Smoke, `--faint` → Smoke,
  `--grad` → `--color-iris` (solid violet; gradient reserved for hero text via `.grad`),
  `--cyan`/`--indigo`/`--fuchsia` → Iris, `--track`/`--tile` → Bone/pastel,
  `--shadow` → `none`.

### Typography
- Sans (Fellix substitute): **Inter**, weights 400 + 500 (stand-in for 520), `letter-spacing: -0.025em` across the scale.
- Mono "lab-label" voice (PP Fraktion Mono substitute): **JetBrains Mono**, weight 400,
  uppercase, `letter-spacing: +0.025em`, `font-feature-settings: "calt" 0, "liga" 0`.
- Type scale per reference (caption 10 → display 48) with the specified tracking.

### Shape & elevation
- Radii: inputs 8px, cards 12–16px, big surfaces 24px, **buttons/tags/chips 9999px (pills)**.
- **No drop shadows, no blur, no glow, no mesh backdrop.** Separation by hue + whitespace + at most a 1px hairline border.

### Component classes (in `app.css`)
- `.btn` → pill geometry; `.btn-primary` = Ink fill + Paper text; `.btn-ghost` = transparent, no border, Ink text.
- `.eyebrow` / `.lab-label` → mono, uppercase, +0.025em, Smoke.
- `.card` → Paper surface on Bone section, hairline border, 12–16px radius, no shadow.
- `.tile` → pastel category tile, 16px radius, 12px colored dot + Fellix label.
- `.stat` / `.statrow` → mono stat block row.
- `.grad` → inline gradient-text (hero phrase only).
- Data bars/meters → solid Iris violet on a hairline track.

## base.html changes
- Load Inter (400,500) + JetBrains Mono (400) from Google Fonts; keep Tabler icons.
- **Remove** the floating theme-toggle button and both theme `<script>` blocks.
- **Remove** the dark-default inline script in `<head>`.
- Body canvas = Paper; no `::before/::after` mesh layers.

## Per-page mapping
Each template: strip glassmorphism/glow/shadow; CTAs → pills; eyebrows → mono lab-labels;
cards → flat Paper-on-Bone; pastels as category/status surfaces only; hero phrase gets `.grad`.
- **landing** — Hume hero (gradient phrase, pill CTAs), 3-col feature row (no chrome), Bone footer.
- **login / register** — centered card on Bone, pill submit, mono eyebrow, dot-cluster logo.
- **home (upload)** — section heading block + dropzone (dashed hairline, pastel-wash hover), feature tiles.
- **dashboard** — score gauge + sub-score meters in Iris; section/skills as pastel tiles; JD matcher; radar + timeline recolored.
- **editor** — Quill toolbar + PDF view restyled flat; chat panel restyled (still degrades gracefully).
- **compare** — bar-chart card (Iris bars, mono tabs/labels) on Bone.
- **cover_letter** — section heading + flat card + pill actions.

## Charts (Chart.js, dashboard + compare)
- Radar + bars: single Iris violet data, `#222` labels, hairline grid, **no glow/shadow**.
- Gauge + meters: Iris fill on a hairline track.

## Out of scope
Backend, routes, ML, AI chat fix, new features, dark mode, copy rewrites.

## Verification
Pure CSS/markup — no logic, so no unit tests apply. Evidence = **Preview MCP**:
run the app (`resume-helper` launch config, :8000), screenshot every redesigned page,
confirm zero new console errors, check mobile width via `preview_resize`.
