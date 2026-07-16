"""LangGraph orchestrator — the same panel, with conditional routing.

Where `Orchestrator` runs all six agents in a line, this one branches: a job
description too vague to match against skips SkillMatch and Experience
entirely and goes straight to the escalation, because scoring a candidate
against nothing is wasted work whose only output would be a number the
DecisionAgent is about to throw away.

The branch is visible in the response — skipped agents appear in the trace with
`status: "skipped"`, so the interface shows the route the case actually took.

Both orchestrators return the identical shape (see `screening.result`), so the
front end neither knows nor cares which one ran.

Select with ORCHESTRATOR=graph. The default is linear: langgraph imports a
sizeable dependency tree, and paying that on every serverless cold start is
only worth it if the routing is wanted.
"""

import logging
import operator
import time
from typing import Annotated, Literal, TypedDict

from langgraph.graph import END, StateGraph

from screening import result as result_shape
from screening.agents.decision_agent import DecisionAgent
from screening.agents.experience_agent import ExperienceAgent
from screening.agents.explanation_agent import ExplanationAgent
from screening.agents.jd_parser import JDParserAgent
from screening.agents.resume_parser import ResumeParserAgent
from screening.agents.skill_match_agent import SkillMatchAgent
from screening.services.documents import extract_text_from_path
from screening.services.llm_service import LLMService

logger = logging.getLogger(__name__)


class ScreeningState(TypedDict, total=False):
    resume_text: str
    jd_text: str
    resume_data: dict
    jd_data: dict
    skill_result: dict
    experience_result: dict
    decision_result: dict
    explanation: str
    # Nodes append; the reducer concatenates rather than overwriting.
    trace: Annotated[list[dict], operator.add]


def _step(agent: str, description: str, started: float,
          output: dict | None = None, status: str = "ok") -> dict:
    return {
        "agent": agent,
        "description": description,
        "duration_ms": round((time.perf_counter() - started) * 1000),
        "source": (output or {}).get("source"),
        "note": (output or {}).get("note"),
        "status": status,
    }


def _skipped(agent: str, description: str, why: str) -> dict:
    return {
        "agent": agent,
        "description": description,
        "duration_ms": 0,
        "source": None,
        "note": why,
        "status": "skipped",
    }


class GraphOrchestrator:
    def __init__(self) -> None:
        self.llm = LLMService()
        self.resume_agent = ResumeParserAgent(self.llm)
        self.jd_agent = JDParserAgent(self.llm)
        self.skill_agent = SkillMatchAgent()
        self.experience_agent = ExperienceAgent()
        self.decision_agent = DecisionAgent()
        self.explanation_agent = ExplanationAgent()
        self.graph = self._build()

    # ── nodes ─────────────────────────────────────────────────────────

    def _parse_resume(self, state: ScreeningState) -> ScreeningState:
        started = time.perf_counter()
        data = self.resume_agent.parse(state["resume_text"])
        return {
            "resume_data": data,
            "trace": [_step("ResumeParser",
                            "Read the resume into structured skills and experience",
                            started, data)],
        }

    def _parse_jd(self, state: ScreeningState) -> ScreeningState:
        started = time.perf_counter()
        data = self.jd_agent.parse(state["jd_text"])
        return {
            "jd_data": data,
            "trace": [_step("JDParser",
                            "Read the role's requirements and experience band",
                            started, data)],
        }

    def _match_skills(self, state: ScreeningState) -> ScreeningState:
        started = time.perf_counter()
        data = self.skill_agent.evaluate(state["resume_data"], state["jd_data"])
        return {
            "skill_result": data,
            "trace": [_step("SkillMatch",
                            "Compared the candidate's skills against the requirements",
                            started)],
        }

    def _evaluate_experience(self, state: ScreeningState) -> ScreeningState:
        started = time.perf_counter()
        data = self.experience_agent.evaluate(state["resume_data"], state["jd_data"])
        return {
            "experience_result": data,
            "trace": [_step("Experience",
                            "Weighed years of experience against the role's band",
                            started)],
        }

    def _skip_matching(self, state: ScreeningState) -> ScreeningState:
        why = "Skipped — the role names no concrete requirements to match against."
        logger.info("Vague JD: bypassing skill and experience agents")
        return {
            "trace": [
                _skipped("SkillMatch",
                         "Compared the candidate's skills against the requirements", why),
                _skipped("Experience",
                         "Weighed years of experience against the role's band", why),
            ],
        }

    def _decide(self, state: ScreeningState) -> ScreeningState:
        started = time.perf_counter()
        # On the vague route skill_result/experience_result are absent. The
        # DecisionAgent escalates on JD clarity before reading either, so the
        # empty dicts are never dereferenced — no branch-specific logic here.
        data = self.decision_agent.decide(
            state.get("skill_result", {}),
            state.get("experience_result", {}),
            state["jd_data"],
            state["resume_data"],
        )
        return {
            "decision_result": data,
            "trace": [_step("Decision",
                            "Combined the signals into a recommendation", started)],
        }

    def _explain(self, state: ScreeningState) -> ScreeningState:
        started = time.perf_counter()
        text = self.explanation_agent.generate(
            state["resume_data"],
            state["jd_data"],
            state.get("skill_result", result_shape.SKILL_MATCH_NOT_RUN),
            state.get("experience_result", result_shape.EXPERIENCE_NOT_RUN),
            state["decision_result"],
        )
        return {
            "explanation": text,
            "trace": [_step("Explanation",
                            "Wrote the rationale for the decision", started)],
        }

    # ── routing ───────────────────────────────────────────────────────

    @staticmethod
    def _route_after_jd(state: ScreeningState) -> Literal["match_skills", "skip_matching"]:
        jd_data = state.get("jd_data", {})
        if not jd_data.get("required_skills") or jd_data.get("jd_clarity") == "vague":
            return "skip_matching"
        return "match_skills"

    def _build(self):
        workflow = StateGraph(ScreeningState)

        workflow.add_node("parse_resume", self._parse_resume)
        workflow.add_node("parse_jd", self._parse_jd)
        workflow.add_node("match_skills", self._match_skills)
        workflow.add_node("evaluate_experience", self._evaluate_experience)
        workflow.add_node("skip_matching", self._skip_matching)
        workflow.add_node("make_decision", self._decide)
        workflow.add_node("explain", self._explain)

        workflow.set_entry_point("parse_resume")
        workflow.add_edge("parse_resume", "parse_jd")

        workflow.add_conditional_edges(
            "parse_jd",
            self._route_after_jd,
            {"match_skills": "match_skills", "skip_matching": "skip_matching"},
        )

        workflow.add_edge("match_skills", "evaluate_experience")
        workflow.add_edge("evaluate_experience", "make_decision")
        workflow.add_edge("skip_matching", "make_decision")
        workflow.add_edge("make_decision", "explain")
        workflow.add_edge("explain", END)

        return workflow.compile()

    # ── entry points ──────────────────────────────────────────────────

    def run_from_text(self, resume_text: str, jd_text: str) -> dict:
        final = self.graph.invoke({"resume_text": resume_text, "jd_text": jd_text})

        return result_shape.shape(
            final["resume_data"],
            final["jd_data"],
            final.get("skill_result"),
            final.get("experience_result"),
            final["decision_result"],
            final["explanation"],
            _in_panel_order(final["trace"]),
        )

    def run(self, resume_path: str, jd_path: str) -> dict:
        """Path-based entry point, for parity with Orchestrator."""
        resume_text = extract_text_from_path(resume_path)
        with open(jd_path, "r", encoding="utf-8") as f:
            return self.run_from_text(resume_text, f.read())


_PANEL_ORDER = [
    "ResumeParser", "JDParser", "SkillMatch",
    "Experience", "Decision", "Explanation",
]


def _in_panel_order(trace: list[dict]) -> list[dict]:
    """Nodes append as they fire, so a skip lands out of order. The interface
    reads the trace as the panel's running sheet, so restore that order."""
    return sorted(trace, key=lambda s: _PANEL_ORDER.index(s["agent"]))
