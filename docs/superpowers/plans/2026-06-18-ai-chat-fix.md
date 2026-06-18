# Implementation Plan — Fix the AI Career-Consultant Chat

Date: 2026-06-18
Status: PLANNED (not yet started)
Related: `Plans/ROADMAP.md` item 1.

## Problem

The `/chat` endpoint is dead. At startup the logs show:
`Failed to import chat dependencies: ForwardRef._evaluate() missing 1 required
keyword-only argument: 'recursive_guard'`. This is the known incompatibility between
old `langchain-core` (0.1.52) / its pydantic usage and Python 3.12.4+. Separately,
chat needs a `HUGGINGFACE_API_TOKEN` to actually call the model.

## Goal

Chat initializes cleanly on Python 3.12 and works when a token is present; degrades
with a clear message when the token is absent — no startup tracebacks.

## Tasks (bite-sized, verify after each)

1. **Reproduce & pin the cause.** Confirm the import error in a clean `.venv/bin/python -c`
   import of the langchain symbols. Record the failing versions.
2. **Find a compatible version set.** Bump `langchain-core` + `langchain-huggingface`
   to versions that support Python 3.12 (and adjust the import paths if the API moved,
   e.g. `HuggingFaceEndpoint` / `ChatHuggingFace` locations). Update `requirements.txt`.
   Verify: `python -c "import langchain_huggingface"` succeeds.
3. **Adapt `app.py` chat init** to the new API surface; keep the existing graceful
   fallbacks (`chat_model = None` path) intact.
4. **Token-absent UX.** When `HUGGINGFACE_API_TOKEN` is unset, `/chat` returns a clear
   "chat unavailable — set a token" reply instead of erroring; no traceback at startup.
5. **Test.** Add a small test that importing the chat module / init path does not raise
   on Python 3.12 (monkeypatch token absent). Keep the 24 analysis tests green.
6. **Verify live.** Start server, confirm no `Failed to import chat dependencies` in
   logs; with a dummy/real token, send a message in the editor chat and confirm a reply
   (or the graceful message without a token).
7. **Finish.** Commit on a branch `fix/ai-chat`, update `Plans/ROADMAP.md`, merge.

## Risks

- Upgrading langchain may cascade into other API changes — keep the change minimal and
  pinned; if it pulls heavy deps, prefer the smallest compatible bump.
- No token in this environment → final end-to-end "real reply" check may need the user
  to supply `HUGGINGFACE_API_TOKEN`; the token-absent path is fully testable without it.
