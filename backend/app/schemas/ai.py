from typing import Literal

from pydantic import BaseModel, Field

from .job import EligibilityResult

# ---------------------------------------------------------------------------
# Every response schema below carries analysis_mode: "ai" | "fallback" so the
# frontend can render a visibly different badge/banner for demo/fallback
# output — never let it look like a real LLM result. See
# app/services/ai/ai_service.py for how that mode is decided.
# ---------------------------------------------------------------------------


# ---- Document requirements --------------------------------------------------


class DocumentRequirementsRequest(BaseModel):
    company_name: str = Field(min_length=1, max_length=255)
    job_title: str = Field(min_length=1, max_length=255)
    job_description: str = Field(min_length=1, max_length=8000)


class DocumentRequirementItem(BaseModel):
    document: str
    status: Literal["required", "recommended"]
    source: str


class WalletComparisonItem(BaseModel):
    document: str
    available: bool
    matched_credential_title: str | None = None


class DocumentRequirementsResponse(BaseModel):
    company: str
    job_title: str
    requirements: list[DocumentRequirementItem]
    not_specified: list[str]
    # Compares the extracted requirements against the AUTHENTICATED student's
    # own active credentials — never populated from a frontend-supplied list.
    wallet_comparison: list[WalletComparisonItem]
    analysis_mode: Literal["ai", "fallback"]


# ---- Company intelligence ----------------------------------------------------


class CompanyIntelligenceRequest(BaseModel):
    company_name: str = Field(min_length=1, max_length=255)
    job_title: str = Field(min_length=1, max_length=255)
    job_description: str | None = Field(default=None, max_length=8000)


class PackageInfo(BaseModel):
    available: bool
    amount: str | None = None
    currency: str | None = None
    year: int | None = None
    source: str | None = None
    message: str | None = None


class TrendItem(BaseModel):
    claim: str
    source: str
    year: int


class CompanyIntelligenceResponse(BaseModel):
    company: str
    overview: str
    common_roles: list[str]
    eligibility: list[str]
    skills: list[str]
    recruitment_process: list[str]
    package_information: PackageInfo
    trends: list[TrendItem]
    sources: list[str]
    analysis_mode: Literal["ai", "fallback"]


# ---- Job analysis --------------------------------------------------------------


class JobAnalysisRequest(BaseModel):
    job_title: str = Field(min_length=1, max_length=255)
    job_description: str = Field(min_length=1, max_length=8000)


class JobRequirements(BaseModel):
    """The structured shape both the AI extractor and the deterministic fallback extractor must produce."""

    degree: list[str] = []
    minimum_cgpa: float | None = None
    graduation_year: list[int] = []
    technical_skills: list[str] = []
    soft_skills: list[str] = []
    experience: str | None = None
    certifications: list[str] = []
    documents: list[str] = []
    other_eligibility: list[str] = []


class JobAnalysisResponse(JobRequirements):
    analysis_mode: Literal["ai", "fallback"]


# ---- Credential matching -----------------------------------------------------


class CredentialMatchRequest(BaseModel):
    job_title: str = Field(min_length=1, max_length=255)
    job_description: str = Field(min_length=1, max_length=8000)


class MatchSummary(BaseModel):
    matched: int
    missing: int
    total: int
    score: int


class CredentialMatchResponse(BaseModel):
    match_summary: MatchSummary
    matched: list[str]
    missing: list[str]
    recommendations: list[str]
    analysis_mode: Literal["ai", "fallback"]


# ---- Health -------------------------------------------------------------------


class AIHealthResponse(BaseModel):
    ai_enabled: bool
    provider: str | None
    model: str | None


# ---- Real job analysis (job-marketplace phase) --------------------------------
# Job/company text is loaded server-side from a real job_id — never accepted
# as free text from the client — then run through the SAME three analyzer
# functions above unchanged, plus the deterministic (non-AI) eligibility
# check. One combined response so the frontend doesn't stitch together three
# separate calls with client-supplied company/job text.


class JobAIAnalysisResponse(BaseModel):
    job_id: str
    company_name: str
    job_title: str
    document_requirements: DocumentRequirementsResponse
    company_intelligence: CompanyIntelligenceResponse
    credential_match: CredentialMatchResponse
    eligibility: EligibilityResult
