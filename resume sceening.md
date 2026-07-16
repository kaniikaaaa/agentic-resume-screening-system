# Agentic Resume Screening System - Project Overview & Interview Notes

## Project Summary

**What it does:** An AI-powered, agentic backend system that automatically evaluates candidate resumes against job descriptions, provides match scores, makes recommendations, and explains its reasoning in a transparent way.

**Problem it solves:** Hiring teams receive hundreds of resumes per role. Manual screening is time-consuming, inconsistent, and prone to bias. This system automates the initial screening phase by acting as an intelligent "hiring committee" made up of multiple specialized agents.

**Key differentiator:** Instead of a single monolithic scoring function, the system uses a **multi-agent architecture** where each agent specializes in one specific task (parsing, skill matching, experience evaluation, etc.), making decisions transparent and explainable.

---

## Architecture Overview

### High-Level Flow

```
Resume (PDF/TXT) + Job Description (TXT)
         ↓
   ┌─────────────────┐
   │  Orchestrator   │ (Coordinator that manages the workflow)
   └────────┬────────┘
            ↓
   ┌─────────────────────────────────────┐
   │ 1. Parse Resume (ResumeParserAgent) │
   │ 2. Parse Job Description (JDParser) │
   └─────────────┬───────────────────────┘
                 ↓
   ┌─────────────────────────────────────┐
   │ 3. Skill Matching (SkillMatchAgent) │
   │ 4. Experience Check (ExperienceAgent)
   └─────────────┬───────────────────────┘
                 ↓
   ┌─────────────────────────────────────┐
   │ 5. Make Decision (DecisionAgent)    │
   │ 6. Generate Explanation (Expl.Agent)│
   └─────────────┬───────────────────────┘
                 ↓
        Final Recommendation
        (Score, Decision, Reasoning)
```

### Key Agents

| Agent | Responsibility |
|-------|-----------------|
| **ResumeParserAgent** | Extracts structured data from resume (skills, experience years, contact info, etc.) using LLM |
| **JDParserAgent** | Extracts structured data from job description (required skills, experience range, etc.) |
| **SkillMatchAgent** | Compares candidate skills vs. required skills; calculates % match |
| **ExperienceAgent** | Evaluates if candidate's years of experience fit JD requirements |
| **DecisionAgent** | Combines skill and experience scores; applies business logic to make final recommendation |
| **ExplanationAgent** | Generates human-readable reasoning for the decision |

---

## Decision Logic & Scoring

### Scoring Formula

```
Final Score = (0.6 × Skill Score) + (0.4 × Experience Score)
```

**Weights:** Skills are weighted at 60% (more important than experience) and experience at 40%.

### Decision Thresholds

| Final Score | Recommendation | Requires Human Review |
|-------------|-----------------|----------------------|
| ≥ 85 | ✅ Proceed to Interview | No (Confidence: 90%) |
| 65-84 | ⚠️ Needs Manual Review | Yes (Confidence: 60%) |
| < 65 | ❌ Reject | No (Confidence: 75%) |
| JD Vague | Manual Review Required | Yes (Confidence: 30%) |

### Skill Matching Logic

- **Matched Skills:** Count intersection of resume skills and JD required skills
- **Missing Skills:** Skills required but candidate lacks
- **Extra Skills:** Candidate has skills not required (bonus, but not scored)
- **Score Calculation:** `(Matched Skills / Required Skills) × 100`

### Experience Evaluation Logic

| Scenario | Score | Status |
|----------|-------|--------|
| Perfect fit (within range) | 100 | Perfect Fit |
| Under-qualified (< min) | 30 | Under-qualified |
| Over-qualified (> max) | 70 | Over-qualified |
| Meets minimum ("4+ years") | 100 | Qualified |
| JD doesn't specify experience | 50 | Unknown |

---

## Technical Stack

| Component | Technology |
|-----------|------------|
| **Framework** | FastAPI (REST API) |
| **PDF Processing** | pdfplumber |
| **LLM** | Google Generative AI (Gemini) |
| **Data Validation** | Pydantic |
| **Language** | Python 3.x |

### Dependencies
```
fastapi, uvicorn, pydantic, python-multipart, langchain, pdfplumber, google-genai
```

---

## Project Structure

```
agentic-resume-screening-system/
├── app/
│   ├── main.py                    # FastAPI app entry point
│   ├── orchestrator.py            # Orchestrator class & workflow
│   ├── agents/
│   │   ├── resume_parser.py       # Parse resume
│   │   ├── jd_parser.py           # Parse job description
│   │   ├── skill_match_agent.py   # Skill matching logic
│   │   ├── experience_agent.py    # Experience evaluation
│   │   ├── decision_agent.py      # Scoring & decision
│   │   ├── explanation_agent.py   # Generate reasoning
│   │   └── __init__.py
│   ├── services/
│   │   └── llm_service.py         # LLM interaction wrapper
│   └── __init__.py
├── data/
│   ├── jd_01_backend_python_standard.txt
│   ├── jd_02_senior_fintech_strict.txt
│   ├── jd_03_junior_flexible.txt
│   └── jd_04_vague_ambiguous.txt
├── tests/
│   ├── test_parsers.py            # Unit tests
│   └── __init__.py
├── requirements.txt               # Python dependencies
├── README.md                       # Project documentation
└── list_models.py                 # Utility to list available LLM models
```

---

## Example Workflow

**Input:**
- Resume: "Software Engineer with Python, Django, AWS. 5 years experience."
- JD: "Backend Engineer needed. Required: Python, PostgreSQL. 3-7 years experience."

**Processing:**
1. Parse resume → Skills: {Python, Django, AWS}, Experience: 5 years
2. Parse JD → Required Skills: {Python, PostgreSQL}, Experience Range: 3-7 years
3. Skill Match → Match: {Python} (1/2 = 50%)
4. Experience → Fits range 3-7 (Score: 100)
5. Decide → Final Score = (0.6 × 50) + (0.4 × 100) = 70
6. Recommend → "Needs manual review" (confidence: 60%)

**Output:**
```json
{
  "match_score": 0.7,
  "recommendation": "Needs manual review",
  "requires_human": true,
  "confidence": 0.6,
  "reasoning_summary": "Candidate has strong experience (5 yrs fits range) but is missing PostgreSQL..."
}
```

---

## Edge Cases Handled

| Edge Case | Handler | Decision |
|-----------|---------|----------|
| Vague JD (no clear requirements) | DecisionAgent | Manual Review (confidence: 30%) |
| Missing experience data | ExperienceAgent | Default score: 50 (Unknown) |
| Empty JD skill list | DecisionAgent | Manual Review Required |
| PDF parsing fails | Orchestrator | Error handling |
| Candidate over-qualified | ExperienceAgent | Still scoreable (70 points) |

---

## Interview Preparation Notes

### Key Talking Points

1. **Multi-Agent Architecture**
   - Explain why separate agents are better than monolithic approach
   - Agents are testable, maintainable, and each can be updated independently
   - Clear separation of concerns

2. **Explainability**
   - Why transparency matters in hiring
   - The system provides reasoning, not just a black-box score
   - Helps hiring team understand why a candidate was rejected/accepted

3. **Business Logic**
   - Why 60/40 weight split? (Skills weighted higher because they're more objective)
   - Why three recommendation buckets instead of binary? (Gray zone for human review)
   - How the system handles ambiguous/vague job descriptions

4. **Scalability Considerations**
   - Current design processes one resume at a time
   - Could be extended to batch processing
   - LLM calls could be cached for identical JDs

5. **Limitations & Future Improvements**
   - Depends on LLM quality for parsing (can hallucinate)
   - No semantic skill matching (exact string matching only currently)
   - Could add: soft skills evaluation, cultural fit, customizable weights

### Questions You Should Be Ready to Answer

**Technical Questions:**

Q: "How does the system ensure consistent parsing across different resume formats?"
A: It uses Google Generative AI (LLM) to parse resumes, which handles various formats better than regex. However, this introduces LLM hallucination risk, so results should be validated.

Q: "What happens if the LLM misunderstands a skill or experience?"
A: Currently, it would produce incorrect scoring. In production, you'd want: 1) confidence scores from LLM, 2) manual validation for edge cases, 3) user feedback loop to retrain.

Q: "Why weight skills at 60% and experience at 40%?"
A: Skills are more objective/verifiable than experience years. A junior with perfect skills beats a senior with outdated skills. But this is configurable.

Q: "How would you handle multiple-language resumes?"
A: Google Generative AI supports multiple languages natively, so it should work. Would need testing with different languages.

**Design Questions:**

Q: "How would you scale this for processing 1000 resumes?"
A: Add async API endpoints, batch processing, caching of parsed JDs, and queue management (Redis/RabbitMQ). Currently synchronous and single-threaded.

Q: "What if a hiring manager wants custom weights (e.g., 70% skills, 30% experience)?"
A: Add configurable weights to DecisionAgent. Store as part of job posting config. Could be database-driven.

Q: "How do you handle false negatives (rejecting good candidates)?"
A: The "Needs manual review" zone (65-85 score) catches borderline cases. Plus, the system shows reasoning, so hiring team can override.

**Code Review Questions:**

Q: "Why use Orchestrator pattern here?"
A: Decouples the workflow from individual agents. Easy to test, modify individual agents, and change the workflow order.

Q: "Is there error handling for malformed PDFs or job descriptions?"
A: Basic error handling exists, but could be improved with try-catch blocks, logging, and graceful degradation.

Q: "How do you test agent logic?"
A: `test_parsers.py` exists (could be expanded). Mock LLM responses, test with known inputs/outputs, edge cases.

### Red Flags to Address

- ❌ "This is just regex matching" → No, it uses LLM for intelligent parsing
- ❌ "This discriminates based on experience" → System is designed to handle edge cases fairly (over-qualified still scores 70)
- ❌ "No bias mitigation" → Worth mentioning that explainability helps catch bias; could add fairness checks

### Practice Answers

**"Walk us through how you'd add a new evaluation criterion (e.g., certifications)?"**

Answer:
1. Create a `CertificationsAgent` class following the same pattern
2. Extract required certifications in `JDParserAgent.parse()`
3. Extract candidate certifications in `ResumeParserAgent.parse()`
4. In `CertificationsAgent.evaluate()`, compare and score
5. Modify `DecisionAgent` to factor in cert score (e.g., new weight like 60% skills, 20% exp, 20% certs)
6. Update `ExplanationAgent` to mention cert match/miss
7. Test with sample data

**"What's the biggest limitation of this system?"**

Answer:
1. **LLM dependency:** Over-relies on LLM for parsing; garbage in = garbage out
2. **Exact string matching:** Skills aren't semantically compared ("Python" vs "Py" won't match)
3. **No model verification:** Doesn't validate if extracted data is correct
4. **Single-threaded:** Can't handle high volume
5. **No bias testing:** Doesn't measure/mitigate hiring bias

**"How would you approach adding semantic skill matching?"**

Answer:
1. Pre-process skills with embeddings (e.g., via word2vec, OpenAI embeddings)
2. Calculate cosine similarity between resume skills and required skills
3. Set a threshold (e.g., 0.8) to consider it a match
4. Update SkillMatchAgent to use similarity scores instead of exact matching
5. Test with common synonyms (e.g., "JS" ≈ "JavaScript", "SQL" ≈ "PostgreSQL")

---

## Files to Understand Before Interview

**Priority 1 (Critical):**
- [orchestrator.py](app/orchestrator.py) - Core workflow
- [decision_agent.py](app/agents/decision_agent.py) - Scoring logic
- [skill_match_agent.py](app/agents/skill_match_agent.py) - Skill matching

**Priority 2 (Important):**
- [experience_agent.py](app/agents/experience_agent.py) - Experience logic
- [main.py](app/main.py) - API setup
- [README.md](README.md) - Official documentation

**Priority 3 (Nice to know):**
- [resume_parser.py](app/agents/resume_parser.py) - Resume parsing
- [jd_parser.py](app/agents/jd_parser.py) - JD parsing
- [test_parsers.py](tests/test_parsers.py) - Test examples

---

## Strengths to Highlight

✅ **Multi-agent architecture** - Clean separation of concerns, easy to extend
✅ **Explainability** - Provides reasoning for decisions, not just scores
✅ **Handles edge cases** - Vague JDs, over/under qualified candidates, missing data
✅ **Configurable thresholds** - Business rules can be tuned without code changes
✅ **Scalable design** - Can add new evaluation criteria easily

---

## Areas for Improvement (Proactive Talking Points)

⚠️ **LLM reliability** - Would add confidence scores and validation
⚠️ **Error handling** - Could improve with better fallbacks and logging
⚠️ **Semantic skills** - Current matching is exact string-based; could use embeddings
⚠️ **Async/batch processing** - System is synchronous; would need refactor for scale
⚠️ **Bias testing** - Would add fairness metrics and demographic parity checks

---

## Quick Reference - Code Flow

```python
# High-level execution flow
orchestrator = Orchestrator()  # Initialize all agents

# Run evaluation
result = orchestrator.run(
    resume_path="resume.pdf",
    jd_path="job_description.txt"
)

# Result structure
{
    "match_score": 0.7,                    # 0-1 scale
    "recommendation": "Needs manual review",
    "requires_human": True,
    "confidence": 0.6,
    "reasoning_summary": "...",            # Explanation
    "data_source": "pdf"                   # Resume source
}
```

---

## Closing Talking Points

1. **Why this project matters:** Hiring is consequential—people's livelihoods depend on fair decisions. Building transparent, explainable systems is crucial.

2. **What you learned:** Multi-agent design, business logic implementation, handling uncertainty and edge cases, and why explainability is as important as accuracy.

3. **Future directions:** Semantic skill matching, feedback loops, bias mitigation, real-time updates, mobile app for hiring managers.

4. **What interested you most:** (Choose one based on the conversation—could be the reasoning chain, the architecture, or handling ambiguity).

---

**Last Updated:** Interview Preparation Guide
