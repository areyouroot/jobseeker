import os
import requests

class LLMProvider:
    @staticmethod
    def generate(model: str, prompt: str, context: dict) -> str:
        if model == "ollama":
            return LLMProvider._call_ollama(prompt, context)
        elif model == "gpt-4":
            return LLMProvider._call_openai(prompt, context)
        # Add others...
        else:
            return "Model not supported yet."

    @staticmethod
    def _call_ollama(prompt: str, context: dict) -> str:
        url = os.getenv("OLLAMA_HOST", "http://localhost:11434") + "/api/generate"
        payload = {
            "model": "llama3", # Default or configurable
            "prompt": f"Context: {context}\n\nTask: {prompt}",
            "stream": False
        }
        try:
            res = requests.post(url, json=payload)
            return res.json().get("response", "")
        except Exception as e:
            return f"Error calling Ollama: {str(e)}"

    @staticmethod
    def _call_openai(prompt: str, context: dict) -> str:
        # Mock implementation for now
        return "OpenAI response placeholder"
