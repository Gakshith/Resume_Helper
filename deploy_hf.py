"""One-shot deploy to Hugging Face Spaces (Docker SDK).

Usage:
    pip install huggingface_hub          # already in requirements
    huggingface-cli login                # paste a HF token with WRITE scope
    python deploy_hf.py                   # creates the Space and uploads everything

The token is read from your local HF login cache — it never appears in this file or
in chat. huggingface_hub uploads the 27 MB model with Git LFS automatically, so there
is no manual LFS step.
"""
import sys
from huggingface_hub import HfApi, whoami

SPACE_NAME = "Resume_Helper"

# Files/dirs that must NOT be uploaded (secrets, local junk, large dev-only data).
IGNORE = [
    ".git*", ".git/*",
    "*.env", ".env", ".env.*",
    ".venv/*", "venv/*",
    "uploads/*",            # private uploaded resumes
    "Login_Db.json",        # local user store
    "__pycache__/*", "*.pyc", "*.pyo",
    ".pytest_cache/*", ".coverage", "htmlcov/*",
    ".idea/*", ".vscode/*",
    ".claude/*", ".claude-flow/*", "ruvector.db",
    ".worktrees/*",
    "deploy_hf.py", "DEPLOY-HF.md",
]


def main() -> int:
    try:
        me = whoami()
        user = me["name"]
        role = me.get("auth", {}).get("accessToken", {}).get("role")
    except Exception as e:  # not logged in / bad token
        print("Not logged in. Run:  huggingface-cli login   (use a token with WRITE scope)")
        print(f"  detail: {e}")
        return 1

    if role and role != "write":
        print(f"Your token role is '{role}'. A WRITE token is required.")
        print("Create one at https://huggingface.co/settings/tokens then re-run huggingface-cli login.")
        return 1

    repo_id = f"{user}/{SPACE_NAME}"
    api = HfApi()

    print(f"Creating Space {repo_id} (Docker, public) ...")
    api.create_repo(
        repo_id=repo_id,
        repo_type="space",
        space_sdk="docker",
        private=False,
        exist_ok=True,
    )

    print("Uploading project files (model uploads via LFS automatically) ...")
    api.upload_folder(
        folder_path=".",
        repo_id=repo_id,
        repo_type="space",
        ignore_patterns=IGNORE,
        commit_message="Deploy Resume_Helper",
    )

    print("\nDone. Your Space is building here:")
    print(f"  https://huggingface.co/spaces/{repo_id}")
    print("Open the Logs tab to watch the Docker build; the app goes live when it finishes.")
    print("(Optional) To enable the AI chat, add a Space secret HUGGINGFACE_API_TOKEN in Settings.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
