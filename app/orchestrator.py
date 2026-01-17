from app.agents.resume_parser import ResumeParserAgent
from app.agents.jd_parser import JDParserAgent
from app.agents.skill_match_agent import SkillMatchAgent
from app.agents.experience_agent import ExperienceAgent
from app.agents.decision_agent import DecisionAgent
from app.agents.explanation_agent import ExplanationAgent
import pdfplumber

class Orchestrator:
    def __init__(self):
        self.resume_agent = ResumeParserAgent()
        self.jd_agent = JDParserAgent()
        self.skill_agent = SkillMatchAgent()
        self.experience_agent = ExperienceAgent()
        self.decision_agent = DecisionAgent()
        self.explanation_agent = ExplanationAgent()

    def extract_pdf_text(self, path):
        text = ""
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text

    def run(self, resume_path: str, jd_path: str):
        resume_text = self.extract_pdf_text(resume_path)

        with open(jd_path, "r", encoding="utf-8") as f:
            jd_text = f.read()

        # LLM / Hybrid parsing
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
