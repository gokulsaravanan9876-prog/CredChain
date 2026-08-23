# ---------------------------------------------------------------------------
# Job requirement extraction and document-requirement extraction — each with
# a real AI path and a clearly-labeled deterministic fallback path.
#
# Both public functions return (result, mode) where mode is "ai" or
# "fallback" — callers (routes/ai.py) must surface this in the API response
# so the frontend never presents fallback output as if it were a real LLM
# analysis.
# ---------------------------------------------------------------------------

import re

from pydantic import ValidationError

from ...schemas.ai import DocumentRequirementItem, JobRequirements
from . import ai_service
from .prompts import DOCUMENT_REQUIREMENTS_SYSTEM_PROMPT, JOB_ANALYSIS_SYSTEM_PROMPT


def analyze_job_requirements(job_title: str, job_description: str) -> tuple[JobRequirements, str]:
    if ai_service.is_ai_enabled():
        key = ai_service.cache_key("job-analysis", job_title, job_description)
        cached = ai_service.get_cached(key)
        if cached is not None:
            data, mode = cached
            return JobRequirements(**data), mode
        try:
            requirements = _analyze_job_requirements_ai(job_title, job_description)
            ai_service.set_cached(key, requirements.model_dump(), "ai")
            return requirements, "ai"
        except ai_service.AIUnavailableError:
            pass  # fall through to deterministic fallback below

    return _analyze_job_requirements_fallback(job_title, job_description), "fallback"


def _analyze_job_requirements_ai(job_title: str, job_description: str) -> JobRequirements:
    user_content = f"Job title: {job_title}\n\nJob description:\n{job_description}"
    data = ai_service.call_ai_json(system_prompt=JOB_ANALYSIS_SYSTEM_PROMPT, user_content=user_content)
    try:
        return JobRequirements(**data)
    except ValidationError as exc:
        raise ai_service.AIMalformedOutputError(f"AI job analysis output failed schema validation: {exc}") from exc


# Display name per catalog entry — plain .title() mangles acronyms (would turn "sql" into "Sql").
_SKILL_DISPLAY_NAMES = {
    "java": "Java",
    "python": "Python",
    "sql": "SQL",
    "data structures": "Data Structures",
    "system design": "System Design",
    "cloud": "Cloud",
    "aws": "AWS",
    "javascript": "JavaScript",
    "react": "React",
    "communication": "Communication",
}
_SKILL_CATALOG = list(_SKILL_DISPLAY_NAMES.keys())
# "B.E." maps to the same canonical label as "B.Tech" — Indian job postings
# routinely write "B.Tech/B.E." meaning either is acceptable, not two
# separate degree requirements. Without this, a phrase like "B.Tech/B.E.
# Computer Science" would create two requirement items where a candidate
# holding either real degree can only ever satisfy one, artificially
# lowering the match score.
_DEGREE_CANONICAL = {
    "b.tech": "B.TECH",
    "b.e.": "B.TECH",
    "bachelor": "BACHELOR'S",
    "m.tech": "M.TECH",
    "mba": "MBA",
    "bca": "BCA",
    "mca": "MCA",
}
_DOCUMENT_CATALOG = ["resume", "degree certificate", "transcript", "cover letter", "id proof"]
_CGPA_PATTERN = re.compile(r"cgpa[^0-9]{0,10}(\d+(?:\.\d+)?)")
_YEAR_PATTERN = re.compile(r"20\d{2}")


def _analyze_job_requirements_fallback(job_title: str, job_description: str) -> JobRequirements:
    """
    FALLBACK/DEMO MODE — plain deterministic keyword matching, used only
    when AI is unavailable. This is explicitly NOT an LLM and must never be
    presented as one; callers tag this result "fallback" (see
    analyze_job_requirements above).
    """
    text = f"{job_title}\n{job_description}".lower()

    technical_skills = [_SKILL_DISPLAY_NAMES[s] for s in _SKILL_CATALOG if s in text and s != "communication"]
    soft_skills = ["Communication"] if "communication" in text else []

    cgpa_match = _CGPA_PATTERN.search(text)
    minimum_cgpa = float(cgpa_match.group(1)) if cgpa_match else None

    graduation_year = sorted({int(y) for y in _YEAR_PATTERN.findall(text)})

    degree = sorted({label for token, label in _DEGREE_CANONICAL.items() if token in text})

    documents = [doc.title() for doc in _DOCUMENT_CATALOG if doc in text]

    return JobRequirements(
        degree=degree,
        minimum_cgpa=minimum_cgpa,
        graduation_year=graduation_year,
        technical_skills=technical_skills,
        soft_skills=soft_skills,
        experience=None,
        certifications=[],
        documents=documents,
        other_eligibility=[],
    )


def analyze_document_requirements(company_name: str, job_title: str, job_description: str) -> tuple[dict, str]:
    """Returns ({"requirements": [...], "not_specified": [...]}, mode)."""
    if ai_service.is_ai_enabled():
        key = ai_service.cache_key("document-requirements", company_name, job_title, job_description)
        cached = ai_service.get_cached(key)
        if cached is not None:
            return cached
        try:
            result = _analyze_document_requirements_ai(company_name, job_title, job_description)
            ai_service.set_cached(key, result, "ai")
            return result, "ai"
        except ai_service.AIUnavailableError:
            pass

    return _analyze_document_requirements_fallback(job_description), "fallback"


def _analyze_document_requirements_ai(company_name: str, job_title: str, job_description: str) -> dict:
    user_content = f"Company: {company_name}\nJob title: {job_title}\n\nJob description:\n{job_description}"
    data = ai_service.call_ai_json(system_prompt=DOCUMENT_REQUIREMENTS_SYSTEM_PROMPT, user_content=user_content)
    try:
        requirements = [DocumentRequirementItem(**item) for item in data.get("requirements", [])]
        not_specified = [str(s) for s in data.get("not_specified", [])]
    except ValidationError as exc:
        raise ai_service.AIMalformedOutputError(f"AI document requirements output failed schema validation: {exc}") from exc
    return {"requirements": [r.model_dump() for r in requirements], "not_specified": not_specified}


def _analyze_document_requirements_fallback(job_description: str) -> dict:
    """FALLBACK/DEMO MODE — see module docstring. Only flags a document as required/recommended if its exact name literally appears in the text."""
    text = job_description.lower()
    requirements = []
    not_specified = []
    for doc in _DOCUMENT_CATALOG:
        if doc in text:
            requirements.append({"document": doc.title(), "status": "required", "source": "job description (fallback keyword match)"})
        else:
            not_specified.append(doc.title())
    return {"requirements": requirements, "not_specified": not_specified}
