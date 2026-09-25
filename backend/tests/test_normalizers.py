import pytest
from app.domain.normalizers import normalize_login_identifier
from app.domain.enums import IdentifierType


def test_valid_10_digit_nisn_with_leading_zero():
    # Crucial rule: NISN leading zero MUST be preserved as string
    raw = "0071234321"
    res = normalize_login_identifier(raw)
    assert res.identifier_type == IdentifierType.NISN
    assert res.normalized == "0071234321"
    assert isinstance(res.normalized, str)
    assert res.normalized.startswith("00")
    assert "0071234321" not in res.masked
    assert res.masked.endswith("321")


def test_invalid_nisn_length():
    with pytest.raises(ValueError):
        normalize_login_identifier("123456789")  # 9 digits

    with pytest.raises(ValueError):
        normalize_login_identifier("12345678901")  # 11 digits


def test_valid_16_digit_nuptk():
    raw = "1234567890123456"
    res = normalize_login_identifier(raw)
    assert res.identifier_type == IdentifierType.NUPTK
    assert res.normalized == "1234567890123456"
    assert res.masked.endswith("456")


def test_valid_18_digit_nip():
    raw = "198204152005011789"
    res = normalize_login_identifier(raw)
    assert res.identifier_type == IdentifierType.NIP
    assert res.normalized == "198204152005011789"
    assert res.masked.endswith("789")


def test_invalid_teacher_identifier_lengths():
    with pytest.raises(ValueError):
        normalize_login_identifier("123456789012345")  # 15 digits

    with pytest.raises(ValueError):
        normalize_login_identifier("12345678901234567")  # 17 digits


def test_valid_8_character_alphanumeric_npsn():
    # Numeric NPSN
    res1 = normalize_login_identifier("20101543")
    assert res1.identifier_type == IdentifierType.NPSN
    assert res1.normalized == "20101543"

    # Alphanumeric NPSN with lowercase input normalized to uppercase
    res2 = normalize_login_identifier("ab101543")
    assert res2.identifier_type == IdentifierType.NPSN
    assert res2.normalized == "AB101543"
    assert res2.masked.endswith("543")


def test_invalid_npsn_length():
    with pytest.raises(ValueError):
        normalize_login_identifier("2010154")  # 7 chars

    with pytest.raises(ValueError):
        normalize_login_identifier("201015439")  # 9 chars


def test_invalid_characters_and_empty():
    with pytest.raises(ValueError):
        normalize_login_identifier("")

    with pytest.raises(ValueError):
        normalize_login_identifier("!@#$%^&*()")


def test_valid_email_identifier():
    raw = "raihanansari6678@gmail.com"
    res = normalize_login_identifier(raw)
    assert res.identifier_type == IdentifierType.EMAIL
    assert res.normalized == "raihanansari6678@gmail.com"
    assert "EMAIL:" in res.masked
    assert "*******" in res.masked
    assert res.masked.endswith("@gmail.com")

