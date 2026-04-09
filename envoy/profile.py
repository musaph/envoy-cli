"""Profile management for envoy-cli — named environment profiles (e.g. dev, staging, prod)."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import re


PROFILE_NAME_RE = re.compile(r'^[a-zA-Z][a-zA-Z0-9_-]{0,63}$')


@dataclass
class Profile:
    name: str
    description: str = ""
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        if not PROFILE_NAME_RE.match(self.name):
            raise ValueError(
                f"Invalid profile name '{self.name}'. Must start with a letter and "
                "contain only letters, digits, underscores, or hyphens (max 64 chars)."
            )

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "tags": self.tags,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Profile":
        return cls(
            name=data["name"],
            description=data.get("description", ""),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {}),
        )

    def __repr__(self) -> str:
        return f"Profile(name={self.name!r}, description={self.description!r})"


class ProfileManager:
    """Manages a collection of named profiles backed by EnvoyConfig."""

    PROFILES_KEY = "profiles"

    def __init__(self, config):
        self._config = config

    def _all(self) -> Dict[str, dict]:
        return self._config.get(self.PROFILES_KEY) or {}

    def _save_all(self, profiles: Dict[str, dict]) -> None:
        self._config.set(self.PROFILES_KEY, profiles)

    def create(self, profile: Profile) -> None:
        all_profiles = self._all()
        if profile.name in all_profiles:
            raise ValueError(f"Profile '{profile.name}' already exists.")
        all_profiles[profile.name] = profile.to_dict()
        self._save_all(all_profiles)

    def get(self, name: str) -> Optional[Profile]:
        data = self._all().get(name)
        return Profile.from_dict(data) if data else None

    def update(self, profile: Profile) -> None:
        all_profiles = self._all()
        if profile.name not in all_profiles:
            raise KeyError(f"Profile '{profile.name}' does not exist.")
        all_profiles[profile.name] = profile.to_dict()
        self._save_all(all_profiles)

    def delete(self, name: str) -> bool:
        all_profiles = self._all()
        if name not in all_profiles:
            return False
        del all_profiles[name]
        self._save_all(all_profiles)
        return True

    def list_profiles(self) -> List[Profile]:
        return [Profile.from_dict(d) for d in self._all().values()]
