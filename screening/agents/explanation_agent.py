class ExplanationAgent:
    """Writes the plain-language rationale behind the decision.

    Reads only the other agents' outputs, so the summary can never claim
    something the scores don't support.
    """

    def generate(self, resume_data: dict, jd_data: dict, skill_result: dict,
                 experience_result: dict, decision_result: dict) -> str:
        # Escalations already carry their own reason; anything else would be
        # reasoning about a score the DecisionAgent refused to trust.
        if decision_result.get("reason"):
            return decision_result["reason"]

        parts = [
            _skills_sentence(skill_result),
            experience_result["reason"],
        ]

        if decision_result["requires_human"]:
            parts.append("Flagged for a recruiter to confirm before any action is taken.")

        if resume_data.get("source") == "rule_based":
            parts.append(
                "Parsed in deterministic mode, so skills were matched against a "
                "fixed vocabulary rather than read in context."
            )

        return " ".join(p for p in parts if p)


def _skills_sentence(skill_result: dict) -> str:
    score = skill_result["score"]
    matched = skill_result["matched_skills"]
    missing = skill_result["missing_skills"]

    if score >= 80:
        text = f"Strong skill alignment ({skill_result['coverage']} required skills)"
        if matched:
            text += f", including {_list(matched[:4])}"
        if missing:
            text += f". Missing {_list(missing[:3])}"
        return text + "."

    if score >= 50:
        return (
            f"Partial skill match ({skill_result['coverage']} required skills). "
            f"Has {_list(matched[:3])} but is missing {_list(missing[:3])}."
        )

    if matched:
        return (
            f"Weak skill match ({skill_result['coverage']} required skills). "
            f"Only {_list(matched[:3])} overlap, with {_list(missing[:4])} absent."
        )

    return f"No overlap with the required skills — {_list(missing[:4])} are all absent."


def _list(items: list[str]) -> str:
    """Join for prose: "a", "a and b", "a, b and c"."""
    if not items:
        return "none"
    if len(items) == 1:
        return items[0]
    return f"{', '.join(items[:-1])} and {items[-1]}"
