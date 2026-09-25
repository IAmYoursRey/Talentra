import logging
from app.core.audit import AuditLogger
from app.domain.enums import AuditEventType
from app.domain.normalizers import normalize_login_identifier


def test_audit_logs_never_contain_sensitive_data(caplog):
    caplog.set_level(logging.INFO)
    logger = AuditLogger()

    # Log an event
    logger.log(
        event_type=AuditEventType.AUTH_LOGIN_SUCCESS,
        safe_context="Login successful for student user",
        user_id="usr_std_001",
        school_id="sch_teladan_001",
        correlation_id="corr-12345",
    )

    log_output = caplog.text

    # Assert that sensitive keywords and patterns are absent
    forbidden_terms = [
        "password",
        "PasswordSiswa123!",
        "talentra_session",
        "eyJh",  # JWT header prefix
        "0071234321",  # full NISN
        "198204152005011789",  # full NIP
        "4235760662200112",  # full NUPTK
    ]

    for term in forbidden_terms:
        assert term not in log_output, f"Security violation: found '{term}' in audit log output!"


def test_normalizer_masks_identifiers():
    res_nisn = normalize_login_identifier("0071234321")
    assert "0071234321" not in res_nisn.masked
    assert res_nisn.masked == "NISN: *******321"

    res_nip = normalize_login_identifier("198204152005011789")
    assert "198204152005011789" not in res_nip.masked
    assert res_nip.masked == "NIP: ***************789"

    res_nuptk = normalize_login_identifier("4235760662200112")
    assert "4235760662200112" not in res_nuptk.masked
    assert res_nuptk.masked == "NUPTK: *************112"

    res_npsn = normalize_login_identifier("20101543")
    assert "20101543" not in res_npsn.masked
    assert res_npsn.masked == "NPSN: *****543"
