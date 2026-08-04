"""Unit tests for `app.core.security` - pure logic, no DB, no HTTP."""

from datetime import timedelta

import jwt
import pytest

from app.core.security import (
    TokenType,
    _create_token,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_hash_password_is_not_plaintext() -> None:
    hashed = hash_password("correct horse battery staple")
    assert hashed != "correct horse battery staple"


def test_verify_password_accepts_correct_password() -> None:
    hashed = hash_password("hunter2")
    assert verify_password("hunter2", hashed) is True


def test_verify_password_rejects_wrong_password() -> None:
    hashed = hash_password("hunter2")
    assert verify_password("wrong-password", hashed) is False


def test_access_token_round_trips_subject_and_type() -> None:
    token = create_access_token("user-123")
    claims = decode_token(token)
    assert claims["sub"] == "user-123"
    assert claims["type"] == TokenType.ACCESS.value


def test_refresh_token_round_trips_subject_and_type() -> None:
    token = create_refresh_token("user-123")
    claims = decode_token(token)
    assert claims["sub"] == "user-123"
    assert claims["type"] == TokenType.REFRESH.value


def test_token_carries_extra_claims() -> None:
    token = create_access_token("user-123", extra_claims={"cv": 3})
    claims = decode_token(token)
    assert claims["cv"] == 3


def test_two_tokens_for_same_subject_have_different_jti() -> None:
    token_a = create_access_token("user-123")
    token_b = create_access_token("user-123")
    assert decode_token(token_a)["jti"] != decode_token(token_b)["jti"]


def test_decode_token_rejects_tampered_signature() -> None:
    token = create_access_token("user-123")
    tampered = token[:-1] + ("A" if token[-1] != "A" else "B")
    with pytest.raises(jwt.PyJWTError):
        decode_token(tampered)


def test_decode_token_rejects_expired_token() -> None:
    # `_create_token` is the shared helper both create_access_token and
    # create_refresh_token delegate to - calling it directly with a negative
    # expiry is the simplest way to produce an already-expired token without
    # mocking the clock.
    token = _create_token("user-123", TokenType.ACCESS, timedelta(minutes=-5))

    with pytest.raises(jwt.ExpiredSignatureError):
        decode_token(token)
