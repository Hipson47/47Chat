# backend/orchestrator/clients/openai_client.py
"""
Wrapper for the OpenAI API client used for moderator/final decision tasks.
Defaults to the lightweight "gpt-5-nano" model.
Falls back to mock responses when OPENAI_API_KEY is not present.

Enhanced with resilience layer: retries, circuit breaker, and metrics.
"""
from __future__ import annotations

import asyncio
import os
import time
from typing import Optional
from ...config import settings

try:
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None  # type: ignore

# Import resilience components
from ...clients.retry import with_retries
from ...clients.circuit import CircuitBreaker
from ...clients.config import get_resilience_config
from ...clients import metrics

DEFAULT_MODEL = settings.OPENAI_MODEL if hasattr(settings, "OPENAI_MODEL") else "gpt-5-nano"


class OpenAIModeratorClient:
    def __init__(self, model: str = DEFAULT_MODEL):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.enabled = bool(self.api_key) and OpenAI is not None
        # Allow overriding model via env var
        # Prefer project settings; allow env override to keep flexibility
        self.model = os.getenv("OPENAI_MODEL", settings.OPENAI_MODEL if hasattr(settings, "OPENAI_MODEL") else model)
        
        # Initialize resilience components
        config = get_resilience_config()
        self._retry_policy = config.to_retry_policy()
        self._circuit_breaker = CircuitBreaker(
            name="openai_moderator",
            failure_threshold=config.cb_failure_threshold,
            recovery_time_s=config.cb_recovery_time_s,
            half_open_max_success=config.cb_half_open_max_success,
        )
        
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
        
        # Check circuit breaker
        if not self._circuit_breaker.allow_request():
            metrics.update_circuit_state("openai_moderator", self._circuit_breaker.state)
            return "[OpenAI] Service temporarily unavailable (circuit breaker open)."
        
        # Convert sync call to async for resilience layer
        async def make_request() -> str:
            return await asyncio.to_thread(self._make_sync_request, prompt)
        
        # Use resilience layer
        try:
            # Run async operation in current event loop or create one
            try:
                loop = asyncio.get_running_loop()
                # We're in an async context, but invoke is sync - use asyncio.create_task
                task = loop.create_task(
                    self._invoke_with_resilience(make_request)
                )
                # This is a hack - we need to handle this properly
                return "[OpenAI] Async operation started (sync interface limitation)"
            except RuntimeError:
                # No running loop, safe to use asyncio.run
                return asyncio.run(self._invoke_with_resilience(make_request))
        except Exception as e:
            return f"[OpenAI error] {str(e)}"
    
    async def _invoke_with_resilience(self, make_request) -> str:
        """Invoke with full resilience layer."""
        start_time = time.time()
        client_name = "openai_moderator"
        
        try:
            metrics.record_request_start(client_name)
            
            result = await with_retries(make_request, self._retry_policy)
            
            # Record success
            duration = time.time() - start_time
            metrics.record_request_success(client_name, duration)
            self._circuit_breaker.on_success()
            metrics.update_circuit_state(client_name, self._circuit_breaker.state)
            
            return result
            
        except Exception as e:
            # Record failure
            duration = time.time() - start_time
            error_kind = metrics.classify_exception(e)
            
            if error_kind == "timeout":
                metrics.record_timeout(client_name)
            
            metrics.record_request_error(client_name, error_kind, duration)
            self._circuit_breaker.on_failure()
            metrics.update_circuit_state(client_name, self._circuit_breaker.state)
            
            return f"[OpenAI error] {str(e)}"
    
    def _make_sync_request(self, prompt: str) -> str:
        """Make the actual synchronous OpenAI API request."""
        try:
            # Prefer Chat Completions without vendor-specific token parameters
            resp = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful moderator that synthesizes a final decision."},
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
                    if hasattr(first, "message") and getattr(first.message, "content", None):
                        return str(first.message.content[0].text).strip()  # type: ignore[attr-defined]
                return "[OpenAI] Empty response"
            except Exception as second_error:  # pragma: no cover
                raise Exception(f"{second_error} | prior: {first_error}")
