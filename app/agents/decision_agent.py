class DecisionAgent:
    def decide(self, skill_result, experience_result, jd_data):
        skill_score = skill_result["score"]          # 0–100
        exp_score = experience_result["score"]       # 0–100

        # Weighted final score (skills > experience thoda zyada important)
        final_score = (0.6 * skill_score) + (0.4 * exp_score)
        final_score = round(final_score, 2)

        # Default flags
        requires_human = False
        recommendation = "Reject"

        # JD vague case
        if jd_data.get("required_skills") is None or len(jd_data.get("required_skills")) == 0:
            return {
                "final_score": 0.0,
                "match_score": 0.0,
                "recommendation": "Manual Review Required",
                "requires_human": True,
                "confidence": 0.3,
                "reason": "Job description is too vague to make an automatic decision."
            }

        # Decision thresholds
        if final_score >= 80:
            recommendation = "Proceed to interview"
            confidence = 0.9
        elif 60 <= final_score < 80:
            recommendation = "Needs manual review"
            requires_human = True
            confidence = 0.6
        else:
            recommendation = "Reject"
            confidence = 0.75

        return {
            "final_score": final_score,
            "match_score": round(final_score / 100, 2),   # As per Pitcrew format (0–1)
            "recommendation": recommendation,
            "requires_human": requires_human,
            "confidence": confidence
        }
