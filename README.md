# Quorum — Agentic Resume Screening

A panel of specialised agents reads a resume against a job description, scores
the match, shows its working, and hands the case to a human when it shouldn't be
the one deciding.

Next.js front end, FastAPI agent pipeline. Deploys to Render as a single Docker
service, or to Vercel as a Next.js app plus a Python function.

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

### Two orchestrators

| `ORCHESTRATOR` | Behaviour |
|---|---|
| `linear` *(default)* | All six agents, in order, every time. |
| `graph` | The same panel wired as a LangGraph state graph, with conditional routing. |

The graph route branches: a role too vague to match against **skips SkillMatch
and Experience entirely** and goes straight to the escalation, because scoring a
candidate against nothing is wasted work whose only output would be a number the
`DecisionAgent` is about to discard. Skipped agents come back in the trace with
`status: "skipped"`, and the interface strikes them through — the route the case
took is visible, not buried.

Both return the identical shape (see [`screening/result.py`](screening/result.py)),
and a test asserts they reach the same verdict on every sample, so routing can
never change the answer — only the work done to reach it. `linear` is the default
because `langgraph` is a heavy import to pay for on every serverless cold start.

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
python -m pytest tests/   # 57 tests, no API key needed
```

---

## Deploying

Two supported targets. They differ only in how the interface reaches the API.

| | Render | Vercel |
|---|---|---|
| Shape | one Docker web service | Next.js + a Python serverless function |
| Interface | static export, served by FastAPI | served by Next |
| API reached via | same origin, no rewrite | `next.config.mjs` rewrite |
| Config | [`render.yaml`](render.yaml), [`Dockerfile`](Dockerfile) | [`vercel.json`](vercel.json) |

### Render

Render has no serverless functions, and its native Python runtime has no Node,
so the [`Dockerfile`](Dockerfile) builds the interface in a Node stage, exports
it to static files, and copies just those into a Python image. FastAPI then
serves the interface and the API from **one origin** — no second service, no
CORS.

1. Push to GitHub.
2. Render → **New** → **Blueprint** → pick this repo. It reads `render.yaml`
   and needs nothing else. (Or **New → Web Service** → Runtime **Docker**.)
3. *(Optional)* Add `GEMINI_API_KEY` under **Environment**. Without it the
   service runs deterministically rather than failing.

Health check is wired to `/api/py/health`.

> On Render's **free** plan the service sleeps after ~15 minutes idle, so the
> first request afterwards takes ~50s while it wakes. The screening itself is
> unaffected. A paid instance doesn't sleep.

Run the exact production image locally:

```bash
docker build -t quorum .
docker run --rm -p 8000:8000 -e GEMINI_API_KEY=... quorum
# http://localhost:8000
```

### Vercel

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

`multipart/form-data` — `resume` (PDF or DOCX, ≤5 MB) and `job_description`
(text). Format is decided by the file's magic number, not its extension, so a
mislabelled upload still reads correctly.

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

Errors return `{"detail": "..."}` with a status: `415` unsupported format,
`422` unreadable file or a job description under 40 characters, `413` too large.

### `GET /api/py/health`

Reports which mode the deploy is in, and why.

---

## Scoring

`0.6 × skill coverage + 0.4 × experience`, then:

| Score | Outcome | |
|---|---|---|
| ≥ 85 | Proceed to interview | closed automatically |
| 65–84 | Needs manual review | held for a recruiter |
| 60–64 | Needs manual review | **near miss** — held, confidence 0.5 |
| < 60 | Reject | closed automatically |

Skills are weighted higher because they're the more checkable signal. The
interface draws the bands on the score rail, so you can see why a
recommendation fell where it did rather than taking it on faith.

**Why the near-miss band.** With a bare cut at 65, a 65.0 reached a recruiter
and a 64.9 got an automated no — on a difference the scoring cannot resolve,
since one skill the parser misreads moves a candidate further than that. Worse,
the panel was contradicting itself: `ExperienceAgent` would report *"marginally
short"* while `DecisionAgent` rejected outright and set `requires_human: false`.
Scores in the 60–64 band are held instead, with the confidence dropped to 0.5
and the rationale saying which way it fell — a borderline no, not a solid maybe.

This doesn't abolish the cliff, it moves it to 60, where a rejection is one the
panel's own reasoning supports. A wrongly rejected candidate is the one error
nobody ever finds out about, so it's the one worth paying for.

---

## Layout

```
app/            Next.js App Router — the interface
components/     Masthead, Intake, Verdict, Trace
lib/            shared types, the agent roster, sample fixtures
api/index.py    FastAPI entry — serverless function on Vercel, and the
                whole server (interface included) on Render
Dockerfile      Node build stage -> Python runtime, for Render
render.yaml     Render Blueprint
vercel.json     Vercel function config
screening/      the agent pipeline (imported by api/index.py)
  agents/       one file per agent
  services/     Gemini client, document extraction, skill taxonomy
  orchestrator.py     linear route (default)
  graph_orchestrator.py  LangGraph route, conditional
public/samples/ synthetic resumes and roles — the interface's samples,
                and the tests' fixtures
tests/          57 deterministic tests
```

---

## Known limits

- **Text-based PDF and DOCX only.** Scanned resumes need OCR; the API says so
  with a `422` rather than silently scoring an empty file.
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
