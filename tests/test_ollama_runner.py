# tests/test_ollama_runner.py

import subprocess
import pytest
from ollama_runner import run_ollama_model


def test_run_ollama_model_calls_subprocess(monkeypatch):
    prompt = "Mi Magyarország fővárosa?"
    model_name = "mistral"

    def mock_run(args, **kwargs):
        class Result:
            stdout = b"Budapest\n"  # bytes, nem str
            stderr = b""
            returncode = 0
        return Result()

    monkeypatch.setattr(subprocess, "run", mock_run)

    result = run_ollama_model(prompt, model_name)
    assert result.strip() == "Budapest"
