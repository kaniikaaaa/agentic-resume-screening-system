"""FastAPI entry point.

Deployed as a single Vercel serverless function; `next.config.mjs` rewrites
/api/py/* here. Routes carry the /api/py prefix because Vercel forwards the
original request path to the function.
"""

import sys
from pathlib import Path

# The function's working directory is the bundle root, not this file's parent.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from screening import config
from screening.orchestrator import Orchestrator
from screening.services.pdf import PDFExtractionError, extract_text_from_bytes

app = FastAPI(
    title="Agentic Resume Screening System",
    version="1.0.0",
    docs_url="/api/py/docs",
    openapi_url="/api/py/openapi.json",
)

# Built once per container and reused across warm invocations.
_orchestrator: Orchestrator | None = None


def get_orchestrator() -> Orchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = Orchestrator()
    return _orchestrator


@app.get("/api/py/health")
def health() -> dict:
    llm = get_orchestrator().llm
    return {
        "status": "ok",
        "mode": "llm" if llm.available else "rule_based",
        "llm_status": llm.status,
        "model": config.GEMINI_MODEL if llm.available else None,
    }


@app.post("/api/py/screen")
async def screen(
    resume: UploadFile = File(..., description="Candidate resume as a PDF"),
    job_description: str = Form(..., description="Job description text"),
) -> JSONResponse:
    jd_text = (job_description or "").strip()
    if len(jd_text) < 40:
        raise HTTPException(
            status_code=422,
            detail="The job description is too short to screen against. Paste the full posting.",
        )
    if len(jd_text) > config.MAX_JD_CHARS:
        raise HTTPException(
            status_code=413,
            detail=f"The job description exceeds {config.MAX_JD_CHARS:,} characters.",
        )

    if resume.content_type and "pdf" not in resume.content_type.lower():
        raise HTTPException(status_code=415, detail="The resume must be a PDF.")

    data = await resume.read()
    if len(data) > config.MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"The resume exceeds the {config.MAX_UPLOAD_BYTES // (1024 * 1024)} MB limit.",
        )

    try:
        resume_text = extract_text_from_bytes(data)
    except PDFExtractionError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    try:
        result = get_orchestrator().run_from_text(resume_text, jd_text)
    except Exception as exc:
        # The agents already degrade internally, so reaching here means
        # something genuinely unexpected broke.
        raise HTTPException(
            status_code=500, detail=f"Screening failed: {exc}"
        ) from exc

    return JSONResponse(result)
