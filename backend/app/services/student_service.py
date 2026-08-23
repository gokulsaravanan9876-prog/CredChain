# ---------------------------------------------------------------------------
# University <-> Student relationship: the one place a student's
# institution_id is ever changed. Student.institution_id (see
# models/student.py) already existed as a nullable FK — this module is what
# was missing: a safe, server-validated way to SET it, instead of relying on
# a fake/mock link or an unchecked client-supplied UUID.
#
# The security invariant: a student can only ever be linked to an
# institution that genuinely exists as a row in the institutions table.
# There's no way to "invent" one — the id is checked with db.get() against
# the real table, exactly the same check issue_credential already relies on
# for the institution/student relationship in the other direction.
# ---------------------------------------------------------------------------

import uuid

from sqlalchemy.orm import Session

from ..models.institution import Institution
from ..models.student import Student


class InstitutionNotFoundError(Exception):
    pass


def link_student_to_institution(db: Session, student: Student, institution_id: uuid.UUID) -> Student:
    institution = db.get(Institution, institution_id)
    if institution is None:
        raise InstitutionNotFoundError()

    student.institution_id = institution.id
    db.add(student)
    db.commit()
    db.refresh(student)
    return student
