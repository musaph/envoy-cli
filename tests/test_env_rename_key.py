import pytest
from envoy.env_rename_key import EnvKeyRenamer, RenameKeyChange, RenameKeyResult


@pytest.fixture
def renamer():
    return EnvKeyRenamer()


@pytest.fixture
def overwrite_renamer():
    return EnvKeyRenamer(overwrite=True)


@pytest.fixture
def sample_vars():
    return {"DB_HOST": "localhost", "DB_PORT": "5432", "APP_SECRET": "abc123"}


class TestRenameKeyResult:
    def test_repr(self):
        r = RenameKeyResult()
        assert "RenameKeyResult" in repr(r)
        assert "changes=0" in repr(r)

    def test_has_changes_false_when_empty(self):
        r = RenameKeyResult()
        assert not r.has_changes

    def test_has_changes_true_when_populated(self):
        r = RenameKeyResult(changes=[RenameKeyChange("A", "B", "val")])
        assert r.has_changes

    def test_has_errors_false_when_empty(self):
        r = RenameKeyResult()
        assert not r.has_errors

    def test_has_errors_true_when_populated(self):
        r = RenameKeyResult(errors=["some error"])
        assert r.has_errors

    def test_renamed_keys_returns_old_keys(self):
        r = RenameKeyResult(changes=[RenameKeyChange("OLD", "NEW", "v")])
        assert r.renamed_keys == ["OLD"]


class TestEnvKeyRenamer:
    def test_rename_single_key(self, renamer, sample_vars):
        result = renamer.rename(sample_vars, {"DB_HOST": "DATABASE_HOST"})
        assert len(result.changes) == 1
        assert result.changes[0].old_key == "DB_HOST"
        assert result.changes[0].new_key == "DATABASE_HOST"
        assert result.changes[0].value == "localhost"

    def test_rename_multiple_keys(self, renamer, sample_vars):
        result = renamer.rename(sample_vars, {"DB_HOST": "DATABASE_HOST", "DB_PORT": "DATABASE_PORT"})
        assert len(result.changes) == 2

    def test_missing_key_is_skipped(self, renamer, sample_vars):
        result = renamer.rename(sample_vars, {"MISSING_KEY": "NEW_KEY"})
        assert "MISSING_KEY" in result.skipped
        assert not result.has_changes

    def test_same_key_is_skipped(self, renamer, sample_vars):
        result = renamer.rename(sample_vars, {"DB_HOST": "DB_HOST"})
        assert "DB_HOST" in result.skipped
        assert not result.has_changes

    def test_conflict_without_overwrite_produces_error(self, renamer, sample_vars):
        result = renamer.rename(sample_vars, {"DB_HOST": "DB_PORT"})
        assert result.has_errors
        assert not result.has_changes

    def test_conflict_with_overwrite_succeeds(self, overwrite_renamer, sample_vars):
        result = overwrite_renamer.rename(sample_vars, {"DB_HOST": "DB_PORT"})
        assert result.has_changes
        assert not result.has_errors

    def test_apply_returns_updated_dict(self, renamer, sample_vars):
        updated = renamer.apply(sample_vars, {"DB_HOST": "DATABASE_HOST"})
        assert "DATABASE_HOST" in updated
        assert "DB_HOST" not in updated
        assert updated["DATABASE_HOST"] == "localhost"

    def test_apply_preserves_other_keys(self, renamer, sample_vars):
        updated = renamer.apply(sample_vars, {"DB_HOST": "DATABASE_HOST"})
        assert "DB_PORT" in updated
        assert "APP_SECRET" in updated

    def test_rename_change_repr(self):
        c = RenameKeyChange("OLD", "NEW", "value")
        assert "OLD" in repr(c)
        assert "NEW" in repr(c)
