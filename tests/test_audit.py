"""Tests for the audit logging module."""

import json
import pytest
from pathlib import Path

from envoy.audit import AuditEntry, AuditLog


@pytest.fixture
def temp_log_dir(tmp_path):
    return str(tmp_path / "audit_test")


@pytest.fixture
def audit_log(temp_log_dir):
    return AuditLog(log_dir=temp_log_dir)


class TestAuditEntry:
    def test_entry_creation(self):
        entry = AuditEntry(action="push", key="myapp/prod", environment="prod", user="alice")
        assert entry.action == "push"
        assert entry.key == "myapp/prod"
        assert entry.environment == "prod"
        assert entry.user == "alice"
        assert entry.timestamp is not None

    def test_entry_to_dict(self):
        entry = AuditEntry(action="pull", key="myapp/staging", environment="staging", user="bob")
        d = entry.to_dict()
        assert d["action"] == "pull"
        assert d["key"] == "myapp/staging"
        assert d["environment"] == "staging"
        assert d["user"] == "bob"
        assert "timestamp" in d

    def test_entry_from_dict_roundtrip(self):
        original = AuditEntry(action="delete", key="myapp/dev", environment="dev", user="carol")
        restored = AuditEntry.from_dict(original.to_dict())
        assert restored.action == original.action
        assert restored.key == original.key
        assert restored.environment == original.environment
        assert restored.user == original.user
        assert restored.timestamp == original.timestamp

    def test_entry_repr(self):
        entry = AuditEntry(action="push", key="app/prod", environment="prod", user="dave")
        repr_str = repr(entry)
        assert "PUSH" in repr_str
        assert "app/prod" in repr_str
        assert "prod" in repr_str
        assert "dave" in repr_str


class TestAuditLog:
    def test_record_creates_log_file(self, audit_log, temp_log_dir):
        audit_log.record("push", "myapp/prod", "prod", user="alice")
        log_file = Path(temp_log_dir) / "audit.log"
        assert log_file.exists()

    def test_record_and_read_all(self, audit_log):
        audit_log.record("push", "myapp/prod", "prod", user="alice")
        audit_log.record("pull", "myapp/staging", "staging", user="bob")
        entries = audit_log.read_all()
        assert len(entries) == 2
        assert entries[0].action == "push"
        assert entries[1].action == "pull"

    def test_read_all_empty_log(self, audit_log):
        entries = audit_log.read_all()
        assert entries == []

    def test_filter_by_environment(self, audit_log):
        audit_log.record("push", "myapp/prod", "prod", user="alice")
        audit_log.record("push", "myapp/staging", "staging", user="alice")
        audit_log.record("pull", "myapp/prod", "prod", user="bob")
        prod_entries = audit_log.filter_by_environment("prod")
        assert len(prod_entries) == 2
        assert all(e.environment == "prod" for e in prod_entries)

    def test_filter_by_action(self, audit_log):
        audit_log.record("push", "myapp/prod", "prod", user="alice")
        audit_log.record("pull", "myapp/prod", "prod", user="bob")
        audit_log.record("push", "myapp/staging", "staging", user="carol")
        push_entries = audit_log.filter_by_action("push")
        assert len(push_entries) == 2
        assert all(e.action == "push" for e in push_entries)

    def test_clear_removes_log(self, audit_log, temp_log_dir):
        audit_log.record("push", "myapp/prod", "prod", user="alice")
        audit_log.clear()
        log_file = Path(temp_log_dir) / "audit.log"
        assert not log_file.exists()
        assert audit_log.read_all() == []

    def test_log_entries_are_valid_json(self, audit_log, temp_log_dir):
        audit_log.record("push", "myapp/prod", "prod", user="alice")
        log_file = Path(temp_log_dir) / "audit.log"
        with open(log_file) as f:
            for line in f:
                data = json.loads(line.strip())
                assert "action" in data
                assert "timestamp" in data
