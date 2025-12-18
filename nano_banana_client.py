import os
import base64
import requests
import time
import shutil
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
USE_NANO_BANANA_PRO = os.getenv("USE_NANO_BANANA_PRO", "false").lower() == "true"
# Note: nanobanana binary does not exist; only gemini CLI integration is supported
NANO_BANANA_PRO_STYLE = os.getenv("NANO_BANANA_PRO_STYLE", "cinematic-newsroom")
NANO_BANANA_PRO_WIDTH = int(os.getenv("NANO_BANANA_PRO_WIDTH", "1792"))
NANO_BANANA_PRO_HEIGHT = int(os.getenv("NANO_BANANA_PRO_HEIGHT", "1024"))
NANO_BANANA_PRO_TIMEOUT = int(os.getenv("NANO_BANANA_PRO_TIMEOUT", "120"))
# Model settings
NANO_BANANA_GEMINI_MODEL = os.getenv("NANO_BANANA_GEMINI_MODEL", "gemini-3-flash-preview")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


def _dummy(prompt, out_path):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", (1792, 1024), (40, 80, 120))
    d = ImageDraw.Draw(img)
    d.text((20, 20), "DUMMY IMAGE", (255, 255, 255))
    img.save(out_path)
    return out_path


def generate_image(prompt, out_path: Path, max_retries=3, model=None):
    if USE_NANO_BANANA_PRO:
        result = _generate_with_nano_banana_pro(prompt, out_path)
        if result:
            return result

    if not OPENAI_API_KEY:
        return _dummy(prompt, out_path)

    image_model = model or os.getenv("OPENAI_IMAGE_MODEL", "dall-e-3")
    print(f"[OpenAI] Generating image with model: {image_model}")

    url = "https://api.openai.com/v1/images/generations"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Adjust payload based on model
    # DALL-E 2: max 1024x1024, DALL-E 3: supports 1792x1024
    if image_model == "dall-e-2":
        image_size = "1024x1024"
        print(f"[OpenAI] Using image size: {image_size} for {image_model}")
    elif image_model == "gpt-image-1.5":
        image_size = "auto"
        print(f"[OpenAI] Using image size: {image_size} for {image_model}")
    else:
        # DALL-E 3 and others default to 1792x1024
        image_size = "1792x1024"

    payload = {
        "model": image_model,
        "prompt": f"Cinematic 16:9 landscape image, film photography style: {prompt}",
        "n": 1,
        "size": image_size
    }

    # 'response_format' might not be supported by gpt-image-1.5 or newer models
    if image_model != "gpt-image-1.5":
        payload["response_format"] = "b64_json"

    for attempt in range(max_retries):
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=120)
            data = r.json()
            if "error" in data:
                error_msg = data["error"].get("message", "Unknown API error")
                if "rate_limit" in error_msg.lower():
                    wait_time = 65  # Wait 65 seconds for rate limit reset
                    print(f"Rate limit hit, waiting {wait_time}s... (attempt {attempt+1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                print("API Error:", data["error"])
                raise Exception(error_msg)
            img_b64 = data["data"][0]["b64_json"]
            img_bytes = base64.b64decode(img_b64)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            open(out_path, "wb").write(img_bytes)
            return out_path
        except Exception as e:
            if attempt < max_retries - 1 and "rate_limit" in str(e).lower():
                continue
            print("fallback:", e)
            return _dummy(prompt, out_path)

    return _dummy(prompt, out_path)


def _generate_with_nano_banana_pro(prompt: str, out_path: Path):
    """Invoke Nano Banana Pro via Gemini CLI integration.

    Note: The 'nanobanana' binary does not exist. This function only attempts
    to use the 'gemini' CLI with nanobanana extension if available.
    """

    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Try 'gemini' CLI with nanobanana extension
    gemini_path = shutil.which("gemini")
    if gemini_path:
        print("[NanoBananaPro] Attempting image generation via 'gemini' CLI with nanobanana extension...")
        
        # Ensure nanobanana-output directory exists and list initial files
        nanobanana_output_dir = Path(os.getenv("NANO_BANANA_PRO_OUTPUT_DIR", "nanobanana-output"))
        nanobanana_output_dir.mkdir(parents=True, exist_ok=True)
        initial_files = set(nanobanana_output_dir.iterdir())

        # Construct natural language prompt for the agent
        # We instruct the agent to save the image to nanobanana-output/
        # and we will handle the move to out_path.
        cli_prompt = (
            f"Using the nanobanana extension, generate an image. "
            f"Prompt: '{prompt}'. "
            f"Style: '{NANO_BANANA_PRO_STYLE}'. "
            f"Width: {NANO_BANANA_PRO_WIDTH}, Height: {NANO_BANANA_PRO_HEIGHT}. "
            f"CRITICAL: Save the image to the default output directory for nanobanana "
            f"(e.g., '{nanobanana_output_dir}'). "
            f"Generate exactly one image. Do not ask for confirmation."
        )

        cmd = [
            gemini_path,
            "--yolo",  # Auto-approve tool use
            cli_prompt
        ]

        try:
            subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True,
                timeout=NANO_BANANA_PRO_TIMEOUT
            )
            
            # Find the newly created file in nanobanana-output_dir
            new_files = set(nanobanana_output_dir.iterdir())
            generated_file = None
            if new_files:
                # Find the most recently modified file among the new ones
                newly_created = list(new_files - initial_files)
                if newly_created:
                    generated_file = max(newly_created, key=os.path.getmtime)
            
            if generated_file and generated_file.exists():
                shutil.move(str(generated_file), str(out_path))
                print(f"[NanoBananaPro] Successfully moved generated image to {out_path}")
                return out_path
            else:
                print(f"[NanoBananaPro] Gemini CLI finished but no new image found in {nanobanana_output_dir}.")
                
        except Exception as e:
            print(f"[NanoBananaPro] Gemini CLI invocation failed: {e}")

    print("[NanoBananaPro] Gemini CLI not found or image generation failed. Falling back to OpenAI API.")
    return None
