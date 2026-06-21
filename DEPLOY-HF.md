# Deploying Resume_Helper to Hugging Face Spaces

This app is a **FastAPI server** (it runs Python + a 27 MB ML model), so it cannot run on
GitHub Pages — Pages only serves static files. Hugging Face **Spaces** (Docker SDK) runs the
real backend and gives you a public URL anyone can visit.

Everything the Space needs is already in this repo:
- `Dockerfile` — builds the app, pre-downloads NLTK data, serves on port **7860**.
- `README.md` frontmatter — tells HF to use the Docker SDK on port 7860.
- `.dockerignore` — keeps secrets and dev junk out of the image.

## One-time prerequisites
- A free Hugging Face account: https://huggingface.co/join
- `git-lfs` installed locally (the model file is 27 MB and HF requires LFS for files > 10 MB):
  - macOS: `brew install git-lfs`

## Step 1 — Create the Space
1. Go to https://huggingface.co/new-space
2. **Owner**: your account · **Space name**: `Resume_Helper`
3. **SDK**: **Docker** (blank template) · **Hardware**: CPU basic (free)
4. **Visibility**: **Public**  ← this is what makes it accessible to everyone
5. Click **Create Space**. Note the URL: `https://huggingface.co/spaces/<YOUR_HF_USERNAME>/Resume_Helper`

## Step 2 — (Optional) add the AI-chat token
The app runs fully without this; only the AI chat panel needs it (and that feature has a
separate known bug). To set it: open the Space → **Settings** → **Variables and secrets** →
**New secret** → name `HUGGINGFACE_API_TOKEN`, value = your HF token.

## Step 3 — Push the code to the Space
Run these in a **fresh, throwaway clone** (Step 3a rewrites git history to move the model into
LFS — don't do it in your main working copy):

```bash
git clone https://github.com/Gakshith/Resume_Helper.git hf-deploy
cd hf-deploy

# 3a. Move the 27 MB model into Git LFS (required by Hugging Face)
git lfs install
git lfs track "*.pkl"
git add .gitattributes
git lfs migrate import --include="*.pkl" --include-ref=refs/heads/main

# 3b. Point at your Space and push
git remote add space https://huggingface.co/spaces/<YOUR_HF_USERNAME>/Resume_Helper
git push space main
```

When prompted for a password, paste a **Hugging Face access token with write scope**
(create one at https://huggingface.co/settings/tokens). Username = your HF username.

## Step 4 — Watch it build
On the Space page, open the **Logs** tab. The Docker image builds (a few minutes the first
time), then you'll see `Application startup complete` and `ML model loaded and health check
passed`. Your public app is live at:

```
https://huggingface.co/spaces/<YOUR_HF_USERNAME>/Resume_Helper
```

## Test login
The user store (`Login_Db.json`) is **not** deployed (it's gitignored), so the Space starts
with an empty database — just click **Get started** and register a new account.

## ⚠️ Before sharing widely (security notes)
This is fine as a public demo, but it is not hardened for untrusted traffic:
- Anyone can register (no email verification / abuse limits).
- SSL certificate verification is globally disabled in `app.py`.
- Sessions are in-memory (everyone is logged out whenever the Space restarts).
- No CSRF protection or rate limiting.

Harden these (see `Plans/ROADMAP.md` backlog) before treating it as a production service.
