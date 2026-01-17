from app.agents.resume_parser import ResumeParserAgent
from app.agents.jd_parser import JDParserAgent
from app.agents.skill_match_agent import SkillMatchAgent
from app.agents.experience_agent import ExperienceAgent
from app.agents.decision_agent import DecisionAgent
from app.agents.explanation_agent import ExplanationAgent


class Orchestrator:
    def __init__(self):
        self.resume_agent = ResumeParserAgent()
        self.jd_agent = JDParserAgent()
        self.skill_agent = SkillMatchAgent()
        self.experience_agent = ExperienceAgent()
        self.decision_agent = DecisionAgent()
        self.explanation_agent = ExplanationAgent()

    def run(self, resume_path: str, jd_path: str):
        # Step 1: Parse inputs
        resume_data = self.resume_agent.parse(resume_path)
        jd_data = self.jd_agent.parse(jd_path)

        # Step 2: Evaluate
        skill_result = self.skill_agent.evaluate(resume_data, jd_data)
        experience_result = self.experience_agent.evaluate(resume_data, jd_data)

        # Step 3: Decision
        decision_result = self.decision_agent.decide(
            skill_result, experience_result, jd_data
        )

        # Step 4: Explanation
        explanation = self.explanation_agent.generate(
            resume_data,
            jd_data,
            skill_result,
            experience_result,
            decision_result
        )

        # Final Pitcrew output format
        final_output = {
            "match_score": decision_result["match_score"],
            "recommendation": decision_result["recommendation"],
            "requires_human": decision_result["requires_human"],
            "confidence": decision_result["confidence"],
            "reasoning_summary": explanation
        }

        return final_output
