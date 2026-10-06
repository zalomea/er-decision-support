"""ER Decision Support Backend.

Uses llama.cpp GGUF model (ggml-org/Clef-Flash-GGUF:Q4_K_M).
"""

import logging
import os
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field


class _SuppressHealthAccessFilter(logging.Filter):
    def filter(self, record):
        message = record.getMessage()
        return "GET /health HTTP/" not in message and "HEAD /health HTTP/" not in message


logging.getLogger("uvicorn.access").addFilter(_SuppressHealthAccessFilter())

MODEL_ID = "ggml-org/Clef-Flash-GGUF:Q4_K_M"
LLAMA_URL = os.getenv("LLAMA_URL", "http://clef:5080")


app = FastAPI(
    title="ER Decision Support API",
    description="Research prototype for emergency-care decision-support evaluation.",
    version="0.1.0",
)


class DecisionRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    report: str = Field(
        min_length=1,
        max_length=40_000,
        description="De-identified clinical report text (maximum 40,000 characters).",
    )


DISCHARGE_QUESTIONS = {
    "discharge": {
        "type": "noul",
        "instructions": (
            "Should this patient be discharged from the emergency room? "
            "Answer 'yes' if the patient is stable and can safely leave. "
            "Answer 'no' if the patient needs continued treatment, observation, "
            "or admission."
        ),
    },
    "severity": {
        "type": "score",
        "instructions": (
            "What is the severity of this patient's condition? "
            "Rate from Minor (outpatient treatment possible) to Critical "
            "(life-threatening, immediate intervention needed)."
        ),
        "criteria": [
            "Minor - can be treated as outpatient",
            "Moderate - needs observation or short stay",
            "Serious - requires admission or intensive treatment",
            "Critical - life-threatening, immediate intervention needed",
        ],
    },
    "risk_factors": {
        "type": "choice",
        "instructions": "What is the primary risk factor for this patient?",
        "criteria": {
            "none": "No significant risk factors identified",
            "cardiac": "Cardiac or cardiovascular risk",
            "respiratory": "Respiratory or breathing risk",
            "neurological": "Neurological or cognitive risk",
            "infectious": "Infectious disease risk",
            "trauma": "Trauma or injury-related risk",
        },
    },
}

PRIORITY_QUESTIONS = {
    "priority": {
        "type": "score",
        "instructions": (
            "What is the ESI triage level for this patient? Use 1 for the most "
            "urgent (immediate life-saving intervention) and 5 for the least "
            "urgent (no resources expected)."
        ),
        "criteria": [
            "1 - ESI-1: immediate life-saving intervention required",
            "2 - ESI-2: high risk, severe pain, or severe distress",
            "3 - ESI-3: stable; multiple resources expected",
            "4 - ESI-4: stable; one resource expected",
            "5 - ESI-5: stable; no resources expected",
        ],
    },
    "triage_category": {
        "type": "choice",
        "instructions": "What is the appropriate triage category for this patient?",
        "criteria": {
            "esi_1": "ESI-1: Immediate life-saving intervention required",
            "esi_2": "ESI-2: High risk, severe pain, or distress",
            "esi_3": "ESI-3: Stable but needs multiple resources",
            "esi_4": "ESI-4: Stable, needs one resource",
            "esi_5": "ESI-5: Stable, needs no resources",
        },
    },
    "resource_needs": {
        "type": "choice",
        "instructions": "What level of resources will this patient need?",
        "criteria": {
            "none": "No resources needed (discharge)",
            "minimal": "Minimal resources (e.g., prescription, simple test)",
            "moderate": "Moderate resources (e.g., labs, imaging, consult)",
            "extensive": "Extensive resources (e.g., multiple specialists, surgery)",
            "critical": "Critical resources (e.g., ICU, blood products, OR)",
        },
    },
}


@app.get("/health")
def health():
    return {"status": "ok", "model": MODEL_ID}


async def call_systemone(questions: dict, state: str) -> dict:
    """Call the SystemOne API via llama.cpp server."""
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            resp = await client.post(
                f"{LLAMA_URL}/v1/systemone",
                json={
                    "model": "clef-flash",
                    "state": state,
                    "questions": questions,
                },
            )
            resp.raise_for_status()
            payload = resp.json()
            if not isinstance(payload, dict):
                raise ValueError("Inference response must be a JSON object")
            return payload
    except httpx.TimeoutException as exc:
        raise HTTPException(
            status_code=504, detail="Inference service timed out"
        ) from exc
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502, detail="Inference service returned an error"
        ) from exc
    except (httpx.RequestError, ValueError) as exc:
        raise HTTPException(
            status_code=502, detail="Inference service is unavailable"
        ) from exc


@app.post("/api/discharge")
async def discharge(request: DecisionRequest, simple: bool = False):
    questions = {"discharge": DISCHARGE_QUESTIONS["discharge"]} if simple else DISCHARGE_QUESTIONS
    return await call_systemone(questions, request.report)


@app.post("/api/priority")
async def priority(request: DecisionRequest, simple: bool = False):
    questions = {"priority": PRIORITY_QUESTIONS["priority"]} if simple else PRIORITY_QUESTIONS
    return await call_systemone(questions, request.report)


EXAMPLES_DIR = (Path(__file__).resolve().parent / "examples").resolve()


def _extract_context(text: str, query: str, context_chars: int = 80) -> str:
    lower_text = text.lower()
    lower_query = query.lower()
    idx = lower_text.find(lower_query)
    if idx == -1:
        return text[:context_chars * 2]
    start = max(0, idx - context_chars)
    end = min(len(text), idx + len(query) + context_chars)
    snippet = text[start:end].replace("\n", " ").strip()
    prefix = "..." if start > 0 else ""
    suffix = "..." if end < len(text) else ""
    return f"{prefix}{snippet}{suffix}"


@app.get("/api/examples/search")
async def search_examples(q: str = Query(..., min_length=1, max_length=200)):
    results = []
    query = q.strip()
    if not query:
        return {"results": []}
    for path in sorted(EXAMPLES_DIR.rglob("*.txt")):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if query.lower() in text.lower():
            rel_path = path.relative_to(EXAMPLES_DIR)
            context = _extract_context(text, query)
            results.append({
                "file": str(rel_path),
                "context": context,
            })
    return {"results": results}


@app.get("/api/examples/file")
async def get_example_file(path: str = Query(..., min_length=1, max_length=500)):
    target = (EXAMPLES_DIR / path).resolve()
    if not target.is_file() or EXAMPLES_DIR not in target.parents:
        raise HTTPException(status_code=404, detail="File not found")
    try:
        content = target.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        raise HTTPException(status_code=404, detail="File not found")
    return {"content": content}
