# ---------------------------------------------------------------------------
# Test fixtures: a dedicated `credchain_test` Postgres database (never the
# dev `credchain` database), created fresh from the current models at the
# start of the test session and dropped at the end. Each test runs inside
# its own transaction that's rolled back afterward, so tests can't leak
# state into each other regardless of order.
# ---------------------------------------------------------------------------

import os
import sys
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Must happen BEFORE any `from app...` import: app.config.settings is a
# module-level singleton built from the environment at import time, so
# these have to land before app.config (or anything importing it) is first
# imported — otherwise Phase 4 tests would write real key/document files
# into the dev backend/keys and backend/storage directories.
_TEST_KEYS_DIR = tempfile.mkdtemp(prefix="credchain_test_keys_")
_TEST_STORAGE_DIR = tempfile.mkdtemp(prefix="credchain_test_storage_")
os.environ["KEYS_PATH"] = _TEST_KEYS_DIR
os.environ["STORAGE_PATH"] = _TEST_STORAGE_DIR
# The test suite must be deterministic regardless of whatever a developer
# currently has in their local .env (e.g. AI_ENABLED=true with a real key
# for manual smoke testing) — tests that exercise the fallback path assume
# AI is off, and no test in this suite needs a real AI call.
os.environ["AI_ENABLED"] = "false"
# Same rationale as AI_ENABLED above — tests that exercise blockchain
# behavior construct a fake BlockchainClient explicitly (see
# test_blockchain_anchoring.py); no test should accidentally attempt a real
# network call because a developer's local .env has real testnet creds set.
os.environ["BLOCKCHAIN_ENABLED"] = "false"

from app import models  # noqa: E402,F401  (populates Base.metadata)
from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+psycopg2://credchain:credchain@localhost:5432/credchain_test",
)

engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def _test_schema():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    try:
        yield session
    finally:
        session.close()
        # A test that hits an unhandled exception mid-request (e.g. testing
        # that a failure rolls back cleanly) may have already caused this
        # transaction to end itself — only roll back if it's still ours to roll back.
        if transaction.is_active:
            transaction.rollback()
        connection.close()


@pytest.fixture()
def client(db_session):
    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
