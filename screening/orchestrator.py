"""Coordinates the agent pipeline and records what each agent did."""

import time

from screening.agents.decision_agent import DecisionAgent
from screening.agents.experience_agent import ExperienceAgent
from screening.agents.explanation_agent import ExplanationAgent
from screening.agents.jd_parser import JDParserAgent
from screening.agents.resume_parser import ResumeParserAgent
from screening.agents.skill_match_agent import SkillMatchAgent
from screening.services.llm_service import LLMService
from screening.services.pdf import extract_text_from_bytes


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

        sources = {resume_data.get("source"), jd_data.get("source")}
        mode = "llm" if sources == {"llm"} else (
            "rule_based" if sources == {"rule_based"} else "mixed"
        )

        return {
            # The contract the assignment specifies, unchanged.
            "match_score": decision_result["match_score"],
            "recommendation": decision_result["recommendation"],
            "requires_human": decision_result["requires_human"],
            "confidence": decision_result["confidence"],
            "reasoning_summary": explanation,
            # Everything below is what the interface renders.
            "mode": mode,
            "final_score": decision_result["final_score"],
            # An escalation reports 0.0 because it declined to score, not
            # because the candidate scored nothing. The interface needs to tell
            # those apart or it will libel the candidate.
            "scored": decision_result["reason"] is None,
            "candidate": {
                "skills": resume_data["skills"],
                "experience_years": resume_data["experience_years"],
                "projects": resume_data.get("projects", []),
                "source": resume_data["source"],
            },
            "role": {
                "required_skills": jd_data["required_skills"],
                "experience_required": jd_data["experience_required"],
                "clarity": jd_data["jd_clarity"],
                "source": jd_data["source"],
            },
            "skill_match": skill_result,
            "experience": experience_result,
            "trace": trace,
        }

    def run(self, resume_path: str, jd_path: str) -> dict:
        """Path-based entry point, kept for the local test suite."""
        with open(resume_path, "rb") as f:
            resume_text = extract_text_from_bytes(f.read())

        with open(jd_path, "r", encoding="utf-8") as f:
            jd_text = f.read()

        return self.run_from_text(resume_text, jd_text)
