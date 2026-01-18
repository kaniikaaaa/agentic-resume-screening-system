# Agentic Resume Screening System

AI-powered multi-agent system that evaluates resumes against job descriptions and recommends hiring actions with clear reasoning.

## Quick Start

```bash
git clone <repo-url>
cd agentic-resume-screening-system
python -m venv venv && source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Setup environment (optional - works without API key using rule-based fallback)
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY (free from https://aistudio.google.com/apikey)

# Run
python -m tests.test_parsers
```

---

## Architecture Overview

```
Input: Resume (PDF/DOCX) + Job Description (TXT)
                    │
                    ▼
            ┌───────────────┐
            │  Orchestrator │ (LangGraph)
            └───────┬───────┘
                    │
        ┌───────────┴───────────┐
        ▼                       ▼
┌───────────────┐       ┌───────────────┐
│ ResumeParser  │       │   JDParser    │
└───────┬───────┘       └───────┬───────┘
        │                       │
        └───────────┬───────────┘
                    ▼
            ┌───────────────┐
            │  SkillMatch   │
            └───────┬───────┘
                    ▼
            ┌───────────────┐
            │  Experience   │
            └───────┬───────┘
                    ▼
            ┌───────────────┐
            │   Decision    │──── Vague JD? ────► Human Review
            │               │──── Low Conf? ────► Human Review
            └───────┬───────┘
                    ▼
            ┌───────────────┐
            │  Explanation  │
            └───────┬───────┘
                    ▼
            Final JSON Output
```

**Decision Points:**
- Vague JD detected → routes to manual review
- Low confidence score → flags for human review
- Experience mismatch → different recommendation path

---

## Agent Design

| Agent | Responsibility | State Passed |
|-------|----------------|--------------|
| **ResumeParser** | Extract skills, experience from PDF/DOCX | `{skills, experience_years, projects}` |
| **JDParser** | Extract requirements from JD | `{required_skills, experience_required, jd_clarity}` |
| **SkillMatch** | Compare candidate skills vs JD | `{score, matched_skills, missing_skills}` |
| **Experience** | Evaluate experience fit | `{score, status, reason}` |
| **Decision** | Make hiring recommendation | `{recommendation, confidence, requires_human}` |
| **Explanation** | Generate human-readable reasoning | `{reasoning_summary}` |

---

## Prompt Design

We use two focused LLM prompts rather than one massive prompt:

**Resume Extraction Prompt:**
```
You are an AI recruiter assistant.
Extract structured data from the resume below.
Return ONLY valid JSON: {skills: [], experience_years: N, projects: []}
```

**JD Extraction Prompt:**
```
You are an AI recruiter assistant.
Extract structured data from the job description below.
Return ONLY valid JSON: {required_skills: [], experience_required: {min, max}, jd_clarity: "clear"|"vague"}
```

**Why this design:**
- Separate prompts = easier debugging and iteration
- Strict JSON output = reliable parsing
- "ONLY valid JSON" = reduces hallucinated text
- Clear role ("recruiter assistant") = focused responses

---

## Sample Outputs

**Strong Candidate + Standard JD:**
```json
{
  "match_score": 0.96,
  "recommendation": "Proceed to interview",
  "requires_human": false,
  "confidence": 0.9,
  "reasoning_summary": "Strong skill alignment. Candidate matches most required skills such as celery, fastapi, django. Candidate experience (3 years) matches JD range (2-4 years)"
}
```

**Weak Candidate + Standard JD:**
```json
{
  "match_score": 0.65,
  "recommendation": "Reject",
  "requires_human": false,
  "confidence": 0.75,
  "reasoning_summary": "Weak skill match. Candidate is missing many core skills like celery, restful, microservices."
}
```

**Any Candidate + Vague JD:**
```json
{
  "match_score": 0.0,
  "recommendation": "Manual Review Required",
  "requires_human": true,
  "confidence": 0.3,
  "reasoning_summary": "Job description is too vague to make an automated decision. Missing clear technical requirements."
}
```

---

## Error Handling

| Scenario | Behavior |
|----------|----------|
| File not found | Returns error with `requires_human: true` |
| Unsupported format | Returns error explaining supported formats |
| PDF parse failure | Graceful error, flags for human review |
| Vague JD | Routes to manual review (not a failure) |
| LLM fails/quota | Falls back to rule-based extraction |

---

## Trade-offs & Assumptions

**What we chose:**
- **Rule-based fallback** over LLM-only: Ensures system always works, even offline
- **Exact skill matching** over semantic: Simpler, debuggable, no vector DB needed
- **LangGraph** for orchestration: Conditional routing, clean state management
- **Single resume** focus: Clarity over batch processing for MVP

**What we skipped:**
- Semantic skill matching (would need embeddings + vector DB)
- Resume similarity scoring
- API endpoints (FastAPI scaffold exists but not wired)

---

## Future Improvements

1. **Semantic Skill Matching**: Embeddings to match "ReactJS" with "React"
2. **Batch Processing**: Multiple resumes in parallel
3. **Confidence Calibration**: Learn from recruiter feedback
4. **REST API**: Wire up FastAPI endpoints

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GEMINI_API_KEY` | - | Google Gemini API key (optional) |
| `USE_LLM` | `true` | Set `false` to force rule-based mode |
| `USE_LANGGRAPH` | `true` | Set `false` to use original orchestrator |

---

> This repository is private per Pitcrew guidelines. Reviewer access via @pitcrew-hiring collaborator.
