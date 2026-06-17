"""Pure-Python resume analysis.

No FastAPI, no I/O, no external API calls — every function takes text and returns
plain data, so it is fully unit-testable. Used by the upload flow to build the
Resume Intelligence Dashboard.
"""
from __future__ import annotations

import re
from typing import Dict, List

# --- Vocabularies -----------------------------------------------------------

ACTION_VERBS = {
    "led", "built", "designed", "developed", "created", "implemented", "launched",
    "increased", "reduced", "improved", "managed", "architected", "spearheaded",
    "delivered", "optimized", "automated", "engineered", "drove", "established",
    "scaled", "streamlined", "accelerated", "achieved", "generated", "grew",
    "produced", "shipped", "owned", "mentored", "coordinated", "analyzed",
    "deployed", "integrated", "migrated", "refactored", "resolved", "boosted",
    "transformed", "initiated", "executed", "facilitated", "negotiated",
    "secured", "trained", "championed", "pioneered",
}

WEAK_VERBS = {
    "worked", "responsible", "helped", "did", "made", "handled", "assisted",
    "involved", "participated", "tasked",
}

SECTION_KEYWORDS = {
    "summary": ["summary", "objective", "profile", "about me"],
    "experience": ["experience", "employment", "work history"],
    "education": ["education", "academic"],
    "skills": ["skills", "competencies", "technologies", "technical skills"],
    "projects": ["projects", "portfolio"],
    "certifications": ["certification", "certifications", "licenses", "certificates"],
}

SKILL_DICT: Dict[str, List[str]] = {
    "Languages": ["python", "java", "javascript", "typescript", "c++", "c#", "go",
                  "golang", "rust", "ruby", "php", "swift", "kotlin", "scala", "sql"],
    "Frameworks": ["react", "angular", "vue", "next.js", "node.js", "django",
                   "flask", "fastapi", "spring", "express", "rails", "laravel",
                   ".net", "svelte", "tensorflow", "pytorch", "keras"],
    "Tools": ["docker", "kubernetes", "git", "jenkins", "terraform", "ansible",
              "aws", "azure", "gcp", "linux", "jira", "figma", "postman", "kafka", "nginx"],
    "Data/ML": ["pandas", "numpy", "scikit-learn", "sklearn", "spark", "hadoop",
                "tableau", "power bi", "machine learning", "deep learning", "nlp",
                "data analysis", "postgresql", "mysql", "mongodb", "redis"],
    "Soft skills": ["leadership", "communication", "teamwork", "collaboration",
                    "problem solving", "mentoring", "agile", "scrum", "stakeholder"],
}

_STOPWORDS = {
    "the", "and", "for", "with", "you", "are", "our", "your", "will", "have", "has",
    "this", "that", "from", "must", "should", "able", "who", "all", "any", "can",
    "into", "out", "not", "but", "their", "they", "them", "his", "her", "its", "was",
    "were", "been", "being", "a", "an", "to", "of", "in", "on", "as", "at", "by", "is",
    "or", "be", "we", "us", "it", "if", "do", "up", "so", "knowledge", "experience",
    "seeking", "looking", "role", "team", "work", "working", "years", "year", "strong",
    "good", "great", "plus", "etc", "including", "include", "ability", "skills", "skill",
    "skilled", "know", "familiar", "proficient", "preferred", "required", "nice",
    "using", "use", "such", "via", "across", "within", "well", "like", "may", "also",
}

_BULLET_PREFIXES = ("-", "•", "*", "‣", "·", "●", "▪", "◦", "–", "—")


# --- Helpers ----------------------------------------------------------------

def _tokens(text: str) -> List[str]:
    return re.findall(r"[a-zA-Z][a-zA-Z0-9.+#-]*", (text or "").lower())


def _word_present(skill: str, text_lower: str) -> bool:
    pattern = r"(?<![a-z0-9.+#])" + re.escape(skill) + r"(?![a-z0-9.+#])"
    return re.search(pattern, text_lower) is not None


def _bullets(text: str) -> List[str]:
    out = []
    for line in (text or "").splitlines():
        s = line.strip()
        if s and s.startswith(_BULLET_PREFIXES):
            out.append(s)
    return out


def _count_syllables(word: str) -> int:
    word = re.sub(r"[^a-z]", "", word.lower())
    if not word:
        return 0
    groups = re.findall(r"[aeiouy]+", word)
    count = len(groups)
    if word.endswith("e") and count > 1:
        count -= 1
    return max(1, count)


def _clamp(value: float, lo: float = 0, hi: float = 100) -> int:
    return int(max(lo, min(hi, round(value))))


# --- Public API -------------------------------------------------------------

def detect_sections(text: str) -> Dict[str, bool]:
    """Return which standard resume sections are present."""
    low = (text or "").lower()
    result = {}
    for section, keywords in SECTION_KEYWORDS.items():
        result[section] = any(kw in low for kw in keywords)
    return result


def extract_skills(text: str) -> Dict[str, List[str]]:
    """Return detected skills grouped by category (only non-empty groups)."""
    low = (text or "").lower()
    found: Dict[str, List[str]] = {}
    for category, skills in SKILL_DICT.items():
        hits = [s for s in skills if _word_present(s, low)]
        if hits:
            found[category] = sorted(set(hits))
    return found


def compute_stats(text: str) -> Dict[str, float]:
    """Word/bullet counts and impact signals."""
    words = _tokens(text)
    word_count = len(words)
    bullets = _bullets(text)
    units = bullets if bullets else re.split(r"(?<=[.!?])\s+", (text or "").strip())
    units = [u for u in units if u.strip()]
    quantified = sum(1 for u in units if re.search(r"\d|%|\$", u))
    word_set = words  # already lowercased
    action_verb_count = sum(1 for w in word_set if w in ACTION_VERBS)
    weak_verb_count = sum(1 for w in word_set if w in WEAK_VERBS)
    avg_words_per_bullet = round(
        sum(len(_tokens(b)) for b in bullets) / len(bullets), 1
    ) if bullets else 0.0
    return {
        "word_count": word_count,
        "reading_time_min": max(1, round(word_count / 200)),
        "bullet_count": len(bullets),
        "quantified_count": quantified,
        "action_verb_count": action_verb_count,
        "weak_verb_count": weak_verb_count,
        "avg_words_per_bullet": avg_words_per_bullet,
    }


def readability(text: str) -> float:
    """Flesch reading-ease score (higher = easier)."""
    words = _tokens(text)
    sentences = [s for s in re.split(r"[.!?]+", text or "") if s.strip()]
    n_words = len(words)
    n_sentences = max(1, len(sentences))
    if n_words == 0:
        return 0.0
    syllables = sum(_count_syllables(w) for w in words)
    score = (206.835
             - 1.015 * (n_words / n_sentences)
             - 84.6 * (syllables / n_words))
    return round(score, 1)


def resume_score(text: str) -> Dict:
    """Composite 0-100 score plus sub-scores."""
    stats = compute_stats(text)
    sections = detect_sections(text)
    skills = extract_skills(text)
    n_skills = sum(len(v) for v in skills.values())

    completeness = _clamp(sum(sections.values()) / len(sections) * 100)
    impact = _clamp(stats["action_verb_count"] * 11 + stats["quantified_count"] * 13)

    wc = stats["word_count"]
    if 350 <= wc <= 850:
        brevity = 100
    elif wc < 350:
        brevity = _clamp(wc / 350 * 100)
    else:
        brevity = _clamp(100 - (wc - 850) / 12)

    flesch = readability(text)
    # 30-70 Flesch is the sweet spot for professional prose.
    clarity = _clamp(100 - abs(50 - max(0, min(100, flesch))) * 1.4)

    keywords = _clamp(n_skills * 10)

    overall = _clamp(
        impact * 0.30 + completeness * 0.25 + keywords * 0.20
        + brevity * 0.15 + clarity * 0.10
    )
    return {
        "overall": overall,
        "subscores": {
            "impact": impact,
            "completeness": completeness,
            "brevity": brevity,
            "clarity": clarity,
            "keywords": keywords,
        },
    }


def suggestions(text: str) -> List[str]:
    """Actionable, rule-based improvement tips."""
    tips: List[str] = []
    stats = compute_stats(text)
    sections = detect_sections(text)

    if not sections["summary"]:
        tips.append("Add a Summary or Objective section to frame your value up front.")
    if not sections["skills"]:
        tips.append("Add a Skills section listing your core tools and technologies.")
    if not sections["experience"]:
        tips.append("Add a clear Experience section with dated roles.")

    if stats["bullet_count"] and stats["quantified_count"] / max(1, stats["bullet_count"]) < 0.5:
        tips.append("Quantify more achievements with metrics (%, $, time saved, scale).")
    elif stats["bullet_count"] == 0:
        tips.append("Use bullet points for achievements instead of paragraphs.")

    if stats["weak_verb_count"] > 0:
        tips.append("Replace weak verbs (worked, responsible, helped) with strong "
                    "action verbs like led, built, or spearheaded.")
    if stats["action_verb_count"] < 3:
        tips.append("Start each bullet with a strong action verb.")

    if stats["word_count"] < 250:
        tips.append("Your resume looks short — expand on impact and responsibilities.")
    elif stats["word_count"] > 900:
        tips.append("Your resume is long — tighten it toward one to two pages.")

    if not tips:
        tips.append("Strong resume! Tailor keywords to each job description for the best results.")
    return tips


def match_job_description(resume_text: str, jd_text: str) -> Dict:
    """Score resume against a job description (TF-IDF cosine) + keyword gaps."""
    resume_text = resume_text or ""
    jd_text = jd_text or ""
    if not resume_text.strip() or not jd_text.strip():
        return {"score": 0, "matched": [], "missing": []}

    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        tfidf = TfidfVectorizer(stop_words="english").fit_transform([resume_text, jd_text])
        cosine = float(cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0])
    except Exception:
        cosine = 0.0

    resume_terms = set(_tokens(resume_text))
    jd_terms = []
    seen = set()
    for t in _tokens(jd_text):
        base = t.strip(".-+#")
        if len(base) < 3 or base in _STOPWORDS or base in seen:
            continue
        seen.add(base)
        jd_terms.append(base)

    matched = [t for t in jd_terms if t in resume_terms]
    missing = [t for t in jd_terms if t not in resume_terms]

    # Blend keyword overlap (intuitive) with TF-IDF cosine (content depth). A short
    # JD against a long resume yields a tiny cosine, so overlap carries more weight.
    overlap = len(matched) / len(jd_terms) if jd_terms else 0.0
    score = _clamp(overlap * 65 + cosine * 35)
    return {
        "score": score,
        "matched": matched[:25],
        "missing": missing[:25],
    }


def analyze(text: str) -> Dict:
    """One call returning everything the dashboard needs."""
    return {
        "stats": compute_stats(text),
        "sections": detect_sections(text),
        "skills": extract_skills(text),
        "score": resume_score(text),
        "suggestions": suggestions(text),
        "readability": readability(text),
    }
