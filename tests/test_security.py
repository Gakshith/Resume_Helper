"""Unit tests for the pure security helpers (rate limiting, headers, IP, password policy)."""
from collections import defaultdict, deque

import pytest
from pydantic import ValidationError

import security
from Models import Register


def _store():
    return defaultdict(deque)


def test_rate_limit_allows_up_to_limit():
    store = _store()
    for i in range(security.LOGIN_RATE_LIMIT):
        assert security.is_rate_limited("ip", now=1000 + i, store=store) is False


def test_rate_limit_blocks_over_limit():
    store = _store()
    for i in range(security.LOGIN_RATE_LIMIT):
        security.is_rate_limited("ip", now=1000 + i, store=store)
    assert security.is_rate_limited("ip", now=1000 + security.LOGIN_RATE_LIMIT, store=store) is True


def test_rate_limit_resets_after_window():
    store = _store()
    for i in range(security.LOGIN_RATE_LIMIT):
        security.is_rate_limited("ip", now=1000 + i, store=store)
    later = 1000 + security.LOGIN_RATE_WINDOW + 1
    assert security.is_rate_limited("ip", now=later, store=store) is False


def test_rate_limit_is_per_key():
    store = _store()
    for i in range(security.LOGIN_RATE_LIMIT):
        security.is_rate_limited("a", now=1000 + i, store=store)
    assert security.is_rate_limited("b", now=2000, store=store) is False


def test_security_headers_present_and_safe():
    h = security.SECURITY_HEADERS
    assert h["X-Content-Type-Options"] == "nosniff"
    assert h["X-Frame-Options"] == "SAMEORIGIN"
    csp = h["Content-Security-Policy"]
    assert "default-src 'self'" in csp
    assert "object-src 'none'" in csp
    assert "frame-ancestors 'self'" in csp


def test_client_ip_prefers_forwarded_for():
    assert security.client_ip("203.0.113.7, 10.0.0.1", "10.0.0.1") == "203.0.113.7"


def test_client_ip_falls_back_to_peer():
    assert security.client_ip(None, "198.51.100.4") == "198.51.100.4"
    assert security.client_ip("", "198.51.100.4") == "198.51.100.4"


def test_register_rejects_short_password():
    with pytest.raises(ValidationError):
        Register(UserName="alice", Password="1234567")  # 7 chars < 8


def test_register_accepts_strong_password():
    r = Register(UserName="alice", Password="strongpass1")
    assert r.UserName == "alice"
