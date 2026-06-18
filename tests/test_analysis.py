"""Unit tests for the pure-Python resume analysis module (TDD)."""
import math

import analysis


SAMPLE = """
John Doe
Software Engineer

SUMMARY
Experienced software engineer with 5 years building scalable web applications.

EXPERIENCE
Senior Engineer, Acme Corp
- Led a team of 5 engineers and increased deployment speed by 40%
- Built REST APIs in Python and FastAPI serving 1M requests per day
- Reduced infrastructure costs by $200,000 annually

EDUCATION
B.S. Computer Science, MIT

SKILLS
Python, JavaScript, React, Docker, Kubernetes, AWS, PostgreSQL

PROJECTS
- Developed an open-source library with 2000 GitHub stars
"""

WEAK = "Worked on stuff. Did things. Was responsible for the team."


# --- detect_sections ---

def test_detect_sections_finds_present_sections():
    s = analysis.detect_sections(SAMPLE)
    assert s["summary"] is True
    assert s["experience"] is True
    assert s["education"] is True
    assert s["skills"] is True
    assert s["projects"] is True


def test_detect_sections_marks_missing_section():
    s = analysis.detect_sections(SAMPLE)
    assert s["certifications"] is False


# --- extract_skills ---

def test_extract_skills_groups_known_skills():
    skills = analysis.extract_skills(SAMPLE)
    flat = [x.lower() for group in skills.values() for x in group]
    assert "python" in flat
    assert "react" in flat
    assert "docker" in flat


def test_extract_skills_returns_dict_of_lists():
    skills = analysis.extract_skills(SAMPLE)
    assert isinstance(skills, dict)
    assert all(isinstance(v, list) for v in skills.values())


# --- compute_stats ---

def test_compute_stats_counts_bullets_and_quantified():
    st = analysis.compute_stats(SAMPLE)
    assert st["bullet_count"] == 4
    assert st["quantified_count"] >= 3
    assert st["action_verb_count"] >= 3
    assert st["word_count"] > 30
    assert st["reading_time_min"] >= 1


# --- readability ---

def test_readability_returns_number():
    r = analysis.readability(SAMPLE)
    assert isinstance(r, (int, float))
    assert not math.isnan(r)


# --- resume_score ---

def test_resume_score_within_bounds():
    score = analysis.resume_score(SAMPLE)
    assert 0 <= score["overall"] <= 100
    for key in ("impact", "completeness", "brevity", "clarity", "keywords"):
        assert 0 <= score["subscores"][key] <= 100


def test_strong_resume_scores_higher_than_weak():
    assert analysis.resume_score(SAMPLE)["overall"] > analysis.resume_score(WEAK)["overall"]


# --- suggestions ---

def test_suggestions_fire_for_weak_resume():
    tips = analysis.suggestions(WEAK)
    assert isinstance(tips, list)
    assert len(tips) > 0
    assert all(isinstance(t, str) for t in tips)


# --- match_job_description ---

def test_jd_match_identical_is_high():
    res = analysis.match_job_description(SAMPLE, SAMPLE)
    assert res["score"] >= 90


def test_jd_match_reports_matched_and_missing():
    jd = "Seeking a Python developer with FastAPI, AWS, and Kubernetes. Must know GraphQL and Rust."
    res = analysis.match_job_description(SAMPLE, jd)
    assert 0 <= res["score"] <= 100
    matched = [m.lower() for m in res["matched"]]
    missing = [m.lower() for m in res["missing"]]
    assert "python" in matched
    assert "rust" in missing or "graphql" in missing


# --- edge cases from code review ---

def test_empty_resume_scores_zero():
    score = analysis.resume_score("")
    assert score["overall"] == 0
    assert score["subscores"]["clarity"] == 0


def test_whitespace_resume_does_not_crash():
    a = analysis.analyze("   \n\t ")
    assert a["score"]["overall"] == 0


def test_clamp_handles_out_of_range():
    assert analysis._clamp(-5) == 0
    assert analysis._clamp(150) == 100
    assert analysis._clamp(49.5) == 50


def test_jd_match_empty_inputs():
    assert analysis.match_job_description("", "python") == {"score": 0, "matched": [], "missing": []}
    assert analysis.match_job_description("python", "")["score"] == 0


def test_jd_match_all_stopwords_no_crash():
    res = analysis.match_job_description("the and or", "the and or")
    assert isinstance(res["score"], int)
    assert 0 <= res["score"] <= 100


def test_detect_sections_ignores_inline_mentions():
    text = "I have 5 years of experience and my objective is to grow. Did things daily."
    s = analysis.detect_sections(text)
    assert s["experience"] is False
    assert s["summary"] is False


def test_detect_sections_matches_real_headings():
    text = "Professional Experience\nBuilt things.\nEducation\nBSc CS"
    s = analysis.detect_sections(text)
    assert s["experience"] is True
    assert s["education"] is True


def test_extract_skills_respects_word_boundaries():
    flat = [x.lower() for g in analysis.extract_skills("golang postgresql javascript").values() for x in g]
    assert "go" not in flat       # inside "golang"
    assert "sql" not in flat       # inside "postgresql"
    assert "java" not in flat      # inside "javascript"


# --- career timeline ---

TIMELINE_SAMPLE = """
Senior Engineer, Acme Corp    Jan 2020 - Present
Software Engineer, Beta Inc    2017 - 2020
Intern, Gamma Labs    06/2016 - 12/2016
B.S. Computer Science, MIT    2013 - 2017
Increased revenue by 40% during 2019
"""


def test_extract_timeline_finds_ranges():
    tl = analysis.extract_timeline(TIMELINE_SAMPLE)
    assert len(tl) >= 4
    # most recent first
    assert tl[0]["start_year"] == 2020
    assert tl[0]["end"] in ("Present", "present") or tl[0]["end_year"] >= 2026


def test_extract_timeline_labels_roles():
    tl = analysis.extract_timeline(TIMELINE_SAMPLE)
    labels = " ".join(e["label"] for e in tl).lower()
    assert "acme" in labels
    assert "beta" in labels


def test_extract_timeline_ignores_single_year_lines():
    # "Increased revenue by 40% during 2019" has a year but no range -> not an entry
    tl = analysis.extract_timeline(TIMELINE_SAMPLE)
    assert all("revenue" not in e["label"].lower() for e in tl)


def test_extract_timeline_empty():
    assert analysis.extract_timeline("") == []
    assert analysis.extract_timeline("no dates here at all") == []


# --- cover letter ---

def test_cover_letter_includes_role_company_and_skill():
    letter = analysis.generate_cover_letter(SAMPLE, "Machine Learning Engineer", "Nebius")
    assert "Machine Learning Engineer" in letter
    assert "Nebius" in letter
    assert len(letter) > 200
    flat = [s.lower() for g in analysis.extract_skills(SAMPLE).values() for s in g]
    assert any(s in letter.lower() for s in flat)


def test_cover_letter_empty_resume_safe():
    letter = analysis.generate_cover_letter("", "Developer", "Acme")
    assert isinstance(letter, str)
    assert "Developer" in letter and "Acme" in letter


# --- rank jobs ---

def test_rank_jobs_sorts_by_score():
    jobs = [
        {"title": "ML Engineer", "text": "Python PyTorch AWS Docker machine learning data"},
        {"title": "Sales Rep", "text": "cold calling quotas CRM salesforce negotiation retail"},
    ]
    ranked = analysis.rank_jobs(SAMPLE, jobs)
    assert len(ranked) == 2
    assert ranked[0]["score"] >= ranked[1]["score"]
    assert ranked[0]["title"] == "ML Engineer"
    assert "matched" in ranked[0] and "missing" in ranked[0]


def test_rank_jobs_empty():
    assert analysis.rank_jobs(SAMPLE, []) == []


# --- analyze (aggregate) ---

def test_analyze_returns_all_sections():
    a = analysis.analyze(SAMPLE)
    for key in ("stats", "sections", "skills", "score", "suggestions", "readability", "timeline"):
        assert key in a
