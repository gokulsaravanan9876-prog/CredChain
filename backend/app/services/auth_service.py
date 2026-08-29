# ---------------------------------------------------------------------------
# Auth business logic — routes/auth.py stays thin and only translates these
# exceptions into HTTP responses.
# ---------------------------------------------------------------------------

from sqlalchemy.orm import Session

from ..models.company import Company
from ..models.enums import UserRole
from ..models.institution import Institution
from ..models.student import Student
from ..models.user import User
from ..schemas.auth import RegisterRequest
from ..security.password import hash_password, verify_password
from . import signing_service


class EmailAlreadyRegisteredError(Exception):
    pass


class MissingProfileFieldsError(Exception):
    pass


class InstitutionNotFoundError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


class InactiveAccountError(Exception):
    pass


class AdminSelfRegistrationError(Exception):
    """Raised if a registration payload requests role=admin — there is no public admin sign-up path (see backend/scripts/create_admin.py for the only supported provisioning route)."""


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email.lower()).first()


def register_user(db: Session, payload: RegisterRequest) -> User:
    """
    Creates the User row plus the matching role-specific profile row in one
    transaction (all-or-nothing — a failure partway through rolls back both).

    Institution and verifier(company) registration is open to anyone who
    calls this endpoint (same as student registration) and the account is
    immediately usable for login/browsing — but NOT for the two actions that
    require real trust: a new Institution/Company row is created with
    verification_status=PENDING (the model's default), and
    credential_service.issue_signed_credential / job_service.publish_job
    both refuse to act until an admin has approved the account (see
    services/admin_service.py, routes/admin.py). role=admin can never reach
    this function — see the AdminSelfRegistrationError check above; admin
    accounts are provisioned only via backend/scripts/create_admin.py.
    """
    if payload.role == UserRole.ADMIN:
        raise AdminSelfRegistrationError()
    if get_user_by_email(db, payload.email):
        raise EmailAlreadyRegisteredError()

    user = User(
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
        role=payload.role,
        is_active=True,
    )
    db.add(user)
    db.flush()  # assigns user.id without committing, so FK rows below can reference it

    if payload.role == UserRole.STUDENT:
        if not payload.student_identifier:
            raise MissingProfileFieldsError("student_identifier is required for student registration")
        institution_id = None
        if payload.institution_id is not None:
            # Same invariant as the manual link endpoint: only a real,
            # existing institution row can ever be linked — never trust the
            # client-supplied id as-is.
            if db.get(Institution, payload.institution_id) is None:
                raise InstitutionNotFoundError()
            institution_id = payload.institution_id
        db.add(Student(user_id=user.id, student_identifier=payload.student_identifier, institution_id=institution_id))

    elif payload.role == UserRole.INSTITUTION:
        if not payload.institution_name:
            raise MissingProfileFieldsError("institution_name is required for institution registration")
        institution = Institution(
            user_id=user.id,
            name=payload.institution_name,
            registration_number=payload.institution_registration_number,
        )
        db.add(institution)
        db.flush()  # assigns institution.id, needed as the signing-key filename
        # Gives every new institution a stable signing identity at creation
        # time rather than lazily on first issuance — ensure_institution_keypair
        # is idempotent, so this is safe to call unconditionally here.
        signing_service.ensure_institution_keypair(db, institution)

    elif payload.role == UserRole.VERIFIER:
        if not payload.company_name:
            raise MissingProfileFieldsError("company_name is required for verifier registration")
        db.add(
            Company(
                user_id=user.id,
                name=payload.company_name,
                industry=payload.company_industry,
                website=payload.company_website,
            )
        )

    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User:
    """
    Raises InvalidCredentialsError for both "no such user" and "wrong
    password" — deliberately the same error, so a failed login never reveals
    whether an email is registered. Inactive-account status is only checked
    (and reported distinctly) AFTER the password has already matched, so
    that signal can't be used to enumerate accounts either.
    """
    user = get_user_by_email(db, email)
    if user is None or not verify_password(password, user.password_hash):
        raise InvalidCredentialsError()
    if not user.is_active:
        raise InactiveAccountError()
    return user
