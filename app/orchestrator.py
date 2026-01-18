import os
import pdfplumber

from app.agents.resume_parser import ResumeParserAgent
from app.agents.jd_parser import JDParserAgent
from app.agents.skill_match_agent import SkillMatchAgent
from app.agents.experience_agent import ExperienceAgent
from app.agents.decision_agent import DecisionAgent
from app.agents.explanation_agent import ExplanationAgent


class Orchestrator:
    SUPPORTED_FORMATS = ['.pdf', '.docx']

    def __init__(self):
        self.resume_agent = ResumeParserAgent()
        self.jd_agent = JDParserAgent()
        self.skill_agent = SkillMatchAgent()
        self.experience_agent = ExperienceAgent()
        self.decision_agent = DecisionAgent()
        self.explanation_agent = ExplanationAgent()

    def _create_error_response(self, message: str) -> dict:
        """Create a standardized error response that flags for human review."""
        return {
            "match_score": 0.0,
            "recommendation": "Manual Review Required",
            "requires_human": True,
            "confidence": 0.0,
            "reasoning_summary": message,
            "data_source": "error"
        }

    def extract_pdf_text(self, path: str) -> str:
        """Extract text from PDF file."""
        text = ""
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text

    def extract_docx_text(self, path: str) -> str:
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

    def run(self, resume_path: str, jd_path: str) -> dict:
        """
        Run the resume screening pipeline.

        Args:
            resume_path: Path to resume file (PDF or DOCX)
            jd_path: Path to job description text file

        Returns:
            Screening result with match_score, recommendation, etc.
        """
        # Validate resume file exists
        if not os.path.exists(resume_path):
            return self._create_error_response(f"Resume file not found: {resume_path}")

        # Validate JD file exists
        if not os.path.exists(jd_path):
            return self._create_error_response(f"Job description file not found: {jd_path}")

        # Validate resume file format
        ext = os.path.splitext(resume_path)[1].lower()
        if ext not in self.SUPPORTED_FORMATS:
            return self._create_error_response(
                f"Unsupported resume format: {ext}. Supported formats: {', '.join(self.SUPPORTED_FORMATS)}"
            )

        # Extract resume text with error handling
        try:
            if ext == '.pdf':
                resume_text = self.extract_pdf_text(resume_path)
            else:
                resume_text = self.extract_docx_text(resume_path)
        except Exception as e:
            return self._create_error_response(f"Failed to parse resume: {str(e)}")

        # Validate extracted text
        if not resume_text or not resume_text.strip():
            return self._create_error_response("Resume file appears to be empty or could not be read.")

        # Read JD file with error handling
        try:
            with open(jd_path, "r", encoding="utf-8") as f:
                jd_text = f.read()
        except Exception as e:
            return self._create_error_response(f"Failed to read job description: {str(e)}")

        # Validate JD text
        if not jd_text or not jd_text.strip():
            return self._create_error_response("Job description file appears to be empty.")

        # Run the agent pipeline
        resume_data = self.resume_agent.parse(resume_text)
        jd_data = self.jd_agent.parse(jd_text)

        skill_result = self.skill_agent.evaluate(resume_data, jd_data)
        experience_result = self.experience_agent.evaluate(resume_data, jd_data)
        decision_result = self.decision_agent.decide(skill_result, experience_result, jd_data)

        explanation = self.explanation_agent.generate(
            resume_data, jd_data, skill_result, experience_result, decision_result
        )

        return {
            "match_score": decision_result["match_score"],
            "recommendation": decision_result["recommendation"],
            "requires_human": decision_result["requires_human"],
            "confidence": decision_result["confidence"],
            "reasoning_summary": explanation,
            "data_source": resume_data.get("source", "unknown")
        }
