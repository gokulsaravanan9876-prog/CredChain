# ---------------------------------------------------------------------------
# DEVELOPMENT-ONLY seed script. Not imported or run by the FastAPI app
# itself — run it manually. Safe to run repeatedly:
#   - each user is looked up by email first and skipped (not duplicated)
#   - the institution's signing keypair is only generated once
#     (ensure_institution_keypair is idempotent) and never regenerated
#   - the student's institution_id link is (re)applied even if the student
#     row already existed from a Phase 3 run, before institution affiliation
#     existed
#
# Usage:
#   cd backend
#   venv\Scripts\Activate.ps1
#   python -m scripts.seed_demo_users
#
# Passwords below are intentionally simple, hackathon-demo-only values,
# hashed with the exact same app.security.password.hash_password() used by
# real registration — never stored or compared as plaintext. Do NOT reuse
# these passwords or this script's approach for anything beyond a local demo.
# ---------------------------------------------------------------------------

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database import SessionLocal  # noqa: E402
from app.models.company import Company  # noqa: E402
from app.models.enums import UserRole  # noqa: E402
from app.models.institution import Institution  # noqa: E402
from app.models.student import Student  # noqa: E402
from app.models.user import User  # noqa: E402
from app.security.password import hash_password  # noqa: E402
from app.services.signing_service import ensure_institution_keypair  # noqa: E402

STUDENT = {
    "email": "rahul.kumar@student.credchain.dev",
    "password": "StudentDemo123",
    "full_name": "Rahul Kumar",
    "student_identifier": "XYZ-2026-CS-014",
}
INSTITUTION = {
    "email": "admin@xyzuniversity.credchain.dev",
    "password": "InstitutionDemo123",
    "full_name": "Prof. S. Iyer",
    "name": "XYZ University",
    "registration_number": "XYZ-UNIV-001",
}
COMPANY = {
    "email": "hr@abctechnologies.credchain.dev",
    "password": "VerifierDemo123",
    "full_name": "Anjali Mehta",
    "name": "ABC Technologies",
    "industry": "Technology",
}


def _get_or_create_user(db, *, email: str, password: str, full_name: str, role: UserRole) -> tuple[User, bool]:
    user = db.query(User).filter(User.email == email).first()
    if user:
        return user, False
    user = User(email=email, password_hash=hash_password(password), full_name=full_name, role=role, is_active=True)
    db.add(user)
    db.flush()
    return user, True


def seed() -> None:
    db = SessionLocal()
    try:
        # Institution first — the student below links to it.
        institution_user, institution_created = _get_or_create_user(
            db,
            email=INSTITUTION["email"],
            password=INSTITUTION["password"],
            full_name=INSTITUTION["full_name"],
            role=UserRole.INSTITUTION,
        )
        if institution_created:
            institution = Institution(
                user_id=institution_user.id,
                name=INSTITUTION["name"],
                registration_number=INSTITUTION["registration_number"],
            )
            db.add(institution)
            db.flush()
            db.commit()
            print(f"created: {INSTITUTION['email']} (institution)")
        else:
            institution = institution_user.institution
            print(f"skip (already exists): {INSTITUTION['email']}")

        # Idempotent — generates a signing keypair only if this institution
        # doesn't already have one; never regenerates an existing identity.
        had_key = institution.public_key is not None
        ensure_institution_keypair(db, institution)
        if not had_key:
            print(f"generated signing keypair for: {institution.name}")
        else:
            print(f"signing keypair already exists for: {institution.name}")

        student_user, student_created = _get_or_create_user(
            db,
            email=STUDENT["email"],
            password=STUDENT["password"],
            full_name=STUDENT["full_name"],
            role=UserRole.STUDENT,
        )
        if student_created:
            db.add(
                Student(
                    user_id=student_user.id,
                    student_identifier=STUDENT["student_identifier"],
                    institution_id=institution.id,
                )
            )
            db.commit()
            print(f"created: {STUDENT['email']} (student, affiliated with {institution.name})")
        else:
            student = student_user.student
            if student.institution_id != institution.id:
                student.institution_id = institution.id
                db.commit()
                print(f"linked existing student {STUDENT['email']} to {institution.name}")
            else:
                print(f"skip (already exists): {STUDENT['email']}")

        company_user, company_created = _get_or_create_user(
            db,
            email=COMPANY["email"],
            password=COMPANY["password"],
            full_name=COMPANY["full_name"],
            role=UserRole.VERIFIER,
        )
        if company_created:
            db.add(Company(user_id=company_user.id, name=COMPANY["name"], industry=COMPANY["industry"]))
            db.commit()
            print(f"created: {COMPANY['email']} (verifier)")
        else:
            print(f"skip (already exists): {COMPANY['email']}")

        print("\nDemo credentials (development only):")
        print(f"  student      {STUDENT['email']:<40} {STUDENT['password']}")
        print(f"  institution  {INSTITUTION['email']:<40} {INSTITUTION['password']}")
        print(f"  verifier     {COMPANY['email']:<40} {COMPANY['password']}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
