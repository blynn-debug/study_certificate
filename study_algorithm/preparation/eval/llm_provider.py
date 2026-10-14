"""Small structured-JSON provider boundary; credentials never enter audit artifacts."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Protocol
from urllib.parse import urlparse


class ProviderUnavailable(RuntimeError):
    """A live model cannot return a usable, completed structured response."""


class JsonProvider(Protocol):
    """Boundary implemented by a real provider or an explicitly labelled test fixture."""

    def complete(self, *, instructions: str, payload: dict[str, Any],
                 schema: dict[str, Any], name: str) -> dict[str, Any]:
        """Return parsed JSON and separate provider/usage metadata."""


@dataclass(frozen=True)
class ResponsesProvider:
    """OpenAI Responses adapter using its documented strict JSON schema interface."""

    api_key: str = field(repr=False)
    model: str
    base_url: str = "https://api.openai.com/v1"
    timeout_seconds: int = 45
    max_output_tokens: int = 10000

    def __post_init__(self) -> None:
        parsed = urlparse(self.base_url)
        if parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError("Provider base URL must not contain credentials, query, or fragment")
        if parsed.scheme != "https" and not (
            parsed.scheme == "http" and parsed.hostname in {"localhost", "127.0.0.1", "::1"}
        ):
            raise ValueError("Use HTTPS, except for an explicitly configured loopback provider")
        if not self.api_key or not self.model:
            raise ProviderUnavailable("Configure OPENAI_API_KEY and STUDY_EVAL_MODEL locally")
        if not 1 <= self.timeout_seconds <= 60 or not 256 <= self.max_output_tokens <= 20000:
            raise ValueError("Provider timeout or output budget is outside the configured limits")

    @classmethod
    def from_environment(cls, *, review: bool = False) -> ResponsesProvider:
        """Read only the explicitly named configuration variables, never Codex credentials."""
        return cls(
            api_key=os.environ.get("OPENAI_API_KEY", ""),
            model=(os.environ.get("STUDY_EVAL_REVIEW_MODEL", "") if review else "")
            or os.environ.get("STUDY_EVAL_MODEL", ""),
            base_url=os.environ.get("STUDY_EVAL_BASE_URL", "https://api.openai.com/v1"),
        )

    def complete(self, *, instructions: str, payload: dict[str, Any],
                 schema: dict[str, Any], name: str) -> dict[str, Any]:
        """Make one bounded request; incomplete/refused responses never become grades."""
        body = {
            "model": self.model, "store": False,
            "instructions": instructions,
            "input": json.dumps(payload, ensure_ascii=False),
            "max_output_tokens": self.max_output_tokens,
            "text": {"format": {"type": "json_schema", "name": name, "strict": True, "schema": schema}},
        }
        request = urllib.request.Request(
            self.base_url.rstrip("/") + "/responses",
            data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                raw = response.read(4_000_001)
        except urllib.error.HTTPError as exc:
            # HTTP bodies can contain submitted material or deployment information.
            raise ProviderUnavailable(f"Provider HTTP status {exc.code}; no grade recorded") from None
        except (urllib.error.URLError, TimeoutError, OSError):
            raise ProviderUnavailable("Provider transport failure; no grade recorded") from None
        if len(raw) > 4_000_000:
            raise ProviderUnavailable("Provider response exceeded the local size limit")
        try:
            envelope = json.loads(raw)
        except (ValueError, UnicodeError):
            raise ProviderUnavailable("Provider returned invalid JSON") from None
        if envelope.get("status") != "completed":
            raise ProviderUnavailable("Provider response was not completed")
        texts = []
        for output in envelope.get("output", []):
            if output.get("type") != "message":
                continue
            for content in output.get("content", []):
                if content.get("type") == "refusal":
                    raise ProviderUnavailable("Provider refused this assessment")
                if content.get("type") == "output_text":
                    texts.append(content.get("text", ""))
        if len(texts) != 1:
            raise ProviderUnavailable("Expected exactly one structured JSON message")
        try:
            result = json.loads(texts[0])
        except ValueError:
            raise ProviderUnavailable("Provider message was not structured JSON") from None
        return {
            "data": result,
            "metadata": {
                "adapter": "responses", "model": envelope.get("model", self.model),
                "response_id": envelope.get("id"), "usage": envelope.get("usage"),
                "status": "completed", "origin": "live_provider_response",
            },
        }
