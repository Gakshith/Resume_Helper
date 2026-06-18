# CLAUDE.md

## ⚡ START HERE — current state & where knowledge lives (read first)

**New session? Read these to understand the project before doing anything:**
1. `../../../Plans/ROADMAP.md` (container) — status, backlog, constraints. **Single source of truth for what's done & next.**
2. `docs/superpowers/specs/` — design specs (dashboard, security, v3 visuals).
3. `docs/superpowers/plans/` — implementation plans (e.g. the pending AI-chat fix).
4. Ruflo semantic memory — `memory_search` in namespace `resume_helper` for cross-session context.

**Current state (2026-06-18):** main has v1→v3. The app is a **Resume Intelligence
Dashboard** (Aurora dark + light theme toggle): resume score gauge + 5 sub-scores,
section detection, skills chips, JD matcher, suggestions, top-3 role prediction,
**radar chart**, **career timeline**, Quill editor + AI chat. Security is hardened
(bcrypt password hashing+migration, upload size/magic-byte checks, per-user PDF authz).
`analysis.py` holds the pure logic (24 pytest tests in `tests/`).
**Known remaining bug:** the `/chat` AI consultant — langchain-core 0.1.52 is
incompatible with Python 3.12 and it needs `HUGGINGFACE_API_TOKEN` (plan written).

**Process discipline:** for every task write the spec + plan BEFORE coding, update
`Plans/ROADMAP.md`, put deliverables in `Artifacts/`, persist context to Ruflo memory.

## Project Overview

Resume_Helper is a FastAPI web app for resume upload, ML classification, a rich
analysis dashboard, inline editing, and an (currently broken) AI career-consultant
chat. Users register/login, upload a PDF, the backend extracts text with `pypdf`,
predicts a job category with a pickled scikit-learn model, computes a full analysis
report (`analysis.py`), and renders `dashboard.html`; `editor.html` provides a Quill
editor + PDF view + chat. Templates extend `base.html` and share `static/css/app.css`.

## Tech Stack

- Backend: FastAPI, Starlette middleware, Jinja2 templates
- Validation: Pydantic
- PDF processing: `pypdf`
- ML/NLP: scikit-learn, pandas, numpy, NLTK, pickle
- AI chat: `langchain-huggingface`, `langchain-core`, HuggingFace endpoint
- Frontend: server-rendered HTML templates, embedded CSS/JS, Quill, html2pdf.js
- Persistence: local JSON file for users, in-memory dictionaries for sessions/chat state

## Repository Structure

- `app.py`: main FastAPI app, auth, upload flow, ML prediction, chat endpoint
- `Models.py`: Pydantic models for login/register/chat requests
- `templates/login.html`: sign-in page
- `templates/register.html`: account creation page
- `templates/home.html`: authenticated upload page
- `templates/result.html`: PDF viewer, resume editor, export button, chat UI
- `requirements.txt`: Python dependencies
- `.env.example`: expected environment variables
- `uploads/`: runtime PDF upload directory, only `.gitkeep` is tracked
- `resume_classification_model1.pkl`: tracked classifier artifact in this checkout
- `.gitignore`: ignores `.env`, `.venv`, uploads, `Login_Db.json`, caches, logs

## How To Run

1. Create/activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create `.env` from `.env.example` and set:

```bash
HUGGINGFACE_API_TOKEN=your_token_here
```

4. Ensure required runtime directories/files exist:

```bash
mkdir -p uploads static templates
```

5. Start the app:

```bash
uvicorn app:app --reload
```

The default URL is `http://localhost:8000`.

## Common Development Commands

```bash
.venv/bin/python -m py_compile app.py Models.py
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app:app --reload
```

Tests: `tests/test_analysis.py` (24 pytest tests over the pure logic in `analysis.py`).
Run with `.venv/bin/python -m pytest tests/ -q`. NOTE: several "Known Issues" listed
further below are now FIXED (static/ exists, model loads via startup, passwords are
hashed, result.html replaced by dashboard.html/editor.html) — trust the "START HERE"
block at the top for current state.

## Architecture

Request flow:

1. `AuthMiddleware` allows public paths and redirects protected paths to `/login` when no valid `session_token` cookie maps to an in-memory session.
2. `/register` validates form data with `Register`, stores plain user records in `Login_Db.json`, and redirects to login.
3. `/login` checks `Login_Db.json`, creates a random session token in memory, and sets an HTTP-only cookie.
4. `/home` renders the upload page for authenticated users.
5. `/upload-pdf` saves the PDF into `uploads/`, extracts text page by page, loads the classifier, predicts a category ID, maps it to a sorted category list, stores extracted text in `chat_context`, and renders `templates/result.html`.
6. `/chat` requires a logged-in session and uploaded resume context, then sends the resume plus user messages to the HuggingFace chat model through LangChain.

Global mutable state in `app.py`:

- `users_db`: loaded from `Login_Db.json`
- `sessions`: maps session token to username
- `chat_context`: maps session token to extracted resume text
- `user_chat_histories`: maps session token to LangChain message history
- `ml_components`: populated at startup but currently not used by `/upload-pdf`

## Data Model

`Login_Db.json` is generated at runtime and stores records like:

```json
[
  {
    "UserName": "alice",
    "Password": "plain-text-password"
  }
]
```

Uploaded files are written to `uploads/{token_hex}_{original_filename}` and served through `/uploads`.

## API Endpoints

- `GET /`: redirects to `/login`
- `GET /register`: registration page
- `POST /register`: creates a user
- `GET /login`: login page
- `POST /login`: creates a session
- `GET /home`: authenticated upload page
- `GET /logout`: removes session and cookie
- `POST /upload-pdf`: authenticated PDF upload, extraction, classification, result render
- `POST /chat`: JSON chat endpoint, expects `{"message": "..."}`

## Environment Variables

- `HUGGINGFACE_API_TOKEN`: HuggingFace API token used by `HuggingFaceEndpoint`.

The app loads `.env` with `python-dotenv`.

## Known Issues / Uncertainties

- Dependencies are not installed in the current `.venv`; `.venv/bin/pip list` only shows `pip`.
- `static/` is missing, but `app.py` mounts it with `StaticFiles(directory="static")`; importing/running the app will fail after dependencies are installed unless this directory exists.
- Model filenames are inconsistent:
  - README says `resume_classification_model1.pkl`
  - repository contains `resume_classification_model1.pkl`
  - `MODEL_PATH` is `resume_pipeline (1).pkl`
  - `/upload-pdf` hardcodes `/Users/gojuruakshith/Resume_generator/resume_classification_model1.pkl`
- The startup model loader fills `ml_components`, but the upload route ignores it and reloads a hardcoded model path on every upload.
- Passwords are stored in plain text. Use password hashing before any real deployment.
- Sessions, chat context, and chat history are process-local memory. They disappear on restart and will not work across multiple workers.
- `/chat` is listed as public in middleware, but the endpoint itself checks session validity.
- `HTTPException`, `Depends`, `Login`, `sys`, and some duplicate imports appear unused.
- Category mapping sorts category names alphabetically before indexing; confirm this matches the model's training label order before relying on predictions.
- The result template inserts extracted resume text into hidden HTML and chat responses with `innerHTML`; review escaping/XSS behavior before accepting untrusted content.
- NLTK data downloads happen at import time, which can slow startup or fail in locked-down environments.

## Security Notes

- Do not commit `.env`, `Login_Db.json`, or uploaded resumes.
- Add password hashing, CSRF protection for form posts, upload size limits, MIME/content validation, and rate limiting before production use.
- Avoid hardcoded absolute paths and user-specific directories.
- Consider limiting HuggingFace prompt size because full resume text is inserted into the system prompt.

## Quick Start For Future Agents

1. Read `app.py` first; almost all behavior lives there.
2. Check `git status --short` before editing; `.claude/` may be untracked.
3. Fix runtime blockers before feature work: install dependencies, create `static/`, and normalize the model path.
4. Prefer small, targeted changes because the app currently has no automated tests.
5. Use `.venv/bin/python`, not `python`; this shell does not provide a `python` alias.
