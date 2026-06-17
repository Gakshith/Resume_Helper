# Project: Resume Helper (repo: Resume_Helper)

An AI-powered **resume analysis & career-consultant** web app. Users register/login, upload a
PDF resume, and the app extracts the text, classifies it into one of ~24 job categories with a
trained scikit-learn model, and offers an AI chat consultant (LangChain + HuggingFace) for
resume/career advice. Server-rendered with Jinja2 templates.

**Source of truth for product detail:** `README.md` (features, endpoints, setup). Known issues
and fixes are tracked in `BUGS.md`. Don't duplicate those here — link to them.

---

## MANDATORY: use the skills

This repo lives in a Superpowers-enabled workspace. Shared skills are at
`../../../../.claude/skills/` (index: `../../../../.claude/skills/SUPERPOWERS.md`).

Before responding to or acting on any task, check whether a skill applies and use it. Even a
1% chance → read it. Process skills (brainstorming, systematic-debugging) come first, before
clarifying questions or code exploration. Read skills from
`../../../../.claude/skills/<name>/SKILL.md` and follow them exactly.

## Default workflow

brainstorming → using-git-worktrees → writing-plans →
subagent-driven-development / executing-plans → test-driven-development →
requesting-code-review / receiving-code-review → verification-before-completion →
finishing-a-development-branch.

Project knowledge lives in `docs/superpowers/` (specs = what we build, plans = how).

## Tech stack

- **Backend:** FastAPI + Uvicorn, Starlette, python-multipart; Pydantic models in `Models.py`.
- **Frontend:** Jinja2 server-rendered templates in `templates/`, static assets in `static/`.
- **ML / NLP:** scikit-learn (model file `resume_classification_model1.pkl`), pandas, numpy, NLTK.
- **AI chat:** LangChain (`langchain-core`, `langchain-huggingface`) → HuggingFace inference.
- **PDF:** pypdf. **Config:** python-dotenv.
- **Auth/data:** session cookies; users stored in `Login_Db.json` (auto-generated, gitignored).

## Commands

```bash
# from this repo root: projects/Resume_Helper/Git/Resume_Helper/
python3 -m venv .venv && source .venv/bin/activate   # first time
pip install -r requirements.txt                       # install deps
uvicorn app:app --reload                               # run -> http://localhost:8000
# NLTK data (first run, if needed):
python -c "import nltk; nltk.download('punkt'); nltk.download('punkt_tab'); nltk.download('stopwords'); nltk.download('wordnet')"
```

Requires `HUGGINGFACE_API_TOKEN` in a local `.env` (see `.env.example`). The model file
`resume_classification_model1.pkl` must be present in this repo root.

> No automated test suite exists yet. When adding tests (TDD), prefer `pytest`; start with the
> resume-classification and PDF-extraction logic, and add `pytest` to `requirements.txt`.

## Conventions & guardrails

- Specs → `docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md`; Plans → `docs/superpowers/plans/`.
- Worktrees → `.worktrees/`.
- Never commit `.env`, `Login_Db.json`, uploaded files, or the `.venv`.
- **Security debt (from README):** passwords are currently stored in plain text — do not build
  on that; if touching auth, switch to proper hashing (e.g. passlib/bcrypt) first.
- Keep ML/classification and PDF logic in functions separate from request handlers in `app.py`.

## First step

Run **brainstorming** to scope the next feature or fix (start from `BUGS.md` or a README gap),
write a spec into `docs/superpowers/specs/`, then a plan, then implement test-first.
