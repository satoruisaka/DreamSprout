# ollama_runner.py
# OllamaRunner class to interface with Ollama API for text generation.
# Uses requests to send prompts and receive responses.

import requests
from config import CONFIG, OLLAMA_URL

# Simple token counter (replace with a real tokenizer if needed)
def count_tokens(text: str) -> int:
    return len(text.split())

# OllamaRunner class to interface with Ollama API for text generation.
class OllamaRunner:
    def __init__(self, model_name="dummy", server_url=OLLAMA_URL):
        self.model_name = model_name
        self.server_url = server_url

    def generate(self, prompt: str) -> str:
        print(f"Using model: {self.model_name}")  # Debug line
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_ctx": CONFIG["text_model"]["parameters"]["num_ctx"],
                "temperature": CONFIG["text_model"]["parameters"]["temperature"],
                "top_p": CONFIG["text_model"]["parameters"]["top_p"]
            }
        }

        try:
            response = requests.post(self.server_url, json=payload)
            response.raise_for_status()
            data = response.json()
            return data.get("response", "")
        except Exception as e:
            return f"Error calling Ollama API: {e}"