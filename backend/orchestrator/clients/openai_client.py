# backend/orchestrator/clients/openai_client.py
"""
Wrapper for the OpenAI API client used for moderator/final decision tasks.
Defaults to the lightweight "gpt-5-nano" model.
Falls back to mock responses when OPENAI_API_KEY is not present.
"""

from __future__ import annotations

import os

from ...config import settings

try:
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None  # type: ignore

DEFAULT_MODEL = (
    settings.OPENAI_MODEL if hasattr(settings, "OPENAI_MODEL") else "gpt-5-nano"
)


class OpenAIModeratorClient:
    def __init__(self, model: str = DEFAULT_MODEL):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.enabled = bool(self.api_key) and OpenAI is not None
        # Allow overriding model via env var
        # Prefer project settings; allow env override to keep flexibility
        self.model = os.getenv(
            "OPENAI_MODEL",
            settings.OPENAI_MODEL if hasattr(settings, "OPENAI_MODEL") else model,
        )
        if self.enabled:
            # Lazy client creation to avoid import issues if pkg missing
            self._client: OpenAI | None = OpenAI(api_key=self.api_key)  # type: ignore[arg-type]
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
            # Prefer Chat Completions without vendor-specific token parameters
            resp = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful moderator that synthesizes a final decision.",
                    },
                    {"role": "user", "content": prompt},
                ],
            )
            content = resp.choices[0].message.content or ""
            return content.strip()
        except Exception as first_error:  # Try Responses API as a fallback
            try:
                resp = self._client.responses.create(
                    model=self.model,
                    input=prompt,
                    # Avoid passing max_* tokens to be provider-agnostic
                )
                # openai>=1.0 exposes a convenience property
                if hasattr(resp, "output_text") and resp.output_text:
                    return str(resp.output_text).strip()
                # Fallback to reading from content
                if getattr(resp, "choices", None):
                    first = resp.choices[0]
                    if hasattr(first, "message") and getattr(
                        first.message, "content", None
                    ):
                        return str(first.message.content[0].text).strip()  # type: ignore[attr-defined]
                return "[OpenAI] Empty response"
            except Exception as second_error:  # pragma: no cover
                return f"[OpenAI error] {second_error} | prior: {first_error}"
