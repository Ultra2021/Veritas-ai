"""Application configuration.

Loads environment variables from the ``.env`` file using python-dotenv
and exposes typed settings for the rest of the backend.

``LLM_PROVIDER`` selects the active model provider (``groq`` by default,
with ``gemini`` supported as an option). When no usable provider key is
configured, the agents fall back to deterministic logic.
"""

import os

from dotenv import load_dotenv

load_dotenv()

LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "groq")
GROQ_API_KEY: str | None = os.getenv("GROQ_API_KEY")
GROQ_MODEL: str = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
GEMINI_API_KEY: str | None = os.getenv("GEMINI_API_KEY")
FRONTEND_ORIGIN: str = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")
