# ---------------------------------------------------------------------------
# Deterministic job eligibility — Part 3's explicit requirement: AI never
# makes this decision. Every check here is a plain Python comparison
# against real Credential/Student rows, reused unchanged by the job detail
# page, the apply-eligibility gate, and the AI job-analysis endpoint's
# eligibility section (single source of truth — see routes/ai.py).
#
# Mandatory gate (all must pass for status=ELIGIBLE): required_degree,
# minimum_cgpa, graduation_year_requirement. required_skills/certifications
# are shown as line items but are advisory, not blocking — a job market
# doesn't hard-reject over one missing skill, and Part 5 separately treats
# missing skills as "preparation suggestions," which only makes sense if
# they aren't a hard gate.
#
# CRITICAL correctness rule: a mandatory requirement the student's real
# active credentials simply have no data for (e.g. no credential carries a
# cgpa value at all) is NOT the same thing as that requirement failing.
# "9.6 CGPA vs required 9.0" must PASS; "no CGPA on file vs required 9.0"
# must be reported as INCOMPLETE, never silently folded into either PASS or
# FAIL — both of those would be a fabricated claim about data that doesn't
# exist. See EligibilityCheckItem.status / EligibilityResult.status.
# ---------------------------------------------------------------------------

from sqlalchemy.orm import Session

from ..models.credential import Credential
from ..models.enums import CredentialStatus
from ..models.job import Job
from ..models.student import Student

CheckStatus = str  # "met" | "not_met" | "incomplete"


class EligibilityCheck:
    def __init__(self, label: str, check_status: CheckStatus, mandatory: bool):
        self.label = label
        self.status = check_status
        self.mandatory = mandatory

    @property
    def met(self) -> bool:
        return self.status == "met"


def _active_credentials(db: Session, student: Student) -> list[Credential]:
    return db.query(Credential).filter(Credential.student_id == student.id, Credential.status == CredentialStatus.ACTIVE).all()


def evaluate(db: Session, job: Job, student: Student) -> dict:
    credentials = _active_credentials(db, student)
    checks: list[EligibilityCheck] = []

    if job.required_degree:
        needle = job.required_degree.strip().lower()
        degrees = [c.degree for c in credentials if c.degree]
        if not degrees:
            checks.append(EligibilityCheck(job.required_degree, "incomplete", mandatory=True))
        else:
            met = any(needle in d.lower() or d.lower() in needle for d in degrees)
            checks.append(EligibilityCheck(job.required_degree, "met" if met else "not_met", mandatory=True))

    if job.minimum_cgpa is not None:
        cgpa_values = [float(c.cgpa) for c in credentials if c.cgpa is not None]
        if not cgpa_values:
            checks.append(EligibilityCheck(f"Minimum CGPA {job.minimum_cgpa}", "incomplete", mandatory=True))
        else:
            best_cgpa = max(cgpa_values)
            met = best_cgpa >= float(job.minimum_cgpa)
            checks.append(EligibilityCheck(f"CGPA {best_cgpa:.2f}", "met" if met else "not_met", mandatory=True))

    if job.graduation_year_requirement is not None:
        grad_years = [c.graduation_year for c in credentials if c.graduation_year is not None]
        if not grad_years:
            checks.append(
                EligibilityCheck(f"Graduation Year {job.graduation_year_requirement}", "incomplete", mandatory=True)
            )
        else:
            met = job.graduation_year_requirement in grad_years
            checks.append(
                EligibilityCheck(f"Graduation Year {job.graduation_year_requirement}", "met" if met else "not_met", mandatory=True)
            )

    student_skills = {s.strip().lower() for s in (student.skills or [])}
    for skill in job.required_skills:
        met = skill.strip().lower() in student_skills
        checks.append(EligibilityCheck(skill, "met" if met else "not_met", mandatory=False))

    for cert in job.required_certifications:
        needle = cert.strip().lower()
        met = any(needle in c.title.lower() or c.title.lower() in needle for c in credentials)
        checks.append(EligibilityCheck(cert, "met" if met else "not_met", mandatory=False))

    mandatory_checks = [c for c in checks if c.mandatory]
    if any(c.status == "not_met" for c in mandatory_checks):
        overall = "not_eligible"
    elif any(c.status == "incomplete" for c in mandatory_checks):
        overall = "incomplete"
    else:
        overall = "eligible"

    return {
        "is_eligible": overall == "eligible",
        "status": overall,
        "checks": [{"label": c.label, "met": c.met, "mandatory": c.mandatory, "status": c.status} for c in checks],
    }
