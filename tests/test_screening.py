"""Deterministic-mode tests.

Everything here runs without an API key, so the suite is reproducible and free.
The LLM path is exercised by asserting the agents degrade correctly when it is
unavailable, which is the behaviour that actually has to hold in production.
"""

import os

os.environ["USE_LLM"] = "false"

import pytest

from screening.agents.decision_agent import DecisionAgent
from screening.agents.experience_agent import ExperienceAgent
from screening.agents.skill_match_agent import SkillMatchAgent
from screening.orchestrator import Orchestrator
from screening.services import taxonomy
from screening.services.documents import DocumentError, extract_text

# The same fixtures the interface offers as samples — served from public/ so the
# browser can fetch them, and read from disk here. One copy, not two.
DATA = os.path.join(os.path.dirname(__file__), "..", "public", "samples")


# ── taxonomy ──────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "surface,expected",
    [
        ("postgres", "PostgreSQL"),
        ("PostgreSQL", "PostgreSQL"),
        ("psql", "PostgreSQL"),
        ("nodejs", "Node.js"),
        ("Node.js", "Node.js"),
        ("k8s", "Kubernetes"),
        ("experience with Docker", "Docker"),
        ("django rest framework", "Django REST Framework"),
    ],
)
def test_canonical_collapses_surface_forms(surface, expected):
    assert taxonomy.canonical(surface) == expected


def test_canonical_keeps_unknown_skills():
    # Dropping what the vocabulary hasn't heard of would silently deflate the
    # match score, so unrecognised terms survive rather than vanish.
    assert taxonomy.canonical("Erlang") == "Erlang"
    assert taxonomy.canonical("COBOL") == "COBOL"


def test_canonical_narrows_a_variant_to_its_base_skill():
    # "Kubernetes Operators" has to reach a JD asking for plain Kubernetes.
    assert taxonomy.canonical("Kubernetes Operators") == "Kubernetes"


def test_longest_alias_wins():
    skills = taxonomy.extract_skills("Built APIs with Django REST Framework.")
    assert "Django REST Framework" in skills


def test_learning_context_is_not_a_skill():
    text = "Currently learning Django through online courses\nLearning: Docker, Redis"
    skills = taxonomy.extract_skills(text)
    assert "Django" not in skills
    assert "Docker" not in skills
    assert "Redis" not in skills


def test_skill_held_elsewhere_survives_a_learning_mention():
    text = "Built a REST API using Flask with SQLite\nLearning: Flask, Django"
    skills = taxonomy.extract_skills(text)
    assert "Flask" in skills
    assert "Django" not in skills


def test_education_dates_are_not_experience():
    text = (
        "WORK EXPERIENCE\nEngineer | 2024 - Present\n"
        "EDUCATION\nB.E. Mechanical | Anna University | 2014 - 2018\n"
    )
    # 2014-2018 is a degree. Counting it would age a junior by four years.
    assert taxonomy.extract_experience_years(text) < 4


def test_stated_total_beats_date_ranges():
    text = "Backend engineer with 3+ years of experience.\nRole | 2019 - Present"
    assert taxonomy.extract_experience_years(text) == 3.0


@pytest.mark.parametrize(
    "text,expected",
    [
        ("EXPERIENCE: 2-4 years", {"min": 2, "max": 4}),
        ("Requires 5+ years", {"min": 5, "max": None}),
        ("minimum 3 years of experience", {"min": 3, "max": None}),
        ("Experienced developer wanted", None),
    ],
)
def test_experience_requirement(text, expected):
    assert taxonomy.extract_experience_requirement(text) == expected


# ── agents ────────────────────────────────────────────────────────────


def test_skill_match_normalises_both_sides():
    result = SkillMatchAgent().evaluate(
        {"skills": ["PostgreSQL", "python"]},
        {"required_skills": ["postgres", "Python"]},
    )
    assert result["score"] == 100
    assert result["coverage"] == "2/2"


def test_skill_match_survives_missing_keys():
    assert SkillMatchAgent().evaluate({}, {})["score"] == 0


@pytest.mark.parametrize(
    "years,band,status",
    [
        (3, {"min": 2, "max": 4}, "Fit"),
        (1, {"min": 4, "max": 7}, "Under-qualified"),
        (9, {"min": 2, "max": 4}, "Over-qualified"),
        (8, {"min": 5, "max": None}, "Fit"),
        (3, None, "Unknown"),
    ],
)
def test_experience_verdicts(years, band, status):
    result = ExperienceAgent().evaluate(
        {"experience_years": years}, {"experience_required": band}
    )
    assert result["status"] == status


def test_vague_jd_escalates_instead_of_scoring():
    result = DecisionAgent().decide(
        {"score": 90}, {"score": 100, "status": "Fit"},
        {"required_skills": [], "jd_clarity": "vague"},
        {"skills": ["Python"]},
    )
    assert result["requires_human"] is True
    assert result["match_score"] == 0.0
    assert result["reason"]


def test_unreadable_resume_escalates():
    result = DecisionAgent().decide(
        {"score": 0}, {"score": 50, "status": "Unknown"},
        {"required_skills": ["Python"], "jd_clarity": "clear"},
        {"skills": []},
    )
    assert result["requires_human"] is True


def test_unknown_experience_forces_review():
    # A neutral 50 for experience is a guess; it must not become a confident yes.
    result = DecisionAgent().decide(
        {"score": 100}, {"score": 50, "status": "Unknown"},
        {"required_skills": ["Python", "SQL"], "jd_clarity": "clear"},
        {"skills": ["Python", "SQL"]},
    )
    assert result["requires_human"] is True


# ── documents ─────────────────────────────────────────────────────────


def test_unsupported_file_is_rejected():
    with pytest.raises(DocumentError, match="Unsupported"):
        extract_text(b"Just some text, not a resume at all")


def test_file_lying_about_being_a_pdf_is_rejected():
    with pytest.raises(DocumentError, match="claims to be a PDF"):
        extract_text(b"not really a pdf", "resume.pdf")


def test_empty_upload_is_rejected():
    with pytest.raises(DocumentError):
        extract_text(b"")


def test_pdf_is_detected_by_content_not_extension():
    with open(os.path.join(DATA, "resume_01_priya_sharma.pdf"), "rb") as f:
        # Mislabelled on purpose: the magic number has to win.
        assert "priya" in extract_text(f.read(), "resume.docx").lower()


# ── end to end ────────────────────────────────────────────────────────


def _run(resume: str, jd: str) -> dict:
    return Orchestrator().run(
        os.path.join(DATA, resume), os.path.join(DATA, jd)
    )


def test_strong_candidate_reaches_interview():
    result = _run("resume_01_priya_sharma.pdf", "jd_01_backend_python_standard.txt")
    assert result["recommendation"] == "Proceed to interview"
    assert result["requires_human"] is False
    assert result["match_score"] > 0.85


def test_vague_jd_is_handed_to_a_human():
    result = _run("resume_01_priya_sharma.pdf", "jd_04_vague_ambiguous.txt")
    assert result["requires_human"] is True
    assert result["scored"] is False


def test_career_switcher_is_not_aged_by_their_degree():
    result = _run("resume_04_vikram_singh.pdf", "jd_03_junior_flexible.txt")
    assert result["candidate"]["experience_years"] <= 3


def test_pipeline_reports_every_agent():
    result = _run("resume_01_priya_sharma.pdf", "jd_01_backend_python_standard.txt")
    assert [s["agent"] for s in result["trace"]] == [
        "ResumeParser", "JDParser", "SkillMatch",
        "Experience", "Decision", "Explanation",
    ]


def test_runs_without_an_api_key():
    # The deploy path when GEMINI_API_KEY is unset: degrade, never crash.
    result = _run("resume_01_priya_sharma.pdf", "jd_01_backend_python_standard.txt")
    assert result["mode"] == "rule_based"
    assert result["candidate"]["skills"]
