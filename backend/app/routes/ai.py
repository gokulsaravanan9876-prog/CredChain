import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..models.activity_log import ActivityLog
from ..models.credential import Credential
from ..models.enums import CredentialStatus
from ..models.job import Job
from ..models.user import User
from ..schemas.ai import (
    AIHealthResponse,
    CompanyIntelligenceRequest,
    CompanyIntelligenceResponse,
    CredentialMatchRequest,
    CredentialMatchResponse,
    DocumentRequirementItem,
    DocumentRequirementsRequest,
    DocumentRequirementsResponse,
    JobAIAnalysisResponse,
    JobAnalysisRequest,
    JobAnalysisResponse,
    MatchSummary,
    WalletComparisonItem,
)
from ..schemas.job import EligibilityResult
from ..security.permissions import require_student
from ..services import eligibility_service
from ..services.ai import ai_service, company_intelligence, credential_matcher, requirement_analyzer

router = APIRouter(prefix="/api/ai", tags=["ai"])


def _log_ai_activity(
    db: Session, user: User, action: str, *, company_name: str | None, job_title: str | None, mode: str
) -> None:
    """
    Deliberately does NOT store the job description text — company-provided
    text can be sensitive/proprietary, and it isn't needed to audit that an
    AI feature was used. Only the action, a display-friendly title, and
    whether it ran in real-AI or fallback mode are recorded.
    """
    db.add(
        ActivityLog(
            actor_user_id=user.id,
            action=action,
            entity_type="ai_analysis",
            entity_id=None,
            metadata_={"company_name": company_name, "job_title": job_title, "analysis_mode": mode},
        )
    )
    db.commit()


@router.get("/health", response_model=AIHealthResponse, summary="Whether a real AI provider is configured, or requests will run in fallback/demo mode")
def ai_health() -> AIHealthResponse:
    enabled = ai_service.is_ai_enabled()
    return AIHealthResponse(
        ai_enabled=enabled,
        provider=settings.ai_provider if enabled else None,
        model=settings.ai_model if enabled else None,
    )


@router.post("/document-requirements", response_model=DocumentRequirementsResponse)
def document_requirements(
    payload: DocumentRequirementsRequest,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
) -> DocumentRequirementsResponse:
    if current_user.student is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No student profile for this account")

    try:
        data, mode = requirement_analyzer.analyze_document_requirements(
            payload.company_name, payload.job_title, payload.job_description
        )
    except ai_service.AIMalformedOutputError:
        raise HTTPException(status_code=502, detail="AI returned an unusable response. Please try again.")

    requirements = [DocumentRequirementItem(**item) for item in data["requirements"]]

    # Compare against the AUTHENTICATED student's own ACTIVE credentials
    # only — student_id is never accepted from the request.
    active_credentials = (
        db.query(Credential)
        .filter(Credential.student_id == current_user.student.id, Credential.status == CredentialStatus.ACTIVE)
        .all()
    )
    wallet_comparison = []
    for req in requirements:
        needle = req.document.lower()
        match = next(
            (c.title for c in active_credentials if needle in c.title.lower() or c.title.lower() in needle),
            None,
        )
        wallet_comparison.append(
            WalletComparisonItem(document=req.document, available=match is not None, matched_credential_title=match)
        )

    _log_ai_activity(db, current_user, "AI_DOCUMENT_ANALYSIS", company_name=payload.company_name, job_title=payload.job_title, mode=mode)

    return DocumentRequirementsResponse(
        company=payload.company_name,
        job_title=payload.job_title,
        requirements=requirements,
        not_specified=data["not_specified"],
        wallet_comparison=wallet_comparison,
        analysis_mode=mode,
    )


@router.post("/company-intelligence", response_model=CompanyIntelligenceResponse)
def company_intelligence_endpoint(
    payload: CompanyIntelligenceRequest,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
) -> CompanyIntelligenceResponse:
    if current_user.student is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No student profile for this account")

    try:
        data, mode = company_intelligence.analyze_company_intelligence(
            payload.company_name, payload.job_title, payload.job_description
        )
    except ai_service.AIMalformedOutputError:
        raise HTTPException(status_code=502, detail="AI returned an unusable response. Please try again.")

    _log_ai_activity(db, current_user, "AI_COMPANY_ANALYSIS", company_name=payload.company_name, job_title=payload.job_title, mode=mode)

    return CompanyIntelligenceResponse(company=payload.company_name, analysis_mode=mode, **data)


@router.post("/job-analysis", response_model=JobAnalysisResponse)
def job_analysis(
    payload: JobAnalysisRequest,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
) -> JobAnalysisResponse:
    if current_user.student is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No student profile for this account")

    try:
        requirements, mode = requirement_analyzer.analyze_job_requirements(payload.job_title, payload.job_description)
    except ai_service.AIMalformedOutputError:
        raise HTTPException(status_code=502, detail="AI returned an unusable response. Please try again.")

    _log_ai_activity(db, current_user, "AI_JOB_ANALYSIS", company_name=None, job_title=payload.job_title, mode=mode)

    return JobAnalysisResponse(**requirements.model_dump(), analysis_mode=mode)


@router.post(
    "/credential-match",
    response_model=CredentialMatchResponse,
    summary="Extracts job requirements (AI or fallback) then deterministically matches them against the authenticated student's own active credentials",
)
def credential_match(
    payload: CredentialMatchRequest,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
) -> CredentialMatchResponse:
    if current_user.student is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No student profile for this account")

    try:
        requirements, mode = requirement_analyzer.analyze_job_requirements(payload.job_title, payload.job_description)
    except ai_service.AIMalformedOutputError:
        raise HTTPException(status_code=502, detail="AI returned an unusable response. Please try again.")

    # Always the authenticated student's OWN credentials, queried fresh —
    # never accepted from the request body. Both active and non-active rows
    # are fetched here only so match_credentials() can filter to active
    # itself (keeping the "revoked is never valid evidence" rule in one place).
    credentials = db.query(Credential).filter(Credential.student_id == current_user.student.id).all()
    result = credential_matcher.match_credentials(requirements, credentials)

    _log_ai_activity(db, current_user, "AI_JOB_MATCH", company_name=None, job_title=payload.job_title, mode=mode)

    return CredentialMatchResponse(
        match_summary=MatchSummary(**result["match_summary"]),
        matched=result["matched"],
        missing=result["missing"],
        recommendations=result["recommendations"],
        analysis_mode=mode,
    )


@router.post(
    "/analyze-job/{job_id}",
    response_model=JobAIAnalysisResponse,
    summary=(
        "Full AI analysis of a REAL job posting — company/job text is loaded server-side from job_id, never accepted as "
        "free text, and run through the exact same document-requirements/company-intelligence/credential-match analyzers "
        "above, plus the deterministic (non-AI) eligibility check. No second AI service."
    ),
)
def analyze_job(job_id: uuid.UUID, current_user: User = Depends(require_student), db: Session = Depends(get_db)) -> JobAIAnalysisResponse:
    if current_user.student is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No student profile for this account")

    job = db.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    company_name = job.company.name
    job_title = job.title
    job_description = job.description

    try:
        docs_data, docs_mode = requirement_analyzer.analyze_document_requirements(company_name, job_title, job_description)
        company_data, company_mode = company_intelligence.analyze_company_intelligence(company_name, job_title, job_description)
        job_requirements, match_mode = requirement_analyzer.analyze_job_requirements(job_title, job_description)
    except ai_service.AIMalformedOutputError:
        raise HTTPException(status_code=502, detail="AI returned an unusable response. Please try again.")

    requirements = [DocumentRequirementItem(**item) for item in docs_data["requirements"]]
    active_credentials = (
        db.query(Credential).filter(Credential.student_id == current_user.student.id, Credential.status == CredentialStatus.ACTIVE).all()
    )
    wallet_comparison = []
    for req in requirements:
        needle = req.document.lower()
        match = next((c.title for c in active_credentials if needle in c.title.lower() or c.title.lower() in needle), None)
        wallet_comparison.append(WalletComparisonItem(document=req.document, available=match is not None, matched_credential_title=match))

    document_requirements = DocumentRequirementsResponse(
        company=company_name,
        job_title=job_title,
        requirements=requirements,
        not_specified=docs_data["not_specified"],
        wallet_comparison=wallet_comparison,
        analysis_mode=docs_mode,
    )
    company_intel = CompanyIntelligenceResponse(company=company_name, analysis_mode=company_mode, **company_data)

    all_credentials = db.query(Credential).filter(Credential.student_id == current_user.student.id).all()
    match_result = credential_matcher.match_credentials(job_requirements, all_credentials)
    credential_match = CredentialMatchResponse(
        match_summary=MatchSummary(**match_result["match_summary"]),
        matched=match_result["matched"],
        missing=match_result["missing"],
        recommendations=match_result["recommendations"],
        analysis_mode=match_mode,
    )

    eligibility = EligibilityResult(**eligibility_service.evaluate(db, job, current_user.student))

    _log_ai_activity(db, current_user, "AI_JOB_MARKETPLACE_ANALYSIS", company_name=company_name, job_title=job_title, mode=match_mode)

    return JobAIAnalysisResponse(
        job_id=str(job.id),
        company_name=company_name,
        job_title=job_title,
        document_requirements=document_requirements,
        company_intelligence=company_intel,
        credential_match=credential_match,
        eligibility=eligibility,
    )
