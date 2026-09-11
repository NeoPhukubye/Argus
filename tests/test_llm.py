import os
from unittest.mock import MagicMock, patch

import pytest

from argus.utils.llm import get_gemini_client


def test_get_gemini_client_missing_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    with patch.dict("sys.modules", {"google.generativeai": MagicMock()}):
        with pytest.raises(RuntimeError, match="GEMINI_API_KEY or GOOGLE_API_KEY not set"):
            get_gemini_client()


def test_get_gemini_client_with_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    mock_model = MagicMock()
    mock_genai = MagicMock()
    mock_genai.GenerativeModel.return_value = mock_model
    with patch.dict("sys.modules", {"google.generativeai": mock_genai}):
        client = get_gemini_client()
    assert client is mock_model
    mock_genai.GenerativeModel.assert_called_once_with("gemini-2.0-flash")
