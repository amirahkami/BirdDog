from __future__ import annotations

import json

from pydantic import BaseModel, ValidationError

from app.llm.kiconnect import LLMError, chat_completion


FACTS_SCHEMA_VERSION = "cv.facts.v1"


class Language(BaseModel):
    language: str
    level: str | None = None


class Experience(BaseModel):
    title: str
    organization: str | None = None
    start: str | None = None
    end: str | None = None
    summary: str | None = None


class Education(BaseModel):
    degree: str | None = None
    field: str | None = None
    institution: str | None = None
    year: str | None = None


class CandidateFacts(BaseModel):
    summary: str | None = None
    skills: list[str] = []
    languages: list[Language] = []
    experience: list[Experience] = []
    education: list[Education] = []
    total_years_experience: float | None = None
    seniority: str | None = None
    evidence: dict[str, list[str]] = {}


_SYSTEM = (
    "You extract structured facts from a job seeker's CV. "
    "Use ONLY information explicitly present in the CV — never invent or infer beyond the text. "
    "The CV may be in German or English; keep field values in their original language. "
    "Return ONLY a single JSON object — no prose, no markdown fences."
)

_INSTRUCTIONS = """Return a JSON object with this shape:
{
  "summary": string | null,
  "skills": string[],
  "languages": [{"language": string, "level": string | null}],
  "experience": [{"title": string, "organization": string|null, "start": string|null, "end": string|null, "summary": string|null}],
  "education": [{"degree": string|null, "field": string|null, "institution": string|null, "year": string|null}],
  "total_years_experience": number | null,
  "seniority": string | null,
  "evidence": {"skills": string[], "seniority": string[], "experience": string[]}
}
Use null or empty arrays for anything not supported by the CV text. In "evidence", give short verbatim quotes from the CV that support the key facts."""


def _parse_json(content: str) -> dict:
    text = content.strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise LLMError("KIConnect response was not JSON")
    return json.loads(text[start : end + 1])


def extract_candidate_facts(text: str, language: str | None) -> tuple[dict, dict]:
    """Turn CV text into (facts, evidence) via KIConnect. Raises LLMError on failure."""
    excerpt = (text or "").strip()
    if not excerpt:
        raise LLMError("CV has no extracted text", retryable=False)
    excerpt = excerpt[:20000]

    messages = [
        {"role": "system", "content": _SYSTEM},
        {
            "role": "user",
            "content": (
                f"{_INSTRUCTIONS}\n\nCV language: {language or 'unknown'}\n\nCV TEXT:\n{excerpt}"
            ),
        },
    ]
    content = chat_completion(messages, temperature=0.1, max_tokens=2000)

    try:
        raw = _parse_json(content)
        facts = CandidateFacts.model_validate(raw)
    except (json.JSONDecodeError, ValidationError) as error:
        raise LLMError(f"Could not parse candidate facts: {error}") from error

    facts_dict = facts.model_dump(exclude={"evidence"})
    evidence = {key: value for key, value in facts.evidence.items() if value}
    return facts_dict, evidence
