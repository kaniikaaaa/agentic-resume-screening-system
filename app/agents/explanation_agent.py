class ExplanationAgent:
    def generate(self, resume_data, jd_data, skill_result, experience_result, decision_result):
        reasons = []

        # Skill reasoning
        skill_score = skill_result["score"]
        matched = skill_result["matched_skills"]
        missing = skill_result["missing_skills"]

        if skill_score >= 80:
            reasons.append(
                f"Strong skill alignment. Candidate matches most required skills such as {', '.join(matched[:4])}."
            )
        elif 50 <= skill_score < 80:
            reasons.append(
                f"Partial skill match. Candidate matches {len(matched)} required skills but is missing {', '.join(missing[:3])}."
            )
        else:
            reasons.append(
                f"Weak skill match. Candidate is missing many core skills like {', '.join(missing[:3])}."
            )

        # Experience reasoning
        reasons.append(experience_result["reason"])

        # JD clarity reasoning
        if not jd_data.get("required_skills"):
            reasons.append(
                "The job description is vague or missing technical requirements, so automated evaluation is unreliable."
            )

        # Combine into one paragraph
        reasoning_summary = " ".join(reasons)

        return reasoning_summary
