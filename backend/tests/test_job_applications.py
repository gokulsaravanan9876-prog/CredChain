# ---------------------------------------------------------------------------
# Job marketplace Phase F/G/H/I/J/K: applications, document sharing (via the
# EXISTING credential-request/share pipeline), company dashboard privacy,
# real verification, requested-vs-received mismatch, and the decision
# workflow. This is the core "does the whole job-application trust chain
# actually work" test file.
# ---------------------------------------------------------------------------

SAMPLE_PDF_BYTES = b"%PDF-1.4\n%app\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"


def _auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _register_verifier(client, db_session, email, name):
    from app.models.company import Company

    company = Company(name=name)
    db_session.add(company)
    db_session.commit()
    db_session.refresh(company)
    resp = client.post(
        "/api/auth/register",
        json={"email": email, "password": "Password123", "full_name": "App Verifier", "role": "verifier", "company_id": str(company.id)},
    )
    body = resp.json()
    return {"token": body["access_token"], "company_id": body["user"]["company_id"]}


def _register_institution(client, db_session, email, name):
    from app.models.institution import Institution

    institution = Institution(name=name)
    db_session.add(institution)
    db_session.commit()
    db_session.refresh(institution)
    resp = client.post(
        "/api/auth/register",
        json={"email": email, "password": "Password123", "full_name": "App Inst", "role": "institution", "institution_id": str(institution.id)},
    )
    body = resp.json()
    return {"token": body["access_token"], "institution_id": body["user"]["institution_id"]}


def _register_student(client, institution_id, email, identifier):
    resp = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "Password123",
            "full_name": "App Student",
            "role": "student",
            "student_identifier": identifier,
            "institution_id": institution_id,
        },
    )
    body = resp.json()
    return {"token": body["access_token"], "student_id": body["user"]["student_id"]}


def _issue_credential(client, inst_token, student_id, credential_type, title):
    files = {"document": ("x.pdf", SAMPLE_PDF_BYTES, "application/pdf")}
    resp = client.post(
        "/api/institutions/me/credentials",
        data={"student_id": student_id, "credential_type": credential_type, "title": title},
        files=files,
        headers=_auth_header(inst_token),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def _create_open_job(client, verifier_token, **overrides):
    payload = {
        "title": "Software Engineer",
        "description": "Real job.",
        "employment_type": "full_time",
        "required_documents": ["Migration Certificate"],
    }
    payload.update(overrides)
    job = client.post("/api/companies/me/jobs", json=payload, headers=_auth_header(verifier_token)).json()
    client.post(f"/api/companies/me/jobs/{job['id']}/publish", headers=_auth_header(verifier_token))
    return job


def test_student_can_apply_with_owned_credential_and_see_it_in_my_applications(client, db_session):
    verifier = _register_verifier(client, db_session, "app-co-1@test.credchain.dev", "App Co 1")
    inst = _register_institution(client, db_session, "app-inst-1@test.credchain.dev", "App University 1")
    student = _register_student(client, inst["institution_id"], "app-stu-1@test.credchain.dev", "APP-STU-1")
    job = _create_open_job(client, verifier["token"])
    cred_id = _issue_credential(client, inst["token"], student["student_id"], "migration", "Migration Certificate")

    resp = client.post(
        "/api/students/me/applications", json={"job_id": job["id"], "credential_ids": [cred_id]}, headers=_auth_header(student["token"])
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["status"] == "applied"
    assert resp.json()["company_name"] == "App Co 1"

    list_resp = client.get("/api/students/me/applications", headers=_auth_header(student["token"]))
    assert len(list_resp.json()) == 1


def test_cannot_apply_twice_or_to_closed_or_nonexistent_job(client, db_session):
    import uuid

    verifier = _register_verifier(client, db_session, "app-co-2@test.credchain.dev", "App Co 2")
    inst = _register_institution(client, db_session, "app-inst-2@test.credchain.dev", "App University 2")
    student = _register_student(client, inst["institution_id"], "app-stu-2@test.credchain.dev", "APP-STU-2")
    job = _create_open_job(client, verifier["token"])
    cred_id = _issue_credential(client, inst["token"], student["student_id"], "migration", "Migration Certificate")

    first = client.post(
        "/api/students/me/applications", json={"job_id": job["id"], "credential_ids": [cred_id]}, headers=_auth_header(student["token"])
    )
    assert first.status_code == 201

    second = client.post(
        "/api/students/me/applications", json={"job_id": job["id"], "credential_ids": [cred_id]}, headers=_auth_header(student["token"])
    )
    assert second.status_code == 409

    closed_job = _create_open_job(client, verifier["token"], title="Closing Job")
    client.post(f"/api/companies/me/jobs/{closed_job['id']}/close", headers=_auth_header(verifier["token"]))
    closed_resp = client.post(
        "/api/students/me/applications", json={"job_id": closed_job["id"], "credential_ids": [cred_id]}, headers=_auth_header(student["token"])
    )
    assert closed_resp.status_code == 409

    missing_resp = client.post(
        "/api/students/me/applications", json={"job_id": str(uuid.uuid4()), "credential_ids": [cred_id]}, headers=_auth_header(student["token"])
    )
    assert missing_resp.status_code == 404


def test_company_sees_only_its_own_applicants_never_other_companies_or_all_students(client, db_session):
    verifier_a = _register_verifier(client, db_session, "app-co-a@test.credchain.dev", "App Co A")
    verifier_b = _register_verifier(client, db_session, "app-co-b@test.credchain.dev", "App Co B")
    inst = _register_institution(client, db_session, "app-inst-3@test.credchain.dev", "App University 3")
    student = _register_student(client, inst["institution_id"], "app-stu-3@test.credchain.dev", "APP-STU-3")
    job_a = _create_open_job(client, verifier_a["token"])
    cred_id = _issue_credential(client, inst["token"], student["student_id"], "migration", "Migration Certificate")

    client.post("/api/students/me/applications", json={"job_id": job_a["id"], "credential_ids": [cred_id]}, headers=_auth_header(student["token"]))

    a_apps = client.get("/api/companies/me/applications", headers=_auth_header(verifier_a["token"])).json()
    b_apps = client.get("/api/companies/me/applications", headers=_auth_header(verifier_b["token"])).json()
    assert len(a_apps) == 1
    assert len(b_apps) == 0


def test_company_sees_shared_credential_verify_flow_matching_case(client, db_session):
    verifier = _register_verifier(client, db_session, "app-co-4@test.credchain.dev", "App Co 4")
    inst = _register_institution(client, db_session, "app-inst-4@test.credchain.dev", "App University 4")
    student = _register_student(client, inst["institution_id"], "app-stu-4@test.credchain.dev", "APP-STU-4")
    job = _create_open_job(client, verifier["token"], required_documents=["Migration Certificate"])
    cred_id = _issue_credential(client, inst["token"], student["student_id"], "migration", "Migration Certificate")

    client.post("/api/students/me/applications", json={"job_id": job["id"], "credential_ids": [cred_id]}, headers=_auth_header(student["token"]))

    apps = client.get("/api/companies/me/applications", headers=_auth_header(verifier["token"])).json()
    app = apps[0]
    assert app["credential_request"]["requested_credentials"] == ["Migration Certificate"]
    assert app["credential_request"]["shared_credentials"][0]["credential_type"] == "migration"

    verify_resp = client.post("/api/verification/verify", json={"credential_id": cred_id}, headers=_auth_header(verifier["token"]))
    assert verify_resp.status_code == 200
    assert verify_resp.json()["result"] == "VERIFIED"


def test_wrong_credential_shared_produces_type_mismatch_not_verified(client, db_session):
    verifier = _register_verifier(client, db_session, "app-co-5@test.credchain.dev", "App Co 5")
    inst = _register_institution(client, db_session, "app-inst-5@test.credchain.dev", "App University 5")
    student = _register_student(client, inst["institution_id"], "app-stu-5@test.credchain.dev", "APP-STU-5")
    # Job requires Migration Certificate, but the student only shares a Degree.
    job = _create_open_job(client, verifier["token"], required_documents=["Migration Certificate"])
    degree_cred_id = _issue_credential(client, inst["token"], student["student_id"], "degree", "B.Tech Degree")

    apply_resp = client.post(
        "/api/students/me/applications", json={"job_id": job["id"], "credential_ids": [degree_cred_id]}, headers=_auth_header(student["token"])
    )
    assert apply_resp.status_code == 201

    apps = client.get("/api/companies/me/applications", headers=_auth_header(verifier["token"])).json()
    app = apps[0]
    assert app["credential_request"]["requested_credentials"] == ["Migration Certificate"]
    assert app["credential_request"]["shared_credentials"][0]["credential_type"] == "degree"

    verify_resp = client.post("/api/verification/verify", json={"credential_id": degree_cred_id}, headers=_auth_header(verifier["token"]))
    assert verify_resp.status_code == 200
    assert verify_resp.json()["result"] == "TYPE_MISMATCH"
    assert verify_resp.json()["result"] != "VERIFIED"


def test_company_decision_workflow_whitelisted_transitions(client, db_session):
    verifier = _register_verifier(client, db_session, "app-co-6@test.credchain.dev", "App Co 6")
    inst = _register_institution(client, db_session, "app-inst-6@test.credchain.dev", "App University 6")
    student = _register_student(client, inst["institution_id"], "app-stu-6@test.credchain.dev", "APP-STU-6")
    job = _create_open_job(client, verifier["token"])
    cred_id = _issue_credential(client, inst["token"], student["student_id"], "migration", "Migration Certificate")
    application = client.post(
        "/api/students/me/applications", json={"job_id": job["id"], "credential_ids": [cred_id]}, headers=_auth_header(student["token"])
    ).json()
    app_id = client.get("/api/companies/me/applications", headers=_auth_header(verifier["token"])).json()[0]["id"]

    step1 = client.post(f"/api/companies/me/applications/{app_id}/status", json={"status": "under_review"}, headers=_auth_header(verifier["token"]))
    assert step1.status_code == 200
    assert step1.json()["status"] == "under_review"

    # Cannot skip straight to accepted from under_review.
    invalid = client.post(f"/api/companies/me/applications/{app_id}/status", json={"status": "accepted"}, headers=_auth_header(verifier["token"]))
    assert invalid.status_code == 409

    step2 = client.post(f"/api/companies/me/applications/{app_id}/status", json={"status": "shortlisted"}, headers=_auth_header(verifier["token"]))
    assert step2.status_code == 200
    step3 = client.post(f"/api/companies/me/applications/{app_id}/status", json={"status": "accepted"}, headers=_auth_header(verifier["token"]))
    assert step3.status_code == 200
    assert step3.json()["status"] == "accepted"


def test_student_cannot_set_application_status_and_company_cannot_touch_others_application(client, db_session):
    verifier_a = _register_verifier(client, db_session, "app-co-x@test.credchain.dev", "App Co X")
    verifier_b = _register_verifier(client, db_session, "app-co-y@test.credchain.dev", "App Co Y")
    inst = _register_institution(client, db_session, "app-inst-7@test.credchain.dev", "App University 7")
    student = _register_student(client, inst["institution_id"], "app-stu-7@test.credchain.dev", "APP-STU-7")
    job = _create_open_job(client, verifier_a["token"])
    cred_id = _issue_credential(client, inst["token"], student["student_id"], "migration", "Migration Certificate")
    client.post("/api/students/me/applications", json={"job_id": job["id"], "credential_ids": [cred_id]}, headers=_auth_header(student["token"]))
    app_id = client.get("/api/companies/me/applications", headers=_auth_header(verifier_a["token"])).json()[0]["id"]

    # No student-facing route exists for this at all.
    student_attempt = client.post(f"/api/companies/me/applications/{app_id}/status", json={"status": "accepted"}, headers=_auth_header(student["token"]))
    assert student_attempt.status_code == 403

    other_company_attempt = client.post(
        f"/api/companies/me/applications/{app_id}/status", json={"status": "under_review"}, headers=_auth_header(verifier_b["token"])
    )
    assert other_company_attempt.status_code == 403
