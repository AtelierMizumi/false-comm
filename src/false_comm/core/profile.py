"""Profile management and YAML loader."""

from pathlib import Path

import yaml

from false_comm.models.config import BehaviorProfile


class ProfileRegistry:
    """Manages loading built-in and user-defined behavior profiles."""

    DEFAULT_PROFILES_DIR = Path(__file__).resolve().parent.parent / "data" / "profiles"

    @classmethod
    def list_available_profiles(cls) -> list[str]:
        """Return names of all built-in profiles."""
        if not cls.DEFAULT_PROFILES_DIR.exists():
            return ["standard"]
        return sorted([p.stem for p in cls.DEFAULT_PROFILES_DIR.glob("*.yaml")])

    @classmethod
    def load_profile(cls, name_or_path: str) -> BehaviorProfile:
        """Load a profile by name (built-in) or direct file path."""
        candidate_path = Path(name_or_path)

        # Check direct file path
        if candidate_path.is_file():
            return cls._load_from_file(candidate_path)

        # Check built-in directory
        builtin_file = cls.DEFAULT_PROFILES_DIR / f"{name_or_path}.yaml"
        if builtin_file.is_file():
            return cls._load_from_file(builtin_file)

        # Fallback error with suggestions
        available = ", ".join(cls.list_available_profiles())
        raise ValueError(
            f"Profile '{name_or_path}' not found. Available profiles: {available}, "
            "or provide a direct path to a YAML profile file."
        )

    @classmethod
    def _load_from_file(cls, path: Path) -> BehaviorProfile:
        try:
            with open(path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
            if not isinstance(data, dict):
                raise ValueError(f"Profile file '{path}' must contain a YAML dictionary.")
            return BehaviorProfile.model_validate(data)
        except Exception as e:
            raise ValueError(f"Failed to parse profile at '{path}': {e}") from e
