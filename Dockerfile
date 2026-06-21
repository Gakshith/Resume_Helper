FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HOME=/home/user \
    NLTK_DATA=/home/user/nltk_data \
    MODEL_PATH=resume_classification_model1.pkl

# Hugging Face Spaces runs containers as a non-root user with UID 1000.
RUN useradd -m -u 1000 user
USER user
WORKDIR /home/user/app
ENV PATH="/home/user/.local/bin:$PATH"

COPY --chown=user requirements.txt .
RUN pip install --user -r requirements.txt

# Pre-download NLTK corpora at build time so the app starts instantly.
RUN python -m nltk.downloader -d $NLTK_DATA punkt stopwords wordnet \
    && (python -m nltk.downloader -d $NLTK_DATA punkt_tab || true)

COPY --chown=user . .

# HF Spaces expects the app on port 7860 (see app_port in README frontmatter).
EXPOSE 7860
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
