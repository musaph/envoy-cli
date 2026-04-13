import pytest
from envoy.env_copy import CopyChange, CopyResult, EnvCopier


@pytest.fixture
def copier():
    return EnvCopier()


@pytest.fixture
def overwrite_copier():
    return EnvCopier(overwrite=True)


@pytest.fixture
def sample_vars():
    return {"DB_HOST": "localhost", "DB_PORT": "5432", "API_KEY": "secret"}


class TestCopyChange:
    def test_repr_no_overwrite(self):
        c = CopyChange("SRC", "DST", "val")
        assert "SRC" in repr(c)
        assert "DST" in repr(c)
        assert "overwritten" not in repr(c)

    def test_repr_with_overwrite(self):
        c = CopyChange("SRC", "DST", "val", overwritten=True)
        assert "overwritten" in repr(c)


class TestCopyResult:
    def test_repr(self):
        r = CopyResult()
        assert "CopyResult" in repr(r)

    def test_has_changes_false_when_empty(self):
        assert not CopyResult().has_changes

    def test_has_changes_true_when_populated(self):
        r = CopyResult(changes=[CopyChange("A", "B", "v")])
        assert r.has_changes

    def test_has_errors_false_when_empty(self):
        assert not CopyResult().has_errors

    def test_has_errors_true_when_populated(self):
        r = CopyResult(errors=["some error"])
        assert r.has_errors


class TestEnvCopier:
    def test_copy_single_key(self, copier, sample_vars):
        result = copier.copy(sample_vars, {"DB_HOST": "DB_HOST_COPY"})
        assert result.has_changes
        assert not result.has_errors
        assert result.changes[0].dest_key == "DB_HOST_COPY"
        assert result.changes[0].value == "localhost"

    def test_copy_missing_source_reports_error(self, copier, sample_vars):
        result = copier.copy(sample_vars, {"MISSING": "DEST"})
        assert not result.has_changes
        assert result.has_errors
        assert "MISSING" in result.errors[0]

    def test_copy_existing_dest_without_overwrite_reports_error(self, copier, sample_vars):
        result = copier.copy(sample_vars, {"DB_HOST": "DB_PORT"})
        assert not result.has_changes
        assert result.has_errors
        assert "overwrite" in result.errors[0]

    def test_copy_existing_dest_with_overwrite(self, overwrite_copier, sample_vars):
        result = overwrite_copier.copy(sample_vars, {"DB_HOST": "DB_PORT"})
        assert result.has_changes
        assert not result.has_errors
        assert result.changes[0].overwritten is True

    def test_copy_multiple_mappings(self, copier, sample_vars):
        result = copier.copy(sample_vars, {"DB_HOST": "DB_HOST_BACKUP", "API_KEY": "API_KEY_BACKUP"})
        assert len(result.changes) == 2
        assert not result.has_errors

    def test_copy_does_not_mutate_original(self, copier, sample_vars):
        original = sample_vars.copy()
        copier.copy(sample_vars, {"DB_HOST": "NEW_KEY"})
        assert sample_vars == original
