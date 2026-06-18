"""Pure-Python resume analysis.

No FastAPI, no I/O, no external API calls — every function takes text and returns
plain data, so it is fully unit-testable. Used by the upload flow to build the
Resume Intelligence Dashboard.
"""
from __future__ import annotations

import datetime
import math
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
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return int(lo)
    return int(max(lo, min(hi, round(value))))


# --- Public API -------------------------------------------------------------

def _is_heading(line: str, keywords: List[str]) -> bool:
    """A heading is a short line (<=3 words) that is or contains a section keyword.

    This avoids false positives from inline prose like "5 years of experience".
    """
    compact = re.sub(r"[^a-z ]", "", line.lower()).strip()
    if not compact:
        return False
    words = compact.split()
    for kw in keywords:
        if compact == kw:
            return True
        if len(words) <= 3 and re.search(r"\b" + re.escape(kw) + r"\b", compact):
            return True
    return False


def detect_sections(text: str) -> Dict[str, bool]:
    """Return which standard resume sections are present (heading-based)."""
    lines = (text or "").splitlines()
    result = {}
    for section, keywords in SECTION_KEYWORDS.items():
        result[section] = any(_is_heading(line, keywords) for line in lines)
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

    # No words => nothing to read; clarity is 0 (not the formula's midpoint).
    if stats["word_count"] == 0:
        clarity = 0
    else:
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
    except ImportError:
        # scikit-learn unavailable: fall back to keyword-overlap only.
        print("analysis: scikit-learn not installed; JD match uses keyword overlap only.")
        cosine = 0.0
    except Exception as e:
        print(f"analysis: JD cosine failed ({e}); using keyword overlap only.")
        cosine = 0.0
    if math.isnan(cosine):
        cosine = 0.0
    cosine = max(0.0, min(1.0, cosine))

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


_YEAR = r"(?:19|20)\d{2}"
_MON = r"(?:jan|feb|mar|apr|may|jun|jul|aug|sept?|oct|nov|dec)[a-z]*\.?"
_TIMELINE_RE = re.compile(
    r"(?:" + _MON + r"\s*)?(?:\d{1,2}[/-])?(" + _YEAR + r")"          # group 1: start year
    r"\s*(?:[-–—]|\bto\b)\s*"                                          # separator
    r"(?:(?:(?:" + _MON + r"\s*)?(?:\d{1,2}[/-])?(" + _YEAR + r"))"     # group 2: end year
    r"|(present|current|now|till\s*date|to\s*date))",                  # group 3: open-ended
    re.IGNORECASE,
)


def extract_timeline(text: str) -> List[Dict]:
    """Parse dated experience/education ranges into a chronological timeline."""
    current_year = datetime.date.today().year
    entries: List[Dict] = []
    for line in (text or "").splitlines():
        line = line.strip()
        m = _TIMELINE_RE.search(line)
        if not m:
            continue
        start_year = int(m.group(1))
        if m.group(2):
            end_year = int(m.group(2))
            end = str(end_year)
        else:
            end = "Present"
            end_year = current_year
        label = (line[:m.start()] + " " + line[m.end():]).strip(" ,-–—\t|·•")
        label = re.sub(r"\s{2,}", " ", label)
        if len(label) < 3:
            label = line
        entries.append({
            "label": label,
            "start_year": start_year,
            "end_year": end_year,
            "end": end,
        })
    entries.sort(key=lambda e: (e["start_year"], e["end_year"]), reverse=True)
    return entries[:12]


_NON_NAME = {"resume", "curriculum", "vitae", "cv", "profile", "summary", "objective",
             "experience", "education", "skills", "projects", "contact", "portfolio"}
_TITLE_WORDS = {"engineer", "developer", "manager", "analyst", "designer", "consultant",
                "scientist", "intern", "specialist", "administrator", "architect", "lead",
                "senior", "junior", "officer", "director", "coordinator", "associate",
                "executive"}


def _candidate_name(text: str) -> str:
    """Best-effort extraction of the candidate's name (first Title-Case 2-4 word line).

    Rejects document/section words ("Resume") and job titles ("Software Engineer") so a
    cover letter is never signed with a heading. Falls back to "Candidate".
    """
    for line in (text or "").splitlines():
        s = line.strip()
        if not s:
            continue
        if any(c.isdigit() for c in s) or "@" in s or len(s) > 40:
            break
        words = s.split()
        low = [w.lower() for w in words]
        if (2 <= len(words) <= 4
                and all(w[0].isalpha() and w[0].isupper() for w in words)
                and not any(w in _NON_NAME or w in _TITLE_WORDS for w in low)):
            return s
        break
    return "Candidate"


def generate_cover_letter(resume_text: str, role: str, company: str) -> str:
    """Draft a tailored 3-paragraph cover letter from the resume (template-based)."""
    role = (role or "the role").strip() or "the role"
    company = (company or "your company").strip() or "your company"
    name = _candidate_name(resume_text)
    flat = [s for group in extract_skills(resume_text).values() for s in group]
    top = flat[:5]
    if top:
        joined = ", ".join(top[:-1]) + ((" and " + top[-1]) if len(top) > 1 else top[0])
        skills_sentence = f"My background includes hands-on experience with {joined}. "
    else:
        skills_sentence = "I bring a fast-learning, results-oriented background. "

    return (
        f"Dear Hiring Manager,\n\n"
        f"I am excited to apply for the {role} position at {company}. The opportunity to "
        f"contribute to your team aligns strongly with my skills and career goals.\n\n"
        f"{skills_sentence}I focus on delivering measurable impact, collaborating across "
        f"teams, and continuously raising the quality of my work.\n\n"
        f"I would welcome the chance to discuss how I can help {company} succeed in the "
        f"{role} role. Thank you for your time and consideration.\n\n"
        f"Sincerely,\n{name}"
    )


def rank_jobs(resume_text: str, jobs: List[Dict]) -> List[Dict]:
    """Rank the resume against several jobs (highest match first)."""
    results = []
    for job in jobs or []:
        title = (job.get("title") or "Untitled role").strip() or "Untitled role"
        m = match_job_description(resume_text, job.get("text") or "")
        results.append({"title": title, "score": m["score"], "matched": m["matched"], "missing": m["missing"]})
    results.sort(key=lambda r: r["score"], reverse=True)
    return results


def analyze(text: str) -> Dict:
    """One call returning everything the dashboard needs."""
    return {
        "stats": compute_stats(text),
        "sections": detect_sections(text),
        "skills": extract_skills(text),
        "score": resume_score(text),
        "suggestions": suggestions(text),
        "readability": readability(text),
        "timeline": extract_timeline(text),
    }
