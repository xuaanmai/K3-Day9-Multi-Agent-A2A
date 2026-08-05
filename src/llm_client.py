"""
HuggingFace LLM Client module using InferenceClient.
Model: meta-llama/Llama-3.1-8B-Instruct (8B parameters <= 10B)
"""

import os
from typing import List, Dict, Any, Optional

try:
    import dotenv
    dotenv.load_dotenv()
except Exception:
    pass

try:
    import huggingface_hub
    InferenceClient = huggingface_hub.InferenceClient
except Exception:
    InferenceClient = None


# Model declared in code as per rule 9.4
MODEL_NAME = "meta-llama/Llama-3.1-8B-Instruct"
PARAMETER_SIZE = "8B"

class LLMClient:
    def __init__(self, model: str = MODEL_NAME, token: Optional[str] = None):
        self.model = model
        self.token = token or os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_TOKEN")
        if InferenceClient is not None:
            self.client = InferenceClient(model=self.model, token=self.token)
        else:
            self.client = None

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 500,
        temperature: float = 0.1
    ) -> str:
        """Sends a chat completion request to HuggingFace Inference API."""
        if self.client is None:
            return "LLM_ERROR: huggingface_hub package is not installed in the active environment."
        try:
            response = self.client.chat_completion(
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"LLM_ERROR: {str(e)}"
