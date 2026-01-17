# Agentic Resume Screening System

An AI-powered, agentic backend system that evaluates candidate resumes against job descriptions, explains its reasoning, and recommends the next hiring action.  
This project is built as a response to the Pitcrew Backend Engineering Assignment and focuses on clarity of thought, explainability, and multi-agent design rather than UI or deployment.

---

## Problem Statement

Hiring teams receive hundreds of resumes per role. Manually screening them is slow and inconsistent.  
This system acts like a “hiring committee” made of multiple agents, where each agent specializes in one task:

- Reading resumes  
- Understanding job requirements  
- Comparing skills  
- Evaluating experience  
- Making decisions  
- Explaining reasoning  

Instead of a single monolithic function, decisions emerge from collaboration between agents.

---

## Architecture Overview

 ┌─────────────────────┐
            │     Orchestrator    │
            └─────────┬───────────┘
                      │
    ┌─────────────────┼─────────────────┐
    │                 │                 │
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ ResumeParser │ │ JDParser │ │ Error Handling │
│ Agent │ │ Agent │ │ & Validation │
└────────┬────────┘ └────────┬────────┘ └─────────────────┘
│ │
▼ ▼
Structured Resume Structured JD
│ │
└────────────┬──────┘
▼
┌─────────────────┐
│ SkillMatchAgent │
└────────┬────────┘
▼
┌────────────────────┐
│ ExperienceAgent │
└────────┬───────────┘
▼
┌────────────────────┐
│ DecisionAgent │
└────────┬───────────┘
▼
┌────────────────────┐
│ ExplanationAgent │
└────────┬───────────┘
▼


---

## Agents and Responsibilities

| Agent Name | Responsibility |
|------------|---------------|
| ResumeParserAgent | Reads resume PDFs and extracts raw text, skills, and experience |
| JDParserAgent | Reads job descriptions and extracts required skills and experience ranges |
| SkillMatchAgent | Compares resume skills with JD requirements |
| ExperienceAgent | Evaluates candidate experience against JD experience |
| DecisionAgent | Combines skill and experience scores to make a hiring decision |
| ExplanationAgent | Generates human-readable reasoning |
| Orchestrator | Coordinates all agents and produces final output |

---

## Agentic Design Philosophy

This system is agentic because:

- Each agent has a **single clear responsibility**
- Agents **pass structured data** to one another
- Decisions are made at multiple intermediate stages
- The system handles uncertainty and flags cases for human review
- State evolves as the pipeline progresses

What we avoided:

- One giant function doing everything
- One massive LLM prompt
- A blind linear pipeline with no branching
- Keyword-only matching without reasoning

---

## Input

1. Resume  
   - Format: PDF  
   - Example: `resume_01_priya_sharma.pdf`

2. Job Description  
   - Format: TXT  
   - Example: `jd_01_backend_python_standard.txt`

---

## Output (Pitcrew Format)

```json
{
  "match_score": 0.94,
  "recommendation": "Proceed to interview",
  "requires_human": false,
  "confidence": 0.9,
  "reasoning_summary": "Strong skill alignment. Candidate matches most required skills such as python, django, fastapi, postgresql. Candidate experience (3 years) matches JD range (2-4 years)."
}

| Field             | Meaning                               |
| ----------------- | ------------------------------------- |
| match_score       | Overall match from 0.0 to 1.0         |
| recommendation    | Hiring action                         |
| requires_human    | Whether recruiter should double-check |
| confidence        | How confident the system is           |
| reasoning_summary | Explainable decision rationale        |

How Agents Pass State

ResumeParserAgent → resume_data

{
  "skills": [...],
  "experience_years": 3,
  "raw_text": "..."
}


JDParserAgent → jd_data

{
  "required_skills": [...],
  "experience_required": {"min": 2, "max": 4}
}


SkillMatchAgent → skill_result

{
  "score": 90,
  "matched_skills": [...],
  "missing_skills": [...]
}


ExperienceAgent → experience_result

{
  "score": 100,
  "status": "Perfect Fit",
  "reason": "Candidate experience (3 years) matches JD range (2-4 years)"
}


DecisionAgent → decision_result

{
  "final_score": 94.0,
  "match_score": 0.94,
  "recommendation": "Proceed to interview",
  "requires_human": false,
  "confidence": 0.9
}


ExplanationAgent → reasoning_summary

| Scenario              | System Behavior          |
| --------------------- | ------------------------ |
| Vague JD              | Manual Review Required   |
| Junior candidate      | Needs manual review      |
| Parsing failure       | Graceful error handling  |
| Low confidence cases  | Human-in-the-loop        |
| Overconfident scoring | Avoided using thresholds |

Why Rule-Based First?

Trade-offs:

Deterministic

Easy to debug

Explainable

Fast execution

No dependency on paid APIs

With more time:

Use LLMs (Gemini/OpenAI) for extraction

Use embeddings for semantic skill matching

Resume similarity scoring

Feedback loop from recruiter decisions

Setup Instructions
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -m tests.test_parsers

Sample Scenarios Covered
Case	Behavior
Strong backend candidate	Auto-approve
Frontend candidate	Reject
Career switcher	Human review
Vague JD	Manual review
Future Improvements

LLM-powered parsing

Resume embeddings + vector similarity

Batch resume processing

Web UI dashboard

Confidence calibration using historical data

Final Thoughts

This system prioritizes:

Clear reasoning

Multi-agent collaboration

Cautious automation

Human-in-the-loop design

Transparent decision-making

Which directly aligns with Pitcrew’s philosophy of explainable, trustworthy AI systems.