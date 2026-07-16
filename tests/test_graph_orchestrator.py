"""The LangGraph route.

The contract that matters: it must agree with the linear orchestrator on the
verdict, and differ only in the work it skips getting there.
"""

import os

os.environ["USE_LLM"] = "false"

import pytest

from screening.graph_orchestrator import GraphOrchestrator
from screening.orchestrator import Orchestrator

DATA = os.path.join(os.path.dirname(__file__), "..", "public", "samples")


def _path(name: str) -> str:
    return os.path.join(DATA, name)


@pytest.fixture(scope="module")
def graph():
    return GraphOrchestrator()


@pytest.fixture(scope="module")
def linear():
    return Orchestrator()


CASES = [
    ("resume_01_priya_sharma.pdf", "jd_01_backend_python_standard.txt"),
    ("resume_02_rahul_verma.pdf", "jd_01_backend_python_standard.txt"),
    ("resume_03_ananya_patel.pdf", "jd_02_senior_fintech_strict.txt"),
    ("resume_04_vikram_singh.pdf", "jd_03_junior_flexible.txt"),
    ("resume_01_priya_sharma.pdf", "jd_04_vague_ambiguous.txt"),
]


@pytest.mark.parametrize("resume,jd", CASES)
def test_both_routes_reach_the_same_verdict(graph, linear, resume, jd):
    # Routing may skip work, but it must never change the answer.
    a = linear.run(_path(resume), _path(jd))
    b = graph.run(_path(resume), _path(jd))

    for field in ("match_score", "recommendation", "requires_human",
                  "confidence", "scored", "reasoning_summary"):
        assert a[field] == b[field], f"{field} diverged on {resume} vs {jd}"


def test_vague_jd_skips_the_matching_agents(graph):
    result = graph.run(
        _path("resume_01_priya_sharma.pdf"), _path("jd_04_vague_ambiguous.txt")
    )
    status = {s["agent"]: s["status"] for s in result["trace"]}

    assert status["SkillMatch"] == "skipped"
    assert status["Experience"] == "skipped"
    # The decision still has to be made and explained.
    assert status["Decision"] == "ok"
    assert status["Explanation"] == "ok"
    assert result["requires_human"] is True


def test_clear_jd_runs_every_agent(graph):
    result = graph.run(
        _path("resume_01_priya_sharma.pdf"), _path("jd_01_backend_python_standard.txt")
    )
    assert all(s["status"] == "ok" for s in result["trace"])


def test_trace_is_in_panel_order(graph):
    # Nodes append as they fire, so a skip lands out of order without sorting.
    result = graph.run(
        _path("resume_01_priya_sharma.pdf"), _path("jd_04_vague_ambiguous.txt")
    )
    assert [s["agent"] for s in result["trace"]] == [
        "ResumeParser", "JDParser", "SkillMatch",
        "Experience", "Decision", "Explanation",
    ]


def test_shape_matches_the_linear_route(graph, linear):
    a = linear.run(_path("resume_01_priya_sharma.pdf"), _path("jd_01_backend_python_standard.txt"))
    b = graph.run(_path("resume_01_priya_sharma.pdf"), _path("jd_01_backend_python_standard.txt"))
    assert a.keys() == b.keys()
