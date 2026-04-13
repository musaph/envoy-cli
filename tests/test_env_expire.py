"""Tests for envoy.env_expire."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from envoy.env_expire import (
    EnvExpiryChecker,
    ExpiryEntry,
    ExpiryResult,
    ExpiryViolation,
)


NOW = datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def checker():
    entries = [
        ExpiryEntry(key="API_KEY", expires_at=datetime(2024, 6, 10, tzinfo=timezone.utc)),
        ExpiryEntry(key="DB_PASS", expires_at=datetime(2024, 6, 20, tzinfo=timezone.utc), notify_before_days=7),
        ExpiryEntry(key="TOKEN", expires_at=datetime(2024, 7, 1, tzinfo=timezone.utc), notify_before_days=3),
    ]
    return EnvExpiryChecker(entries)


class TestExpiryEntry:
    def test_to_dict_roundtrip(self):
        entry = ExpiryEntry(key="X", expires_at=datetime(2025, 1, 1, tzinfo=timezone.utc), notify_before_days=5)
        assert ExpiryEntry.from_dict(entry.to_dict()) == entry

    def test_repr_contains_key_and_date(self):
        entry = ExpiryEntry(key="MY_KEY", expires_at=datetime(2025, 3, 10, tzinfo=timezone.utc))
        assert "MY_KEY" in repr(entry)
        assert "2025-03-10" in repr(entry)


class TestExpiryViolation:
    def test_repr_expired(self):
        v = ExpiryViolation(key="K", expires_at=NOW, expired=True)
        assert "expired" in repr(v)

    def test_repr_expiring_soon(self):
        v = ExpiryViolation(key="K", expires_at=NOW, expired=False)
        assert "expiring soon" in repr(v)


class TestExpiryResult:
    def test_repr(self):
        r = ExpiryResult(violations=[], checked=3)
        assert "checked=3" in repr(r)

    def test_has_violations_false_when_empty(self):
        assert not ExpiryResult().has_violations

    def test_has_violations_true_when_populated(self):
        v = ExpiryViolation(key="K", expires_at=NOW, expired=True)
        assert ExpiryResult(violations=[v]).has_violations

    def test_expired_and_expiring_soon_filtered(self):
        expired = ExpiryViolation(key="A", expires_at=NOW, expired=True)
        soon = ExpiryViolation(key="B", expires_at=NOW, expired=False)
        result = ExpiryResult(violations=[expired, soon])
        assert result.expired == [expired]
        assert result.expiring_soon == [soon]


class TestEnvExpiryChecker:
    def test_no_entries_returns_empty(self, checker):
        result = checker.check({"UNTRACKED": "val"}, now=NOW)
        assert result.checked == 0
        assert not result.has_violations

    def test_expired_key_flagged(self, checker):
        result = checker.check({"API_KEY": "secret"}, now=NOW)
        assert result.checked == 1
        assert len(result.expired) == 1
        assert result.expired[0].key == "API_KEY"

    def test_expiring_soon_flagged(self, checker):
        result = checker.check({"DB_PASS": "pass"}, now=NOW)
        assert result.checked == 1
        assert len(result.expiring_soon) == 1
        assert result.expiring_soon[0].key == "DB_PASS"

    def test_not_expiring_soon_not_flagged(self, checker):
        result = checker.check({"TOKEN": "tok"}, now=NOW)
        assert result.checked == 1
        assert not result.has_violations

    def test_register_adds_entry(self):
        c = EnvExpiryChecker()
        c.register(ExpiryEntry(key="NEW", expires_at=datetime(2020, 1, 1, tzinfo=timezone.utc)))
        result = c.check({"NEW": "v"}, now=NOW)
        assert result.checked == 1
        assert result.expired[0].key == "NEW"

    def test_multiple_vars_checked(self, checker):
        vars_ = {"API_KEY": "a", "DB_PASS": "b", "TOKEN": "t"}
        result = checker.check(vars_, now=NOW)
        assert result.checked == 3
        assert len(result.expired) == 1
        assert len(result.expiring_soon) == 1
