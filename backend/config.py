"""Application configuration.

Loads environment variables from the ``.env`` file using python-dotenv
and exposes typed settings for the rest of the backend.
"""

import os

from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY: str | None = os.getenv("GEMINI_API_KEY")
FRONTEND_ORIGIN: str = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")
