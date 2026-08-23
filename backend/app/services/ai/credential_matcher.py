# ---------------------------------------------------------------------------
# Deterministic credential-to-requirement matching. This module NEVER calls
# an LLM — the match score must be reproducible and auditable, not a
# model's opinion (see Phase 7 spec §12: "Do not let the LLM arbitrarily
# invent the score").
#
# SCORING FORMULA:
#   score = round(matched_measurable_requirements / total_measurable_requirements * 100)
#   score = 0 when there are zero measurable requirements to check.
#
# "Measurable" requirements are the ones with a reliable, structured signal
# in a credential record: explicit degree names, an explicit minimum CGPA,
# explicit graduation years, explicit technical skills, and explicit
# certifications. soft_skills / documents / other_eligibility are excluded
# from scoring — credentials carry no structured signal to check those
# against, and guessing would violate the "do not invent" principle just as
# much on the matching side as on the extraction side.
#
# Only credentials with status == ACTIVE are considered evidence — a
# revoked credential is never counted as a valid match.
#
# Matching itself is a case-insensitive substring check between a
# requirement's label and a credential's title/degree text — a deliberate,
# simple heuristic (not semantic matching), documented as a known
# limitation: "AWS certification" will match a credential titled "AWS
# Certification" but not one titled "Amazon Web Services Associate".
# ---------------------------------------------------------------------------

from dataclasses import dataclass

from ...models.credential import Credential
from ...models.enums import CredentialStatus
from ...schemas.ai import JobRequirements


@dataclass
class _RequirementItem:
    category: str
    label: str


def _build_requirement_items(req: JobRequirements) -> list[_RequirementItem]:
    items: list[_RequirementItem] = []
    for d in req.degree:
        items.append(_RequirementItem("degree", d))
    if req.minimum_cgpa is not None:
        items.append(_RequirementItem("cgpa", f"CGPA ≥ {req.minimum_cgpa}"))
    if req.graduation_year:
        items.append(_RequirementItem("graduation_year", f"Graduation year: {', '.join(str(y) for y in req.graduation_year)}"))
    for s in req.technical_skills:
        items.append(_RequirementItem("technical_skill", s))
    for c in req.certifications:
        items.append(_RequirementItem("certification", c))
    return items


def _credential_texts(credentials: list[Credential]) -> list[str]:
    texts = []
    for c in credentials:
        texts.append(c.title.lower())
        if c.degree:
            texts.append(c.degree.lower())
    return texts


def _is_matched(item: _RequirementItem, credentials: list[Credential], texts: list[str], graduation_years: set[int]) -> bool:
    if item.category == "cgpa":
        threshold = float(item.label.rsplit("≥", 1)[-1].strip())
        return any(c.cgpa is not None and float(c.cgpa) >= threshold for c in credentials)
    if item.category == "graduation_year":
        return any(c.graduation_year in graduation_years for c in credentials)
    needle = item.label.lower()
    return any(needle in text or text in needle for text in texts)


def match_credentials(requirements: JobRequirements, credentials: list[Credential]) -> dict:
    active_credentials = [c for c in credentials if c.status == CredentialStatus.ACTIVE]
    texts = _credential_texts(active_credentials)
    graduation_years = set(requirements.graduation_year)

    items = _build_requirement_items(requirements)
    matched_labels: list[str] = []
    missing_labels: list[str] = []

    for item in items:
        if _is_matched(item, active_credentials, texts, graduation_years):
            matched_labels.append(item.label)
        else:
            missing_labels.append(item.label)

    total = len(items)
    matched_count = len(matched_labels)
    score = round((matched_count / total) * 100) if total > 0 else 0

    recommendations = [f"Consider addressing: {label}" for label in missing_labels]
    if not recommendations:
        recommendations = ["No missing measurable requirements were identified from the job description."]

    return {
        "match_summary": {"matched": matched_count, "missing": total - matched_count, "total": total, "score": score},
        "matched": matched_labels,
        "missing": missing_labels,
        "recommendations": recommendations,
    }
