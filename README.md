# Quorum — Agentic Resume Screening

A panel of specialised agents reads a resume against a job description, scores
the match, shows its working, and hands the case to a human when it shouldn't be
the one deciding.

Next.js front end, FastAPI agent pipeline, both deployed to Vercel as one
project.

---

## Why it's built this way

A single "score this resume" prompt gives you a number nobody can argue with.
This splits the job across six agents, each with one responsibility and a
structured hand-off, so every part of the verdict traces back to the agent that
produced it.

| Agent | Responsibility |
|---|---|
| `ResumeParser` | Resume text → skills, years of experience, projects |
| `JDParser` | Job description → required skills, experience band, clarity |
| `SkillMatch` | Coverage of the required skills |
| `Experience` | Years served against the band the role asks for |
| `Decision` | Weighs the signals; abstains when the inputs are too weak |
| `Explanation` | States the reasoning in terms a recruiter can argue with |

The `Orchestrator` runs them in order and returns the intermediate outputs
alongside the verdict, which is what the interface renders.

### The design decision that matters most

**The system abstains rather than guessing.** A vague job description, or a
resume it could not read, produces a `Manual review required` — not a confident
number computed from nothing. The interface renders that as `—`, never `0`,
because a zero would read as "bad candidate" when it means "we didn't judge".

Escalation triggers:

- the role names fewer than two concrete technologies
- no skills could be extracted from the resume
- the role states no experience requirement (a neutral score would otherwise be
  laundered into a confident verdict)

---

## Two modes

| | Skills read by | Needs a key |
|---|---|---|
| **LLM mode** (default when `GEMINI_API_KEY` is set) | Gemini, in context | yes |
| **Deterministic mode** (automatic fallback) | a fixed vocabulary in [`screening/services/taxonomy.py`](screening/services/taxonomy.py) | no |

Deterministic mode is a real fallback, not a stub: it extracts skills, reads
experience from stated totals or employment dates, and screens end to end. If
the key is missing, the quota is spent, or the model returns something
unparseable, the pipeline degrades per-agent and keeps going. **The app is fully
functional deployed without any key** — it just reads less well.

The vocabulary does two jobs. It powers the fallback, and it canonicalises
skills in *both* modes: a resume saying `PostgreSQL` has to match a role asking
for `postgres`. Comparing raw strings under-reported every score.

It also refuses to take credit for aspirations — `Currently learning Django`
does not make Django a skill, and a degree's date range (`2014 - 2018`) is not
work experience.

---

## Running it

Needs Node 18+ and Python 3.10+ (Vercel's runtime defaults to 3.12).

```bash
npm install
pip install -r requirements.txt

cp .env.example .env      # optional — add GEMINI_API_KEY for LLM mode
```

Two processes, because the front end proxies to the Python app in development:

```bash
npm run dev:api           # FastAPI on :8000
npm run dev               # Next.js on :3000
```

Open <http://localhost:3000>. The interface ships with sample candidates and
roles, so it works on a cold start with nothing to upload.

```bash
python -m pytest tests/   # 36 tests, no API key needed
```

---

## Deploying to Vercel

The repo is already configured — Next.js and the Python function deploy together
as one project.

1. Push to GitHub.
2. Import the repo at [vercel.com/new](https://vercel.com/new). Leave the
   framework preset as **Next.js**; it detects everything.
3. *(Optional)* Add `GEMINI_API_KEY` under **Settings → Environment Variables**
   for LLM mode. Without it the deploy runs deterministically.
4. Deploy.

No other configuration. [`vercel.json`](vercel.json) allows the function 60s and
1 GB, which covers a cold start plus two Gemini calls.

### How the two halves connect

`next.config.mjs` rewrites `/api/py/*`. In development it proxies to
`127.0.0.1:8000`; in production Vercel routes it to the function in
[`api/`](api/), which receives the original path — hence the `/api/py` prefix on
the FastAPI routes.

Live API reference: `/api/py/docs`.

---

## API

### `POST /api/py/screen`

`multipart/form-data` — `resume` (PDF, ≤5 MB) and `job_description` (text).

```jsonc
{
  "match_score": 0.93,          // 0–1
  "recommendation": "Proceed to interview",
  "requires_human": false,
  "confidence": 0.9,
  "reasoning_summary": "Strong skill alignment (8/9 required skills)…",

  "scored": true,               // false when the panel abstained
  "mode": "rule_based",         // llm | rule_based | mixed
  "final_score": 93.4,          // 0–100
  "candidate":   { "skills": ["..."], "experience_years": 3, "source": "..." },
  "role":        { "required_skills": ["..."], "experience_required": {}, "clarity": "clear" },
  "skill_match": { "score": 89, "matched_skills": ["..."], "missing_skills": ["..."], "coverage": "8/9" },
  "experience":  { "score": 100, "status": "Fit", "reason": "..." },
  "trace":       [{ "agent": "ResumeParser", "duration_ms": 12, "source": "rule_based" }]
}
```

The first five fields are the assignment's contract, unchanged. Everything below
`scored` is what the interface renders.

Errors return `{"detail": "..."}` with a status: `415` not a PDF, `422`
unreadable PDF or a job description under 40 characters, `413` too large.

### `GET /api/py/health`

Reports which mode the deploy is in, and why.

---

## Scoring

`0.6 × skill coverage + 0.4 × experience`, then:

| Score | Outcome |
|---|---|
| ≥ 85 | Proceed to interview |
| 65–84 | Needs manual review |
| < 65 | Reject |

Skills are weighted higher because they're the more checkable signal. The
interface draws both thresholds on the score rail, so you can see why a
recommendation fell where it did rather than taking it on faith.

---

## Layout

```
app/            Next.js App Router — the interface
components/     Masthead, Intake, Verdict, Trace
lib/            shared types, the agent roster, sample fixtures
api/index.py    FastAPI entry — the Vercel serverless function
screening/      the agent pipeline (imported by api/index.py)
  agents/       one file per agent
  services/     Gemini client, PDF extraction, skill taxonomy
public/samples/ synthetic resumes and roles — the interface's samples,
                and the tests' fixtures
tests/          36 deterministic tests
```

---

## Known limits

- **Text-based PDFs only.** Scanned resumes need OCR; the API says so with a
  `422` rather than silently scoring an empty file.
- **Deterministic mode can't infer.** It matches a fixed vocabulary, so a skill
  described in words it doesn't know is invisible. LLM mode covers this.
- **Section heuristics assume conventional resumes.** Excluding education dates
  relies on a recognisable `EDUCATION` heading.
- **No persistence.** Each screening is a single stateless request; nothing is
  stored.
- **English only.**

## Worth building next

- Weight required skills by how central they are, instead of counting them equally
- Embeddings for semantic matching, so unknown-but-adjacent skills count
- Batch screening across a candidate pool, ranked
- Calibrate the thresholds against recruiters' actual decisions

---

The sample resumes under `public/samples/` are synthetic and committed
deliberately, so the demo and the tests both work on a fresh clone.
