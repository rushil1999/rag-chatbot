import os
from app.service.logging import log_info, log_error

# Editable core bio, loaded once at import. This is always-present context for
# Vini so it can answer on-persona even when vector search returns little.
_PROFILE_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "profile.md")


def _load_profile() -> str:
  try:
    with open(_PROFILE_PATH, "r", encoding="utf-8") as f:
      content = f.read().strip()
    log_info("Loaded profile from {path} ({length} chars)", path=_PROFILE_PATH, length=len(content))
    return content
  except FileNotFoundError:
    log_error("Profile file not found at {path}; continuing without a base bio", path=_PROFILE_PATH)
    return ""
  except Exception as e:
    log_error("Error loading profile from {path}: {error}", path=_PROFILE_PATH, error=str(e))
    return ""


PROFILE = _load_profile()
