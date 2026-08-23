"""
Development data reset — clears accumulated demo/test ROWS from the local
dev database. Does NOT touch schema, migrations, or tables themselves.

Explicitly does NOT:
  - DROP TABLE
  - DROP DATABASE
  - touch alembic_version / migration history
  - remove any feature, model, route, or test

Deletes rows only, in FK-safe order (children before parents), then removes
the on-disk artifact files those rows referenced (issued credential PDFs,
uploaded student documents, signing keys) — these are dev artifacts, not
schema.

Safety: refuses to run against any DATABASE_URL that doesn't look like a
local dev database (localhost/127.0.0.1 host). Run with --yes to skip the
interactive confirmation prompt.
"""

import argparse
import shutil
import sys
from pathlib import Path
from urllib.parse import urlparse

import sqlalchemy as sa

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings  # noqa: E402
from app.database import engine  # noqa: E402

# Children first, parents last.
TABLES_IN_DELETE_ORDER = [
    "verification_events",
    "activity_logs",
    "share_grant_credentials",
    "share_grants",
    "job_applications",
    "jobs",
    "credential_requests",
    "student_documents",
    "institution_certificate_requests",
    "credential_documents",
    "credentials",
    "students",
    "institutions",
    "companies",
    "users",
]

STORAGE_DIRS = [
    Path(__file__).resolve().parent.parent / "storage" / "credentials",
    Path(__file__).resolve().parent.parent / "storage" / "student_documents",
]


def _is_local_db(url: str) -> bool:
    host = urlparse(url.replace("postgresql+psycopg2", "postgresql")).hostname
    return host in ("localhost", "127.0.0.1")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--yes", action="store_true", help="skip interactive confirmation")
    args = parser.parse_args()

    db_url = settings.database_url
    print(f"DATABASE_URL: {db_url}")

    if not _is_local_db(db_url):
        print("REFUSING: DATABASE_URL does not point at localhost/127.0.0.1. Aborting.")
        sys.exit(1)

    with engine.connect() as conn:
        print("\nRow counts before reset:")
        counts_before = {}
        for table in TABLES_IN_DELETE_ORDER:
            count = conn.execute(sa.text(f'SELECT COUNT(*) FROM "{table}"')).scalar()
            counts_before[table] = count
            print(f"  {table}: {count}")

    if not args.yes:
        answer = input("\nDelete all rows above from the LOCAL DEV database shown? Type 'yes' to proceed: ")
        if answer.strip().lower() != "yes":
            print("Aborted — no changes made.")
            sys.exit(0)

    with engine.begin() as conn:
        for table in TABLES_IN_DELETE_ORDER:
            conn.execute(sa.text(f'DELETE FROM "{table}"'))
        print("\nAll rows deleted (schema, tables, and migrations untouched).")

    with engine.connect() as conn:
        print("\nRow counts after reset:")
        for table in TABLES_IN_DELETE_ORDER:
            count = conn.execute(sa.text(f'SELECT COUNT(*) FROM "{table}"')).scalar()
            print(f"  {table}: {count}")

    for d in STORAGE_DIRS:
        if d.exists():
            for f in d.iterdir():
                if f.is_file():
                    f.unlink()
            print(f"Cleared files in {d}")


if __name__ == "__main__":
    main()
