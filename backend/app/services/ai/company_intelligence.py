# ---------------------------------------------------------------------------
# Company intelligence — real AI path + a clearly-labeled fallback.
#
# The fallback has NO external data source, so it deliberately reports
# almost everything as unavailable rather than inventing plausible-sounding
# company facts — see the module-level principle in Phase 7: never fabricate
# package figures, statistics, or eligibility criteria.
# ---------------------------------------------------------------------------

from pydantic import ValidationError

from ...schemas.ai import CompanyIntelligenceResponse
from . import ai_service
from .prompts import COMPANY_INTELLIGENCE_SYSTEM_PROMPT

# Fields validated here excluding `company`/`analysis_mode`, which the route adds.
_RESPONSE_FIELDS = {"overview", "common_roles", "eligibility", "skills", "recruitment_process", "package_information", "trends", "sources"}


def analyze_company_intelligence(company_name: str, job_title: str, job_description: str | None) -> tuple[dict, str]:
    if ai_service.is_ai_enabled():
        key = ai_service.cache_key("company-intelligence", company_name, job_title, job_description)
        cached = ai_service.get_cached(key)
        if cached is not None:
            return cached
        try:
            result = _analyze_company_intelligence_ai(company_name, job_title, job_description)
            ai_service.set_cached(key, result, "ai")
            return result, "ai"
        except ai_service.AIUnavailableError:
            pass

    return _analyze_company_intelligence_fallback(company_name, job_title), "fallback"


def _analyze_company_intelligence_ai(company_name: str, job_title: str, job_description: str | None) -> dict:
    user_content = f"Company: {company_name}\nJob title: {job_title}\n"
    if job_description:
        user_content += f"\nJob description:\n{job_description}"

    data = ai_service.call_ai_json(system_prompt=COMPANY_INTELLIGENCE_SYSTEM_PROMPT, user_content=user_content)
    try:
        # Validate against the response shape (minus fields the route fills in) before trusting it.
        validated = CompanyIntelligenceResponse(company=company_name, analysis_mode="ai", **{k: v for k, v in data.items() if k in _RESPONSE_FIELDS})
    except ValidationError as exc:
        raise ai_service.AIMalformedOutputError(f"AI company intelligence output failed schema validation: {exc}") from exc
    return validated.model_dump(exclude={"company", "analysis_mode"})


def _analyze_company_intelligence_fallback(company_name: str, job_title: str) -> dict:
    """FALLBACK/DEMO MODE — no external data source, so nearly everything is honestly reported as unavailable rather than invented."""
    return {
        "overview": f"AI-generated company intelligence is not available in fallback/demo mode for {company_name}. Enable AI_ENABLED with a valid AI_API_KEY to get a real analysis.",
        "common_roles": [job_title] if job_title else [],
        "eligibility": [],
        "skills": [],
        "recruitment_process": [],
        "package_information": {
            "available": False,
            "amount": None,
            "currency": None,
            "year": None,
            "source": None,
            "message": "No reliable package information was found.",
        },
        "trends": [],
        "sources": [],
    }
