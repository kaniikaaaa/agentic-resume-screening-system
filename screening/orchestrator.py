"""The linear orchestrator: all six agents, in order, every time.

The default. `GraphOrchestrator` is the same panel with conditional routing —
see ORCHESTRATOR in screening/config.py.
"""

import time

from screening import result as result_shape
from screening.agents.decision_agent import DecisionAgent
from screening.agents.experience_agent import ExperienceAgent
from screening.agents.explanation_agent import ExplanationAgent
from screening.agents.jd_parser import JDParserAgent
from screening.agents.resume_parser import ResumeParserAgent
from screening.agents.skill_match_agent import SkillMatchAgent
from screening.services.documents import extract_text_from_path
from screening.services.llm_service import LLMService


class Orchestrator:
    def __init__(self) -> None:
        # One LLM client shared by both parsers; constructing it per agent
        # would rebuild the HTTP session twice per request.
        self.llm = LLMService()
        self.resume_agent = ResumeParserAgent(self.llm)
        self.jd_agent = JDParserAgent(self.llm)
        self.skill_agent = SkillMatchAgent()
        self.experience_agent = ExperienceAgent()
        self.decision_agent = DecisionAgent()
        self.explanation_agent = ExplanationAgent()

    def run_from_text(self, resume_text: str, jd_text: str) -> dict:
        trace: list[dict] = []

        def step(name: str, description: str, fn):
            started = time.perf_counter()
            output = fn()
            trace.append({
                "agent": name,
                "description": description,
                "duration_ms": round((time.perf_counter() - started) * 1000),
                "source": output.get("source") if isinstance(output, dict) else None,
                "note": output.get("note") if isinstance(output, dict) else None,
                "status": "ok",
            })
            return output

        resume_data = step(
            "ResumeParser", "Read the resume into structured skills and experience",
            lambda: self.resume_agent.parse(resume_text),
        )
        jd_data = step(
            "JDParser", "Read the role's requirements and experience band",
            lambda: self.jd_agent.parse(jd_text),
        )
        skill_result = step(
            "SkillMatch", "Compared the candidate's skills against the requirements",
            lambda: self.skill_agent.evaluate(resume_data, jd_data),
        )
        experience_result = step(
            "Experience", "Weighed years of experience against the role's band",
            lambda: self.experience_agent.evaluate(resume_data, jd_data),
        )
        decision_result = step(
            "Decision", "Combined the signals into a recommendation",
            lambda: self.decision_agent.decide(
                skill_result, experience_result, jd_data, resume_data
            ),
        )
        explanation = step(
            "Explanation", "Wrote the rationale for the decision",
            lambda: {"text": self.explanation_agent.generate(
                resume_data, jd_data, skill_result, experience_result, decision_result
            )},
        )["text"]

        return result_shape.shape(
            resume_data, jd_data, skill_result, experience_result,
            decision_result, explanation, trace,
        )

    def run(self, resume_path: str, jd_path: str) -> dict:
        """Path-based entry point, kept for the local test suite."""
        resume_text = extract_text_from_path(resume_path)
        with open(jd_path, "r", encoding="utf-8") as f:
            return self.run_from_text(resume_text, f.read())
