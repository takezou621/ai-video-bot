import os
import time
import shutil
import subprocess
import requests
import base64
from pathlib import Path
from PIL import Image, ImageDraw
import sd_client

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
USE_NANO_BANANA_PRO = os.getenv("USE_NANO_BANANA_PRO", "false").lower() == "true"
USE_STABLE_DIFFUSION = os.getenv("USE_STABLE_DIFFUSION", "false").lower() == "true"

def generate_image(prompt, out_path: Path, max_retries=3, model=None):
    """
    Generate an image using the configured provider (Stable Diffusion > Nano Banana Pro > OpenAI DALL-E).
    """
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # 1. Try Stable Diffusion (Local)
    if USE_STABLE_DIFFUSION:
        if sd_client.is_available():
            print(f"[SD] Generating image for prompt: {prompt[:50]}...")
            # Use 16:9 aspect ratio suitable for SDXL or SD1.5
            width = 1152
            height = 648
            result = sd_client.generate_image_sd(prompt, out_path, width=width, height=height)
            if result:
                return result
            print("[SD] Generation failed, falling back...")
        else:
            print("[SD] WebUI not reachable, skipping...")

    # 2. Try Nano Banana Pro (Gemini CLI)
    if USE_NANO_BANANA_PRO:
        result = _generate_with_nano_banana_pro(prompt, out_path)
        if result:
            return result

    # 3. Fallback to OpenAI DALL-E
    return _generate_with_openai(prompt, out_path, max_retries, model)

def _generate_with_openai(prompt, out_path, max_retries, model):
    if not OPENAI_API_KEY:
        print("Error: OPENAI_API_KEY not found. Cannot generate image.")
        return _create_dummy_image(out_path)

    image_model = model or os.getenv("OPENAI_IMAGE_MODEL", "dall-e-3")
    print(f"[OpenAI] Generating image with model: {image_model}")

    url = "https://api.openai.com/v1/images/generations"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }

    if image_model == "dall-e-2":
        image_size = "1024x1024"
    else:
        image_size = "1792x1024"

    # Try original prompt first, then fallback to safe prompt
    prompts_to_try = [
        f"Cinematic 16:9 landscape image, film photography style: {prompt}",
        # Fallback safe prompt for content policy violations
        "Japanese anime style YouTube thumbnail background, bright colorful tech news studio, "
        "futuristic digital cityscape with neon lights, abstract technology symbols floating, "
        "vibrant cyan magenta yellow colors, clean modern design, NO text, 16:9 aspect ratio, "
        "Makoto Shinkai style sky, cheerful hopeful atmosphere"
    ]

    for prompt_idx, current_prompt in enumerate(prompts_to_try):
        payload = {
            "model": image_model,
            "prompt": current_prompt,
            "n": 1,
            "size": image_size,
            "response_format": "b64_json"
        }

        for attempt in range(max_retries):
            try:
                r = requests.post(url, headers=headers, json=payload, timeout=120)
                data = r.json()
                if "error" in data:
                    error_msg = data["error"].get("message", "Unknown API error")
                    error_code = data["error"].get("code", "")

                    if "rate_limit" in error_msg.lower():
                        print(f"Rate limit hit, waiting 65s... (attempt {attempt+1}/{max_retries})")
                        time.sleep(65)
                        continue

                    # Content policy violation - try safe fallback prompt
                    if error_code == "content_policy_violation" and prompt_idx == 0:
                        print(f"[OpenAI] Content policy violation, trying safe fallback prompt...")
                        break  # Break inner loop to try next prompt

                    print("API Error:", data["error"])
                    if prompt_idx == len(prompts_to_try) - 1:
                        return _create_dummy_image(out_path)
                    break  # Try next prompt

                img_b64 = data["data"][0]["b64_json"]
                img_bytes = base64.b64decode(img_b64)
                with open(out_path, "wb") as f:
                    f.write(img_bytes)
                if prompt_idx > 0:
                    print(f"[OpenAI] Generated with safe fallback prompt")
                return out_path
            except Exception as e:
                print("OpenAI error:", e)
                if attempt < max_retries - 1:
                    continue
                if prompt_idx == len(prompts_to_try) - 1:
                    return _create_dummy_image(out_path)
                break  # Try next prompt

    return _create_dummy_image(out_path)

def _create_dummy_image(out_path: Path) -> Path:
    """Create a placeholder image if generation fails."""
    img = Image.new("RGB", (1792, 1024), (40, 80, 120))
    d = ImageDraw.Draw(img)
    d.text((20, 20), "DUMMY IMAGE (Generation Failed)", (255, 255, 255))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path)
    print(f"[Fallback] Created dummy image at {out_path}")
    return out_path

def _generate_with_nano_banana_pro(prompt: str, out_path: Path):
    gemini_path = shutil.which("gemini")
    if not gemini_path:
        return None
        
    print("[NanoBananaPro] Attempting image generation via 'gemini' CLI...")
    # Simplified logic for prototype
    return None # Fallback for now as it's complex to handle inside Docker