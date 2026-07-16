SKILL_WEIGHT = 0.6
EXPERIENCE_WEIGHT = 0.4

INTERVIEW_THRESHOLD = 85
REVIEW_THRESHOLD = 65


class DecisionAgent:
    """Combines the skill and experience scores into a hiring action.

    Weighted toward skills, and biased to hand the case to a human whenever the
    inputs themselves are weak — a confident-looking score computed from a
    vague JD or an unparsed resume is worse than no score.
    """

    def decide(self, skill_result: dict, experience_result: dict, jd_data: dict,
               resume_data: dict | None = None) -> dict:
        resume_data = resume_data or {}

        if jd_data.get("jd_clarity") == "vague" or not jd_data.get("required_skills"):
            return _escalate(
                "The job description does not define concrete requirements, so an "
                "automated match would not mean anything.",
                confidence=0.3,
            )

        if not resume_data.get("skills"):
            return _escalate(
                "No skills could be extracted from the resume, so there is nothing "
                "to match against the role.",
                confidence=0.25,
            )

        final_score = round(
            SKILL_WEIGHT * skill_result["score"]
            + EXPERIENCE_WEIGHT * experience_result["score"],
            2,
        )

        if final_score >= INTERVIEW_THRESHOLD:
            recommendation, requires_human, confidence = "Proceed to interview", False, 0.9
        elif final_score >= REVIEW_THRESHOLD:
            recommendation, requires_human, confidence = "Needs manual review", True, 0.6
        else:
            recommendation, requires_human, confidence = "Reject", False, 0.75

        # An unknown experience requirement contributes a neutral 50 to the
        # score; that guess shouldn't be laundered into a confident verdict.
        if experience_result.get("status") == "Unknown" and not requires_human:
            requires_human = True
            confidence = min(confidence, 0.55)

        return {
            "final_score": final_score,
            "match_score": round(final_score / 100, 2),
            "recommendation": recommendation,
            "requires_human": requires_human,
            "confidence": confidence,
            "reason": None,
        }


def _escalate(reason: str, confidence: float) -> dict:
    return {
        "final_score": 0.0,
        "match_score": 0.0,
        "recommendation": "Manual review required",
        "requires_human": True,
        "confidence": confidence,
        "reason": reason,
    }
