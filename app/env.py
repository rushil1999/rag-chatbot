"""Loads environment variables once, from a path that does not depend on the working directory.

A bare `load_dotenv()` searches upward from the CWD, which never finds `app/.env` when the
server is started from the repo root as the README instructs. Importing this module first makes
`os.getenv` reliable everywhere. Real environment variables always win over the file, so
container deployments that inject config directly are unaffected.
"""
from pathlib import Path

from dotenv import load_dotenv

ENV_PATH = Path(__file__).resolve().parent / ".env"

load_dotenv(ENV_PATH)
