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
NANO_BANANA_PRO_BIN = os.getenv("NANO_BANANA_PRO_BIN", "nanobanana")
NANO_BANANA_PRO_STYLE = os.getenv("NANO_BANANA_PRO_STYLE", "cinematic-newsroom")
NANO_BANANA_PRO_WIDTH = int(os.getenv("NANO_BANANA_PRO_WIDTH", "1792"))
NANO_BANANA_PRO_HEIGHT = int(os.getenv("NANO_BANANA_PRO_HEIGHT", "1024"))
NANO_BANANA_PRO_TIMEOUT = int(os.getenv("NANO_BANANA_PRO_TIMEOUT", "120"))
NANO_BANANA_GEMINI_MODEL = os.getenv("NANO_BANANA_GEMINI_MODEL", "gemini-2.0-flash")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


def _dummy(prompt, out_path):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", (1792, 1024), (40, 80, 120))
    d = ImageDraw.Draw(img)
    d.text((20, 20), "DUMMY IMAGE", (255, 255, 255))
    img.save(out_path)
    return out_path


def generate_image(prompt, out_path: Path, max_retries=3):
    result = _generate_with_nano_banana_pro(prompt, out_path)
    if result:
        return result

    if not OPENAI_API_KEY:
        return _dummy(prompt, out_path)

    url = "https://api.openai.com/v1/images/generations"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "dall-e-3",
        "prompt": f"Cinematic 16:9 landscape image, film photography style: {prompt}",
        "n": 1,
        "size": "1792x1024",
        "response_format": "b64_json"
    }

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
    """Invoke Nano Banana Pro via Gemini CLI integration."""

    out_path.parent.mkdir(parents=True, exist_ok=True)
    abs_out_path = out_path.resolve()

    # 1. Try specific binary first
    binary_path = shutil.which(NANO_BANANA_PRO_BIN)
    if binary_path:
        if not GEMINI_API_KEY:
            print("[NanoBananaPro] GEMINI_API_KEY not set. Falling back.")
            return None

        cmd = [
            binary_path,
            "--mode", "image",
            "--prompt", prompt,
            "--style", NANO_BANANA_PRO_STYLE,
            "--width", str(NANO_BANANA_PRO_WIDTH),
            "--height", str(NANO_BANANA_PRO_HEIGHT),
            "--output", str(out_path),
            "--gemini-model", NANO_BANANA_GEMINI_MODEL,
            "--gemini-api-key", GEMINI_API_KEY
        ]

        try:
            subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True,
                timeout=NANO_BANANA_PRO_TIMEOUT,
                env={
                    **os.environ,
                    "GEMINI_API_KEY": GEMINI_API_KEY
                }
            )
            if not out_path.exists():
                print("[NanoBananaPro] generation succeeded but output file missing.")
                return None
            return out_path
        except subprocess.CalledProcessError as exc:
            print("[NanoBananaPro] generation failed:", exc.stderr or exc.stdout)
        except subprocess.TimeoutExpired:
            print("[NanoBananaPro] generation timed out.")
        except Exception as exc:
            print("[NanoBananaPro] unexpected error:", exc)
    
    # ... (previous code) ...

    # 2. Fallback to 'gemini' CLI
    gemini_path = shutil.which("gemini")
    if gemini_path:
        print("[NanoBananaPro] 'nanobanana' binary not found, trying via 'gemini' CLI...")
        
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

    print(f"[NanoBananaPro] binary '{NANO_BANANA_PRO_BIN}' not found and Gemini CLI failed/missing. Falling back.")
    return None
