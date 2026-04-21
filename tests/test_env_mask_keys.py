import pytest
from envoy.env_mask_keys import EnvKeyMasker, MaskKeyChange, MaskKeyResult


@pytest.fixture
def masker():
    return EnvKeyMasker()


@pytest.fixture
def selective_masker():
    return EnvKeyMasker(keys=["SECRET_KEY", "API_TOKEN"])


@pytest.fixture
def sample_vars():
    return {
        "API_TOKEN": "abc123",
        "DATABASE_URL": "postgres://localhost",
        "SECRET_KEY": "supersecret",
        "PORT": "8080",
    }


class TestMaskKeyResult:
    def test_repr(self):
        r = MaskKeyResult()
        assert "MaskKeyResult" in repr(r)
        assert "has_changes=False" in repr(r)

    def test_has_changes_false_when_empty(self):
        r = MaskKeyResult()
        assert not r.has_changes()

    def test_has_changes_true_when_populated(self):
        r = MaskKeyResult(changes=[MaskKeyChange("K", "K", "K*")])
        assert r.has_changes()

    def test_changed_keys_returns_list(self):
        r = MaskKeyResult(changes=[MaskKeyChange("API_KEY", "API_KEY", "AP*****")])
        assert r.changed_keys() == ["API_KEY"]


class TestEnvKeyMasker:
    def test_masks_all_keys_by_default(self, masker, sample_vars):
        result = masker.mask(sample_vars)
        assert result.has_changes()
        for key in sample_vars:
            if len(key) > masker.visible_chars:
                assert key not in result.masked

    def test_visible_chars_preserved(self, masker, sample_vars):
        result = masker.mask(sample_vars)
        for change in result.changes:
            assert change.masked_key.startswith(change.original_key[: masker.visible_chars])

    def test_selective_masker_only_masks_specified_keys(self, selective_masker, sample_vars):
        result = selective_masker.mask(sample_vars)
        assert "DATABASE_URL" in result.masked
        assert "PORT" in result.masked
        assert "DATABASE_URL" not in [c.original_key for c in result.changes]

    def test_short_key_not_masked(self):
        masker = EnvKeyMasker(visible_chars=5)
        result = masker.mask({"PORT": "8080"})
        assert "PORT" in result.masked
        assert not result.has_changes()

    def test_custom_mask_char(self):
        masker = EnvKeyMasker(mask_char="#", visible_chars=1)
        result = masker.mask({"SECRET": "val"})
        masked_key = list(result.masked.keys())[0]
        assert masked_key.startswith("S")
        assert "#" in masked_key

    def test_values_preserved_after_masking(self, masker, sample_vars):
        result = masker.mask(sample_vars)
        original_values = set(sample_vars.values())
        masked_values = set(result.masked.values())
        assert original_values == masked_values

    def test_original_preserved_in_result(self, masker, sample_vars):
        result = masker.mask(sample_vars)
        assert result.original == sample_vars

    def test_zero_visible_chars_masks_entire_key(self):
        masker = EnvKeyMasker(visible_chars=0)
        result = masker.mask({"KEY": "value"})
        assert "***" in result.masked
