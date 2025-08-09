# backend/orchestrator/clients/openai_client.py
"""
Wrapper for the OpenAI API client used for moderator/final decision tasks.
Defaults to the lightweight "gpt-5-nano" model.
Falls back to mock responses when OPENAI_API_KEY is not present.
"""
from __future__ import annotations

import os
from typing import Optional

try:
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None  # type: ignore

DEFAULT_MODEL = "gpt-5-nano"


class OpenAIModeratorClient:
    def __init__(self, model: str = DEFAULT_MODEL):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.enabled = bool(self.api_key) and OpenAI is not None
        self.model = model
        if self.enabled:
            # Lazy client creation to avoid import issues if pkg missing
            self._client: Optional[OpenAI] = OpenAI(api_key=self.api_key)  # type: ignore[arg-type]
            print(f"Initialized OpenAI moderator client with model: {self.model}")
        else:
            self._client = None
            if OpenAI is None:
                print("openai package not installed. Using mock moderator responses.")
            else:
                print("OPENAI_API_KEY not set. Using mock moderator responses.")

    def invoke(self, prompt: str) -> str:
        if not self.enabled or self._client is None:  # mock mode
            return "[Mock OpenAI] Final decision synthesized (no API key)."
        try:
            resp = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful moderator that synthesizes a final decision."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=400,
            )
            content = resp.choices[0].message.content or ""
            return content.strip()
        except Exception as e:  # pragma: no cover
            return f"[OpenAI error] {e}"
