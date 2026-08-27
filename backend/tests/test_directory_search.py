# ---------------------------------------------------------------------------
# Institution/Company/Job discovery directory (Phase 1 job-discovery work).
#
# Covers: directory-only rows (user_id=None, as scripts/seed_directory.py
# creates them) show up in the same public listings as real registered
# institutions/companies with no special-casing; search/location/industry/
# degree/company_id filters actually narrow results server-side; a
# nonexistent institution 404s; open_positions_count on a company reflects
# real OPEN jobs only (never draft/closed).
# ---------------------------------------------------------------------------

import uuid

from app.models.company import Company
from app.models.institution import Institution


def _auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _register_verifier(client, email, name):
    resp = client.post(
        "/api/auth/register",
        json={"email": email, "password": "Password123", "full_name": "Dir Verifier", "role": "verifier", "company_name": name},
    )
    body = resp.json()
    return {"token": body["access_token"], "company_id": body["user"]["company_id"]}


def _register_student(client, email, identifier):
    resp = client.post(
        "/api/auth/register",
        json={"email": email, "password": "Password123", "full_name": "Dir Student", "role": "student", "student_identifier": identifier},
    )
    body = resp.json()
    return {"token": body["access_token"], "student_id": body["user"]["student_id"]}


def _job_payload(**overrides):
    payload = {
        "title": "Software Engineer",
        "description": "Build real things.",
        "employment_type": "full_time",
        "required_degree": "B.Tech Computer Science",
        "minimum_cgpa": 7.5,
        "graduation_year_requirement": 2026,
        "required_skills": [],
        "required_documents": [],
    }
    payload.update(overrides)
    return payload


def _directory_institution(db_session, name: str, location: str | None = None, institution_type: str | None = None) -> Institution:
    """Mirrors what scripts/seed_directory.py inserts: a real row, no login (user_id=None)."""
    inst = Institution(user_id=None, name=name, location=location, institution_type=institution_type)
    db_session.add(inst)
    db_session.commit()
    db_session.refresh(inst)
    return inst


def _directory_company(db_session, name: str, industry: str | None = None, location: str | None = None) -> Company:
    comp = Company(user_id=None, name=name, industry=industry, location=location)
    db_session.add(comp)
    db_session.commit()
    db_session.refresh(comp)
    return comp


# ---- Institutions -----------------------------------------------------------


def test_directory_only_institution_is_publicly_listed_and_never_a_login_account(client, db_session):
    inst = _directory_institution(db_session, "Directory Only University", location="Nowhere City, Testland")

    list_resp = client.get("/api/institutions")
    assert list_resp.status_code == 200
    names = [i["name"] for i in list_resp.json()]
    assert "Directory Only University" in names

    detail_resp = client.get(f"/api/institutions/{inst.id}")
    assert detail_resp.status_code == 200
    assert detail_resp.json()["location"] == "Nowhere City, Testland"


def test_institution_search_matches_name_and_location_case_insensitively(client, db_session):
    _directory_institution(db_session, "Zeta Institute of Technology", location="Springfield, Testland")
    _directory_institution(db_session, "Unrelated College", location="Elsewhere, Testland")

    by_name = client.get("/api/institutions", params={"search": "zeta"})
    assert by_name.status_code == 200
    names = [i["name"] for i in by_name.json()]
    assert "Zeta Institute of Technology" in names
    assert "Unrelated College" not in names

    by_location = client.get("/api/institutions", params={"search": "Springfield"})
    names = [i["name"] for i in by_location.json()]
    assert "Zeta Institute of Technology" in names
    assert "Unrelated College" not in names


def test_institution_search_with_no_match_returns_empty_list_not_error(client, db_session):
    resp = client.get("/api/institutions", params={"search": "Definitely Not A Real Institution Name XYZ"})
    assert resp.status_code == 200
    assert resp.json() == []


def test_nonexistent_institution_returns_404(client, db_session):
    resp = client.get(f"/api/institutions/{uuid.uuid4()}")
    assert resp.status_code == 404


# ---- Companies ----------------------------------------------------------------


def test_directory_only_company_is_publicly_listed_alongside_registered_companies(client, db_session):
    _directory_company(db_session, "Directory Only Corp", industry="Testing", location="Test City")
    verifier = _register_verifier(client, "dir-search-co@test.credchain.dev", "Registered Search Co")

    resp = client.get("/api/companies")
    assert resp.status_code == 200
    names = [c["name"] for c in resp.json()]
    assert "Directory Only Corp" in names
    assert "Registered Search Co" in names
    assert verifier["company_id"] is not None


def test_company_search_industry_and_location_filters(client, db_session):
    _directory_company(db_session, "Filter Target Robotics", industry="Robotics", location="Pune, Maharashtra, India")
    _directory_company(db_session, "Filter Other Bank", industry="Banking", location="Mumbai, Maharashtra, India")

    by_search = client.get("/api/companies", params={"search": "Robotics"})
    names = [c["name"] for c in by_search.json()]
    assert "Filter Target Robotics" in names
    assert "Filter Other Bank" not in names

    by_industry = client.get("/api/companies", params={"industry": "Robotics"})
    names = [c["name"] for c in by_industry.json()]
    assert "Filter Target Robotics" in names
    assert "Filter Other Bank" not in names

    by_location = client.get("/api/companies", params={"location": "Pune"})
    names = [c["name"] for c in by_location.json()]
    assert "Filter Target Robotics" in names
    assert "Filter Other Bank" not in names


def test_company_open_positions_count_reflects_only_open_jobs(client, db_session):
    verifier = _register_verifier(client, "dir-openjobs@test.credchain.dev", "Open Jobs Co")

    draft = client.post("/api/companies/me/jobs", json=_job_payload(title="Draft Role"), headers=_auth_header(verifier["token"])).json()
    open_job = client.post("/api/companies/me/jobs", json=_job_payload(title="Open Role"), headers=_auth_header(verifier["token"])).json()
    client.post(f"/api/companies/me/jobs/{open_job['id']}/publish", headers=_auth_header(verifier["token"]))

    detail = client.get(f"/api/companies/{verifier['company_id']}")
    assert detail.status_code == 200
    assert detail.json()["open_positions_count"] == 1  # only open_job is published; draft stays draft

    listing = client.get("/api/companies", params={"search": "Open Jobs Co"}).json()
    assert listing[0]["open_positions_count"] == 1
    assert draft["status"] == "draft"


# ---- Jobs -----------------------------------------------------------------------


def test_job_company_id_search_and_degree_filters(client, db_session):
    verifier_a = _register_verifier(client, "dir-job-co-a@test.credchain.dev", "Job Filter Co A")
    verifier_b = _register_verifier(client, "dir-job-co-b@test.credchain.dev", "Job Filter Co B")
    student = _register_student(client, "dir-job-student@test.credchain.dev", "DIR-JOB-STU-1")

    job_a = client.post(
        "/api/companies/me/jobs",
        json=_job_payload(title="Backend Engineer", required_degree="B.Tech Computer Science"),
        headers=_auth_header(verifier_a["token"]),
    ).json()
    client.post(f"/api/companies/me/jobs/{job_a['id']}/publish", headers=_auth_header(verifier_a["token"]))

    job_b = client.post(
        "/api/companies/me/jobs",
        json=_job_payload(title="Mechanical Design Engineer", required_degree="B.Tech Mechanical Engineering"),
        headers=_auth_header(verifier_b["token"]),
    ).json()
    client.post(f"/api/companies/me/jobs/{job_b['id']}/publish", headers=_auth_header(verifier_b["token"]))

    by_company = client.get("/api/jobs", params={"company_id": verifier_a["company_id"]}, headers=_auth_header(student["token"]))
    assert by_company.status_code == 200
    titles = [j["title"] for j in by_company.json()]
    assert "Backend Engineer" in titles
    assert "Mechanical Design Engineer" not in titles

    by_search = client.get("/api/jobs", params={"search": "Backend"}, headers=_auth_header(student["token"]))
    titles = [j["title"] for j in by_search.json()]
    assert "Backend Engineer" in titles
    assert "Mechanical Design Engineer" not in titles

    # The student Jobs page has always let a student search by company name too (client-side,
    # pre-existing) — the backend `search` filter has to match that behavior now that Jobs.tsx
    # routes its search box through this endpoint instead of filtering an already-fetched array.
    by_company_name = client.get("/api/jobs", params={"search": "Job Filter Co B"}, headers=_auth_header(student["token"]))
    titles = [j["title"] for j in by_company_name.json()]
    assert "Mechanical Design Engineer" in titles
    assert "Backend Engineer" not in titles

    by_degree = client.get("/api/jobs", params={"degree": "Mechanical"}, headers=_auth_header(student["token"]))
    titles = [j["title"] for j in by_degree.json()]
    assert "Mechanical Design Engineer" in titles
    assert "Backend Engineer" not in titles
