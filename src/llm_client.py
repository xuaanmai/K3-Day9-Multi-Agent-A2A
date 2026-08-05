"""Local Ollama client shared by every logical agent."""

from __future__ import annotations

import json
from typing import Any, Dict
from urllib.error import URLError
from urllib.request import Request, urlopen


MODEL_NAME = "qwen2.5:0.5b"
PARAMETER_SIZE = "0.49B"
PROVIDER = "Ollama"
OLLAMA_HOST = "http://127.0.0.1:11434"


class LLMClient:
    def __init__(
        self,
        model: str = MODEL_NAME,
        host: str = OLLAMA_HOST,
        *,
        enabled: bool = True,
        timeout_seconds: int = 120,
    ):
        self.model = model
        self.host = host.rstrip("/")
        self.enabled = enabled
        self.timeout_seconds = timeout_seconds

    def _post(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        request = Request(
            f"{self.host}{endpoint}",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                return json.loads(response.read().decode("utf-8"))
        except (OSError, URLError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"Ollama request failed: {exc}") from exc

    def assert_ready(self) -> None:
        """Fail before a run if Ollama or the configured model is unavailable."""

        if not self.enabled:
            return
        try:
            with urlopen(f"{self.host}/api/tags", timeout=10) as response:
                data = json.loads(response.read().decode("utf-8"))
        except (OSError, URLError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"Ollama is not available at {self.host}: {exc}") from exc
        names = {model.get("name") for model in data.get("models", [])}
        if self.model not in names:
            raise RuntimeError(
                f"Ollama model {self.model!r} is not installed. Run: ollama pull {self.model}"
            )

    def review(self, agent_name: str, facts: Dict[str, Any]) -> Dict[str, Any]:
        """Ask the shared model for a concise, structured role-specific review."""

        if not self.enabled:
            return {"invoked": False, "success": True, "summary": "deterministic mode"}

        schema = {
            "type": "object",
            "properties": {
                "accepted": {"type": "boolean"},
            },
            "required": ["accepted"],
        }
        response = self._post(
            "/api/chat",
            {
                "model": self.model,
                "stream": False,
                "format": schema,
                "keep_alive": "30m",
                "options": {"temperature": 0, "seed": 42, "num_predict": 16},
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            f"You are {agent_name}. Check whether the supplied code-derived facts "
                            "are suitable for handoff. Never invent facts. Return JSON only."
                        ),
                    },
                    {
                        "role": "user",
                        "content": json.dumps(facts, ensure_ascii=False, separators=(",", ":")),
                    },
                ],
            },
        )
        content = response.get("message", {}).get("content", "")
        try:
            parsed = json.loads(content)
            accepted = bool(parsed["accepted"])
        except (KeyError, TypeError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"Invalid structured response from {agent_name}: {content}") from exc
        return {
            "invoked": True,
            "success": True,
            "accepted": accepted,
            "summary": f"{agent_name} reviewed the code-derived handoff facts.",
        }
