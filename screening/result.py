"""The response contract, shared by both orchestrators.

Kept in one place so the linear and graph paths cannot drift into returning
different shapes for the same screening.
"""

SKILL_MATCH_NOT_RUN = {
    "score": 0,
    "matched_skills": [],
    "missing_skills": [],
    "extra_skills": [],
    "coverage": "0/0",
}

EXPERIENCE_NOT_RUN = {
    "score": 0,
    "status": "Not assessed",
    "reason": "Skipped — there was nothing to weigh the candidate against.",
}


def shape(resume_data: dict, jd_data: dict, skill_result: dict,
          experience_result: dict, decision_result: dict,
          explanation: str, trace: list[dict]) -> dict:
    skill_result = skill_result or SKILL_MATCH_NOT_RUN
    experience_result = experience_result or EXPERIENCE_NOT_RUN

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
        # An escalation reports 0.0 because it declined to score, not because
        # the candidate scored nothing. The interface needs to tell those apart
        # or it will libel the candidate.
        "scored": decision_result.get("reason") is None,
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
