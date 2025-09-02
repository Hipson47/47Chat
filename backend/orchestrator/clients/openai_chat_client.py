"""
General-purpose OpenAI chat client for agent (alter) responses.
Uses the configured model from project settings or OPENAI_MODEL env var.
Falls back gracefully when the API key or package is missing.
"""

from __future__ import annotations

import os

try:
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None  # type: ignore

from ...config import settings


class OpenAIChatClient:
    def __init__(self, model: str | None = None):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.enabled = bool(self.api_key) and OpenAI is not None
        self.model = (
            os.getenv("OPENAI_MODEL", settings.OPENAI_MODEL) if model is None else model
        )
        if self.enabled:
            self._client: OpenAI | None = OpenAI(api_key=self.api_key)  # type: ignore[arg-type]
        else:
            self._client = None

    def invoke(self, prompt: str, system: str | None = None) -> str:
        if not self.enabled or self._client is None:  # mock mode
            # Provide a simple mock so the pipeline keeps running without a key
            return f"[Mock OpenAI alter] {prompt[:200]}..."
        try:
            resp = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": system or "You are a helpful expert.",
                    },
                    {"role": "user", "content": prompt},
                ],
            )
            content = resp.choices[0].message.content or ""
            return content.strip()
        except Exception as first_error:  # Fallback to Responses API
            try:
                resp = self._client.responses.create(
                    model=self.model,
                    input=(system + "\n\n" if system else "") + prompt,
                )
                if hasattr(resp, "output_text") and resp.output_text:
                    return str(resp.output_text).strip()
                if getattr(resp, "choices", None):
                    first = resp.choices[0]
                    if hasattr(first, "message") and getattr(
                        first.message, "content", None
                    ):
                        return str(first.message.content[0].text).strip()  # type: ignore[attr-defined]
                return "[OpenAI alter] Empty response"
            except Exception as second_error:
                return f"[OpenAI alter error] {second_error} | prior: {first_error}"
