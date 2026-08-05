from typing import Any, Dict


class LLMClient:
    def __init__(self, model_name: str = "local-llm"):
        self.model_name = model_name

    def generate(self, prompt: str, **kwargs: Any) -> Dict[str, Any]:
        return {
            "model": self.model_name,
            "prompt": prompt,
            "response": "",
            "metadata": kwargs,
        }
