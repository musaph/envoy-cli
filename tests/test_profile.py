"""Tests for envoy.profile — Profile and ProfileManager."""

import pytest
from unittest.mock import MagicMock

from envoy.profile import Profile, ProfileManager, PROFILE_NAME_RE


# ---------------------------------------------------------------------------
# Profile dataclass
# ---------------------------------------------------------------------------

class TestProfile:
    def test_valid_name_accepted(self):
        p = Profile(name="dev")
        assert p.name == "dev"

    def test_invalid_name_raises(self):
        with pytest.raises(ValueError, match="Invalid profile name"):
            Profile(name="123bad")

    def test_name_with_hyphens_and_digits(self):
        p = Profile(name="staging-2")
        assert p.name == "staging-2"

    def test_to_dict_roundtrip(self):
        p = Profile(name="prod", description="Production", tags=["live"], metadata={"owner": "ops"})
        d = p.to_dict()
        restored = Profile.from_dict(d)
        assert restored.name == p.name
        assert restored.description == p.description
        assert restored.tags == p.tags
        assert restored.metadata == p.metadata

    def test_from_dict_defaults(self):
        p = Profile.from_dict({"name": "dev"})
        assert p.description == ""
        assert p.tags == []
        assert p.metadata == {}

    def test_repr(self):
        p = Profile(name="dev", description="Development")
        assert "dev" in repr(p)
        assert "Development" in repr(p)


# ---------------------------------------------------------------------------
# ProfileManager
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_config():
    store = {}

    def _get(key):
        return store.get(key)

    def _set(key, value):
        store[key] = value

    cfg = MagicMock()
    cfg.get.side_effect = _get
    cfg.set.side_effect = _set
    return cfg


@pytest.fixture
def manager(mock_config):
    return ProfileManager(mock_config)


class TestProfileManager:
    def test_create_and_get(self, manager):
        manager.create(Profile(name="dev", description="Dev env"))
        p = manager.get("dev")
        assert p is not None
        assert p.name == "dev"
        assert p.description == "Dev env"

    def test_create_duplicate_raises(self, manager):
        manager.create(Profile(name="dev"))
        with pytest.raises(ValueError, match="already exists"):
            manager.create(Profile(name="dev"))

    def test_get_nonexistent_returns_none(self, manager):
        assert manager.get("ghost") is None

    def test_update_profile(self, manager):
        manager.create(Profile(name="staging", description="old"))
        manager.update(Profile(name="staging", description="new"))
        assert manager.get("staging").description == "new"

    def test_update_nonexistent_raises(self, manager):
        with pytest.raises(KeyError, match="does not exist"):
            manager.update(Profile(name="ghost"))

    def test_delete_existing(self, manager):
        manager.create(Profile(name="dev"))
        assert manager.delete("dev") is True
        assert manager.get("dev") is None

    def test_delete_nonexistent_returns_false(self, manager):
        assert manager.delete("ghost") is False

    def test_list_profiles(self, manager):
        manager.create(Profile(name="dev"))
        manager.create(Profile(name="prod"))
        names = {p.name for p in manager.list_profiles()}
        assert names == {"dev", "prod"}

    def test_list_empty(self, manager):
        assert manager.list_profiles() == []
