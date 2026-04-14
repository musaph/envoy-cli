"""Integration tests: archive with parser and exporter."""
import pytest
from envoy.parser import EnvParser
from envoy.env_archive import EnvArchiveManager
from envoy.export import EnvExporter


@pytest.fixture
def parser():
    return EnvParser


@pytest.fixture
def manager():
    return EnvArchiveManager()


@pytest.fixture
def exporter():
    return EnvExporter()


ENV_TEXT = """DB_HOST=localhost
DB_PORT=5432
APP_ENV=production
SECRET_KEY=supersecret
"""


class TestArchiveWithParser:
    def test_parse_then_archive_roundtrip(self, manager):
        vars_ = EnvParser.parse(ENV_TEXT)
        manager.save("v1", vars_)
        restored = manager.restore("v1")
        assert restored == vars_

    def test_multiple_snapshots_independent(self, manager):
        v1 = EnvParser.parse("A=1\nB=2\n")
        v2 = EnvParser.parse("A=10\nC=3\n")
        manager.save("snap1", v1)
        manager.save("snap2", v2)
        assert manager.restore("snap1")["A"] == "1"
        assert manager.restore("snap2")["A"] == "10"
        assert "C" not in manager.restore("snap1")

    def test_archive_then_export_shell(self, manager, exporter):
        vars_ = EnvParser.parse(ENV_TEXT)
        manager.save("prod", vars_)
        restored = manager.restore("prod")
        result = exporter.export(restored, fmt="shell")
        assert result.format == "shell"
        assert "DB_HOST" in result.render()
        assert "export" in result.render()

    def test_checksum_stable_across_serialization(self, manager):
        vars_ = EnvParser.parse(ENV_TEXT)
        entry = manager.save("v1", vars_)
        original_checksum = entry.checksum
        data = manager.to_dict_list()
        new_mgr = EnvArchiveManager()
        new_mgr.load_from_dict_list(data)
        entries = new_mgr.list_entries()
        assert entries[0].checksum == original_checksum
