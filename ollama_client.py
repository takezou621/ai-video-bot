"""
Ollama LLM Client - Local LLM integration via Ollama REST API
Replaces Gemini API calls with local inference
"""

import os
import json
import requests
from typing import Optional

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b-instruct-q4_K_M")
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "300"))  # 5分


def call_ollama(
    prompt: str,
    max_tokens: int = 8192,
    temperature: float = 0.9,
    system_prompt: Optional[str] = None
) -> str:
    """
    Call Ollama API with unified interface matching Gemini API

    Args:
        prompt: The user prompt
        max_tokens: Maximum tokens to generate
        temperature: Sampling temperature (0.0-1.0)
        system_prompt: Optional system prompt

    Returns:
        Generated text response

    Raises:
        RuntimeError: If Ollama request fails or times out
    """
    url = f"{OLLAMA_BASE_URL}/api/generate"

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_predict": max_tokens,
        }
    }

    if system_prompt:
        payload["system"] = system_prompt

    try:
        response = requests.post(url, json=payload, timeout=OLLAMA_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        return data.get("response", "")
    except requests.exceptions.Timeout:
        raise RuntimeError(f"Ollama request timed out after {OLLAMA_TIMEOUT}s")
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Ollama API error: {e}")


def check_ollama_health() -> bool:
    """Check if Ollama server is running and model is available"""
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        if response.status_code != 200:
            return False

        models = response.json().get("models", [])
        # Check if the configured model is available
        model_name = OLLAMA_MODEL.split(":")[0]  # Extract base name (e.g., "llama3.1" from "llama3.1:8b-instruct-q4_K_M")
        return any(model_name in m.get("name", "") for m in models)
    except:
        return False


if __name__ == "__main__":
    # Test
    print(f"Testing Ollama client with model: {OLLAMA_MODEL}")
    print(f"Ollama URL: {OLLAMA_BASE_URL}")

    if check_ollama_health():
        print("✅ Ollama is healthy and model is available")

        # Test Japanese response
        try:
            response = call_ollama(
                "こんにちは、日本語で自己紹介してください。3文程度でお願いします。",
                max_tokens=200,
                temperature=0.7
            )
            print(f"\nTest Response:\n{response}")
            print("\n✅ Ollama test successful")
        except Exception as e:
            print(f"\n❌ Ollama test failed: {e}")
    else:
        print("❌ Ollama is not available")
        print("\nTroubleshooting:")
        print("1. Check if Ollama server is running: docker compose ps ollama")
        print("2. Check if model is pulled: docker compose exec ollama ollama list")
        print(f"3. Pull model if needed: docker compose exec ollama ollama pull {OLLAMA_MODEL}")
