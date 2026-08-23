# ---------------------------------------------------------------------------
# PS3 Phase C: student -> university certificate requests. Kept fully
# separate from the company -> student CredentialRequest model (see
# app/models/institution_certificate_request.py). The one invariant these
# tests exist to prove above all: a request is FULFILLED only when a real
# credential is actually issued for it — never merely on approval.
# ---------------------------------------------------------------------------

SAMPLE_PDF_BYTES = b"%PDF-1.4\n%cert-req\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"


def _auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _register_institution(client, email, name):
    resp = client.post(
        "/api/auth/register",
        json={"email": email, "password": "Password123", "full_name": "Cert Inst Admin", "role": "institution", "institution_name": name},
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    return {"token": body["access_token"], "institution_id": body["user"]["institution_id"]}


def _register_student(client, institution_id, email, identifier):
    resp = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "Password123",
            "full_name": f"Cert Student {identifier}",
            "role": "student",
            "student_identifier": identifier,
            "institution_id": institution_id,
        },
    )
    assert resp.status_code == 201, resp.text
    return {"token": resp.json()["access_token"], "student_id": resp.json()["user"]["student_id"]}


def test_student_can_create_and_list_own_certificate_request(client, db_session):
    inst = _register_institution(client, "cert-inst-1@test.credchain.dev", "Cert University 1")
    student = _register_student(client, inst["institution_id"], "cert-stu-1@test.credchain.dev", "CERT-STU-1")

    resp = client.post(
        "/api/students/me/certificate-requests",
        json={"institution_id": inst["institution_id"], "credential_type": "migration", "reason": "Higher studies abroad"},
        headers=_auth_header(student["token"]),
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["status"] == "pending"
    assert body["credential_type"] == "migration"

    list_resp = client.get("/api/students/me/certificate-requests", headers=_auth_header(student["token"]))
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1


def test_student_cannot_request_from_unaffiliated_institution(client, db_session):
    inst_a = _register_institution(client, "cert-inst-a@test.credchain.dev", "Cert University A")
    inst_b = _register_institution(client, "cert-inst-b@test.credchain.dev", "Cert University B")
    student = _register_student(client, inst_a["institution_id"], "cert-stu-a@test.credchain.dev", "CERT-STU-A")

    resp = client.post(
        "/api/students/me/certificate-requests",
        json={"institution_id": inst_b["institution_id"], "credential_type": "transcript"},
        headers=_auth_header(student["token"]),
    )
    assert resp.status_code == 403


def test_unlinked_student_cannot_request_any_certificate(client, db_session):
    inst = _register_institution(client, "cert-inst-unlinked@test.credchain.dev", "Cert Unlinked University")
    resp = client.post(
        "/api/auth/register",
        json={
            "email": "cert-stu-unlinked@test.credchain.dev",
            "password": "Password123",
            "full_name": "Unlinked Student",
            "role": "student",
            "student_identifier": "CERT-STU-UNLINKED",
        },
    )
    token = resp.json()["access_token"]

    req_resp = client.post(
        "/api/students/me/certificate-requests",
        json={"institution_id": inst["institution_id"], "credential_type": "transcript"},
        headers=_auth_header(token),
    )
    assert req_resp.status_code == 403


def test_institution_can_approve_and_reject(client, db_session):
    inst = _register_institution(client, "cert-inst-2@test.credchain.dev", "Cert University 2")
    student = _register_student(client, inst["institution_id"], "cert-stu-2@test.credchain.dev", "CERT-STU-2")

    r1 = client.post(
        "/api/students/me/certificate-requests",
        json={"institution_id": inst["institution_id"], "credential_type": "degree"},
        headers=_auth_header(student["token"]),
    ).json()
    r2 = client.post(
        "/api/students/me/certificate-requests",
        json={"institution_id": inst["institution_id"], "credential_type": "transcript"},
        headers=_auth_header(student["token"]),
    ).json()

    list_resp = client.get("/api/institutions/me/certificate-requests", headers=_auth_header(inst["token"]))
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 2

    approve_resp = client.post(f"/api/institutions/me/certificate-requests/{r1['id']}/approve", headers=_auth_header(inst["token"]))
    assert approve_resp.status_code == 200
    assert approve_resp.json()["status"] == "approved"

    reject_resp = client.post(
        f"/api/institutions/me/certificate-requests/{r2['id']}/reject",
        json={"reason": "Please submit through the registrar's office instead"},
        headers=_auth_header(inst["token"]),
    )
    assert reject_resp.status_code == 200
    assert reject_resp.json()["status"] == "rejected"
    assert reject_resp.json()["rejection_reason"] == "Please submit through the registrar's office instead"


def test_cross_institution_cannot_see_or_act_on_requests(client, db_session):
    inst_a = _register_institution(client, "cert-inst-xa@test.credchain.dev", "Cert University XA")
    inst_b = _register_institution(client, "cert-inst-xb@test.credchain.dev", "Cert University XB")
    student = _register_student(client, inst_a["institution_id"], "cert-stu-xa@test.credchain.dev", "CERT-STU-XA")

    req = client.post(
        "/api/students/me/certificate-requests",
        json={"institution_id": inst_a["institution_id"], "credential_type": "degree"},
        headers=_auth_header(student["token"]),
    ).json()

    list_resp = client.get("/api/institutions/me/certificate-requests", headers=_auth_header(inst_b["token"]))
    assert all(r["id"] != req["id"] for r in list_resp.json())

    approve_resp = client.post(f"/api/institutions/me/certificate-requests/{req['id']}/approve", headers=_auth_header(inst_b["token"]))
    assert approve_resp.status_code == 403


def test_request_is_fulfilled_only_after_real_issuance_not_on_approval(client, db_session):
    inst = _register_institution(client, "cert-inst-3@test.credchain.dev", "Cert University 3")
    student = _register_student(client, inst["institution_id"], "cert-stu-3@test.credchain.dev", "CERT-STU-3")

    req = client.post(
        "/api/students/me/certificate-requests",
        json={"institution_id": inst["institution_id"], "credential_type": "migration", "reason": "Transfer"},
        headers=_auth_header(student["token"]),
    ).json()

    approve_resp = client.post(f"/api/institutions/me/certificate-requests/{req['id']}/approve", headers=_auth_header(inst["token"]))
    assert approve_resp.json()["status"] == "approved"  # NOT fulfilled yet — approval alone never fulfills

    files = {"document": ("migration.pdf", SAMPLE_PDF_BYTES, "application/pdf")}
    issue_resp = client.post(
        "/api/institutions/me/credentials",
        data={
            "student_id": student["student_id"],
            "credential_type": "migration",
            "title": "Migration Certificate",
            "fulfills_request_id": req["id"],
        },
        files=files,
        headers=_auth_header(inst["token"]),
    )
    assert issue_resp.status_code == 201, issue_resp.text
    credential_id = issue_resp.json()["id"]

    list_resp = client.get("/api/institutions/me/certificate-requests", headers=_auth_header(inst["token"]))
    fulfilled = next(r for r in list_resp.json() if r["id"] == req["id"])
    assert fulfilled["status"] == "fulfilled"
    assert fulfilled["fulfilled_credential_id"] == credential_id


def test_fulfilling_someone_elses_request_is_rejected(client, db_session):
    inst_a = _register_institution(client, "cert-inst-fa@test.credchain.dev", "Cert University FA")
    inst_b = _register_institution(client, "cert-inst-fb@test.credchain.dev", "Cert University FB")
    student_a = _register_student(client, inst_a["institution_id"], "cert-stu-fa@test.credchain.dev", "CERT-STU-FA")
    student_b = _register_student(client, inst_b["institution_id"], "cert-stu-fb@test.credchain.dev", "CERT-STU-FB")

    req = client.post(
        "/api/students/me/certificate-requests",
        json={"institution_id": inst_a["institution_id"], "credential_type": "degree"},
        headers=_auth_header(student_a["token"]),
    ).json()
    client.post(f"/api/institutions/me/certificate-requests/{req['id']}/approve", headers=_auth_header(inst_a["token"]))

    files = {"document": ("x.pdf", SAMPLE_PDF_BYTES, "application/pdf")}
    # Institution B tries to fulfill institution A's request for its own (different) student.
    resp = client.post(
        "/api/institutions/me/credentials",
        data={
            "student_id": student_b["student_id"],
            "credential_type": "degree",
            "title": "Degree",
            "fulfills_request_id": req["id"],
        },
        files=files,
        headers=_auth_header(inst_b["token"]),
    )
    assert resp.status_code == 403
