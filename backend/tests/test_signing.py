# ---------------------------------------------------------------------------
# Cryptographic round-trip tests — no HTTP/DB involved, pure signing-service
# and payload-canonicalization tests. This is the "prove the signature
# actually protects the content" test called out explicitly in the Phase 4
# spec (section 21).
# ---------------------------------------------------------------------------

from datetime import datetime, timezone

from app.security import signatures
from app.services.credential_payload import build_canonical_credential_payload, canonicalize_credential_payload


def _sample_payload(cgpa: float = 8.7) -> dict:
    return build_canonical_credential_payload(
        credential_identifier="CRD-test-0001",
        student_identifier="XYZ-2026-CS-014",
        student_name="Rahul Kumar",
        institution_identifier="inst-uuid-1234",
        institution_name="XYZ University",
        credential_type="transcript",
        title="Final Transcript",
        degree="B.Tech Computer Science",
        graduation_year=2026,
        cgpa=cgpa,
        document_hash="a" * 64,
        issued_at=datetime(2026, 8, 22, 10, 0, 0, tzinfo=timezone.utc),
    )


# --- canonicalization determinism (test 10) ---------------------------------


def test_canonical_payload_is_deterministic():
    payload_a = _sample_payload()
    payload_b = _sample_payload()
    assert canonicalize_credential_payload(payload_a) == canonicalize_credential_payload(payload_b)


def test_canonical_payload_is_not_python_dict_repr():
    payload = _sample_payload()
    canonical = canonicalize_credential_payload(payload)
    assert canonical != str(payload).encode("utf-8")
    # sorted keys, compact separators, valid JSON
    import json

    parsed = json.loads(canonical)
    assert parsed == payload


def test_canonical_payload_key_order_does_not_affect_bytes():
    payload_a = _sample_payload()
    # Same logical content, different insertion order.
    payload_b = {k: payload_a[k] for k in reversed(list(payload_a.keys()))}
    assert canonicalize_credential_payload(payload_a) == canonicalize_credential_payload(payload_b)


# --- signature round-trip (test 11, and the critical test in section 21) ----


def test_sign_and_verify_round_trip():
    private_pem, public_pem = signatures.generate_keypair()
    payload = _sample_payload()
    canonical = canonicalize_credential_payload(payload)

    signature = signatures.sign(private_pem, canonical)

    assert signatures.verify(public_pem, canonical, signature) is True


def test_signature_invalid_after_payload_tampered():
    """The critical test: sign CGPA 8.7, then re-canonicalize with CGPA 9.7 — the original signature must fail."""
    private_pem, public_pem = signatures.generate_keypair()

    original_payload = _sample_payload(cgpa=8.7)
    original_canonical = canonicalize_credential_payload(original_payload)
    signature = signatures.sign(private_pem, original_canonical)

    # sanity: the untampered signature verifies
    assert signatures.verify(public_pem, original_canonical, signature) is True

    tampered_payload = _sample_payload(cgpa=9.7)
    tampered_canonical = canonicalize_credential_payload(tampered_payload)

    assert signatures.verify(public_pem, tampered_canonical, signature) is False


def test_signature_changes_when_payload_changes(): # test 12
    private_pem, _ = signatures.generate_keypair()

    sig_a = signatures.sign(private_pem, canonicalize_credential_payload(_sample_payload(cgpa=8.7)))
    sig_b = signatures.sign(private_pem, canonicalize_credential_payload(_sample_payload(cgpa=9.7)))

    assert sig_a != sig_b


def test_verify_fails_with_wrong_public_key():
    private_pem, _ = signatures.generate_keypair()
    _, other_public_pem = signatures.generate_keypair()

    payload = _sample_payload()
    canonical = canonicalize_credential_payload(payload)
    signature = signatures.sign(private_pem, canonical)

    assert signatures.verify(other_public_pem, canonical, signature) is False


# --- document hashing (test 8) ------------------------------------------------


def test_sha256_hash_is_deterministic():
    from app.services.document_service import compute_sha256

    data = b"%PDF-1.4\n%test document bytes\n"
    assert compute_sha256(data) == compute_sha256(data)
    assert len(compute_sha256(data)) == 64


def test_sha256_hash_changes_with_content():
    from app.services.document_service import compute_sha256

    assert compute_sha256(b"%PDF-1.4\noriginal") != compute_sha256(b"%PDF-1.4\nmodified")
