import importlib
import logging
import os
from typing import Any

log = logging.getLogger(__name__)


def get_gemini_client(model_name: str = "gemini-2.0-flash") -> Any:
    try:
        genai: Any = importlib.import_module("google.generativeai")
    except ImportError as exc:
        raise RuntimeError("google-generativeai is not installed") from exc

    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY or GOOGLE_API_KEY not set")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel
    return model(model_name)
