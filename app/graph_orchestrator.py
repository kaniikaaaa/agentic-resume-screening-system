"""
LangGraph-based orchestrator for resume screening.

This orchestrator uses a state graph to coordinate agents with:
- Conditional routing based on JD clarity and confidence
- Early exit for vague job descriptions
- File validation and error handling
- Support for PDF and DOCX resumes
"""

import os
from typing import TypedDict, Literal
from langgraph.graph import StateGraph, END
import pdfplumber

from app.agents.resume_parser import ResumeParserAgent
from app.agents.jd_parser import JDParserAgent
from app.agents.skill_match_agent import SkillMatchAgent
from app.agents.experience_agent import ExperienceAgent
from app.agents.decision_agent import DecisionAgent
from app.agents.explanation_agent import ExplanationAgent


SUPPORTED_FORMATS = ['.pdf', '.docx']


class ScreeningState(TypedDict, total=False):
    """State that flows through the screening graph."""
    resume_path: str
    jd_path: str
    resume_text: str
    jd_text: str
    resume_data: dict
    jd_data: dict
    skill_result: dict
    experience_result: dict
    decision_result: dict
    final_output: dict
    error: str


# Initialize agents once (reused across invocations)
_resume_agent = ResumeParserAgent()
_jd_agent = JDParserAgent()
_skill_agent = SkillMatchAgent()
_experience_agent = ExperienceAgent()
_decision_agent = DecisionAgent()
_explanation_agent = ExplanationAgent()


def extract_pdf_text(path: str) -> str:
    """Extract text from PDF file."""
    text = ""
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text


def extract_docx_text(path: str) -> str:
    """Extract text from DOCX file."""
    try:
        from docx import Document
    except ImportError:
        raise ImportError("python-docx is required for DOCX support. Install with: pip install python-docx")

    doc = Document(path)
    text = ""
    for para in doc.paragraphs:
        text += para.text + "\n"
    return text


def _create_error_output(message: str) -> dict:
    """Create standardized error output."""
    return {
        "match_score": 0.0,
        "recommendation": "Manual Review Required",
        "requires_human": True,
        "confidence": 0.0,
        "reasoning_summary": message,
        "data_source": "error"
    }


# --- Node Functions ---

def load_documents(state: ScreeningState) -> ScreeningState:
    """Load and extract text from resume and JD files."""
    resume_path = state["resume_path"]
    ext = os.path.splitext(resume_path)[1].lower()

    try:
        if ext == '.pdf':
            resume_text = extract_pdf_text(resume_path)
        else:
            resume_text = extract_docx_text(resume_path)
    except Exception as e:
        return {"error": f"Failed to parse resume: {str(e)}"}

    if not resume_text or not resume_text.strip():
        return {"error": "Resume file appears to be empty or could not be read."}

    try:
        with open(state["jd_path"], "r", encoding="utf-8") as f:
            jd_text = f.read()
    except Exception as e:
        return {"error": f"Failed to read job description: {str(e)}"}

    if not jd_text or not jd_text.strip():
        return {"error": "Job description file appears to be empty."}

    return {"resume_text": resume_text, "jd_text": jd_text}


def parse_resume(state: ScreeningState) -> ScreeningState:
    """Parse resume using ResumeParserAgent."""
    if state.get("error"):
        return {}
    resume_data = _resume_agent.parse(state["resume_text"])
    return {"resume_data": resume_data}


def parse_jd(state: ScreeningState) -> ScreeningState:
    """Parse job description using JDParserAgent."""
    if state.get("error"):
        return {}
    jd_data = _jd_agent.parse(state["jd_text"])
    return {"jd_data": jd_data}


def match_skills(state: ScreeningState) -> ScreeningState:
    """Evaluate skill match using SkillMatchAgent."""
    skill_result = _skill_agent.evaluate(state["resume_data"], state["jd_data"])
    return {"skill_result": skill_result}


def evaluate_experience(state: ScreeningState) -> ScreeningState:
    """Evaluate experience using ExperienceAgent."""
    experience_result = _experience_agent.evaluate(state["resume_data"], state["jd_data"])
    return {"experience_result": experience_result}


def make_decision(state: ScreeningState) -> ScreeningState:
    """Make hiring decision using DecisionAgent."""
    decision_result = _decision_agent.decide(
        state["skill_result"],
        state["experience_result"],
        state["jd_data"]
    )
    return {"decision_result": decision_result}


def generate_explanation(state: ScreeningState) -> ScreeningState:
    """Generate explanation and build final output."""
    explanation = _explanation_agent.generate(
        state["resume_data"],
        state["jd_data"],
        state["skill_result"],
        state["experience_result"],
        state["decision_result"]
    )

    final_output = {
        "match_score": state["decision_result"]["match_score"],
        "recommendation": state["decision_result"]["recommendation"],
        "requires_human": state["decision_result"]["requires_human"],
        "confidence": state["decision_result"]["confidence"],
        "reasoning_summary": explanation,
        "data_source": state["resume_data"].get("source", "unknown")
    }

    return {"final_output": final_output}


def handle_vague_jd(state: ScreeningState) -> ScreeningState:
    """Handle vague JD by flagging for human review."""
    final_output = {
        "match_score": 0.0,
        "recommendation": "Manual Review Required",
        "requires_human": True,
        "confidence": 0.3,
        "reasoning_summary": "Job description is too vague to make an automated decision. Missing clear technical requirements.",
        "data_source": state.get("resume_data", {}).get("source", "unknown")
    }
    return {"final_output": final_output}


def handle_error(state: ScreeningState) -> ScreeningState:
    """Handle errors by creating error output."""
    final_output = _create_error_output(state.get("error", "Unknown error occurred"))
    return {"final_output": final_output}


# --- Routing Functions ---

def route_after_load(state: ScreeningState) -> Literal["parse_resume", "handle_error"]:
    """Route based on whether loading succeeded."""
    if state.get("error"):
        return "handle_error"
    return "parse_resume"


def route_after_jd_parse(state: ScreeningState) -> Literal["match_skills", "handle_vague_jd"]:
    """Route based on JD clarity."""
    jd_data = state.get("jd_data", {})
    required_skills = jd_data.get("required_skills", [])

    if not required_skills or jd_data.get("jd_clarity") == "vague":
        return "handle_vague_jd"
    return "match_skills"


def route_after_decision(state: ScreeningState) -> Literal["generate_explanation", "handle_vague_jd"]:
    """Route based on decision confidence."""
    decision = state.get("decision_result", {})

    # If decision already flagged for manual review with very low confidence
    if decision.get("confidence", 1.0) < 0.4 and decision.get("requires_human"):
        return "handle_vague_jd"
    return "generate_explanation"


def build_screening_graph() -> StateGraph:
    """Build and compile the screening workflow graph."""

    workflow = StateGraph(ScreeningState)

    # Add nodes
    workflow.add_node("load_documents", load_documents)
    workflow.add_node("parse_resume", parse_resume)
    workflow.add_node("parse_jd", parse_jd)
    workflow.add_node("match_skills", match_skills)
    workflow.add_node("evaluate_experience", evaluate_experience)
    workflow.add_node("make_decision", make_decision)
    workflow.add_node("generate_explanation", generate_explanation)
    workflow.add_node("handle_vague_jd", handle_vague_jd)
    workflow.add_node("handle_error", handle_error)

    # Set entry point
    workflow.set_entry_point("load_documents")

    # Add edges with error handling
    workflow.add_conditional_edges(
        "load_documents",
        route_after_load,
        {
            "parse_resume": "parse_resume",
            "handle_error": "handle_error"
        }
    )

    workflow.add_edge("parse_resume", "parse_jd")

    # Conditional: check JD clarity after parsing
    workflow.add_conditional_edges(
        "parse_jd",
        route_after_jd_parse,
        {
            "match_skills": "match_skills",
            "handle_vague_jd": "handle_vague_jd"
        }
    )

    workflow.add_edge("match_skills", "evaluate_experience")
    workflow.add_edge("evaluate_experience", "make_decision")

    # Conditional: check confidence after decision
    workflow.add_conditional_edges(
        "make_decision",
        route_after_decision,
        {
            "generate_explanation": "generate_explanation",
            "handle_vague_jd": "handle_vague_jd"
        }
    )

    # Terminal edges
    workflow.add_edge("generate_explanation", END)
    workflow.add_edge("handle_vague_jd", END)
    workflow.add_edge("handle_error", END)

    return workflow.compile()


class GraphOrchestrator:
    """LangGraph-based orchestrator for resume screening."""

    SUPPORTED_FORMATS = ['.pdf', '.docx']

    def __init__(self):
        self.graph = build_screening_graph()

    def run(self, resume_path: str, jd_path: str) -> dict:
        """
        Run the screening workflow.

        Args:
            resume_path: Path to resume (PDF or DOCX)
            jd_path: Path to job description text file

        Returns:
            Screening result with match_score, recommendation, etc.
        """
        # Pre-validation before invoking graph
        if not os.path.exists(resume_path):
            return _create_error_output(f"Resume file not found: {resume_path}")

        if not os.path.exists(jd_path):
            return _create_error_output(f"Job description file not found: {jd_path}")

        ext = os.path.splitext(resume_path)[1].lower()
        if ext not in self.SUPPORTED_FORMATS:
            return _create_error_output(
                f"Unsupported resume format: {ext}. Supported formats: {', '.join(self.SUPPORTED_FORMATS)}"
            )

        initial_state: ScreeningState = {
            "resume_path": resume_path,
            "jd_path": jd_path
        }

        # Execute the graph
        final_state = self.graph.invoke(initial_state)

        return final_state.get("final_output", {})
