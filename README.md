# Agentic Resume Screening

6-agent LangGraph pipeline that parses a job description and a batch of resumes, scores fit across skills and experience, and produces a decision with an audit-trail explanation. Low-confidence classifications drop to a rule-based fallback instead of guessing.

## Stack

Python · LangGraph · Google Gemini · FastAPI · Pydantic · pdfplumber · python-docx

## Architecture

```
JD Parser ─┐
           ├─> Skill Match ─┐
Resume ────┘                ├─> Decision ─> Explanation
           Experience ──────┘
```

Each node is a LangGraph agent. Conditional edges route low-confidence scores to a deterministic fallback before hitting the decision node.

## What's interesting here

- **Rule-based fallback on low confidence.** Any agent that returns a confidence score below the threshold is shadowed by a keyword + scoring heuristic; the graph picks whichever signal is stronger. No silent hallucinations in the decision.
- **Shared state via LangGraph's typed store.** All agents read and write a single `ScreeningState` Pydantic model, so adding an agent is one node + one edge, not a refactor.
- **FastAPI endpoints that return both decision and trace.** Every response includes the per-agent intermediate output, so reviewers can see why a candidate was shortlisted or rejected.

## Run locally

```bash
git clone https://github.com/kaniikaaaa/agentic-resume-screening-system.git
cd agentic-resume-screening-system

python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env   # add GOOGLE_API_KEY

uvicorn app.main:app --reload
# Docs: http://localhost:8000/docs
```

## Agents

| # | Agent | Job |
|---|---|---|
| 1 | JD Parser | Extracts required + nice-to-have skills, YoE, role tags |
| 2 | Resume Parser | Pulls skills, companies, roles, durations from PDF/DOCX |
| 3 | Skill Match | Weighted overlap + semantic similarity |
| 4 | Experience | Normalizes YoE, detects seniority level |
| 5 | Decision | Thresholded recommendation |
| 6 | Explanation | Generates human-readable rationale |

## License

MIT
