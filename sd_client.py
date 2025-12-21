import os
import json
import requests
import base64
import time
from pathlib import Path
from typing import Optional

# Configuration
SD_WEBUI_URL = os.getenv("SD_WEBUI_URL", "http://stable-diffusion:7860")
SD_MODEL_CHECKPOINT = os.getenv("SD_MODEL_CHECKPOINT", "")  # Leave empty to use currently loaded model

def is_available() -> bool:
    """Check if SD WebUI is reachable."""
    try:
        response = requests.get(f"{SD_WEBUI_URL}/sdapi/v1/progress", timeout=3)
        return response.status_code == 200
    except Exception:
        return False

def generate_image_sd(
    prompt: str, 
    output_path: Path, 
    width: int = 1024, 
    height: int = 576, 
    steps: int = 20,
    negative_prompt: str = ""
) -> Optional[Path]:
    """
    Generate an image using Stable Diffusion WebUI API.
    
    Args:
        prompt: Positive prompt
        output_path: Path to save the generated image
        width: Image width (default 1024 for SDXL or 512 for SD1.5 - adjusted by caller usually)
        height: Image height
        steps: Sampling steps
        negative_prompt: Negative prompt
        
    Returns:
        Path to the saved image or None if failed.
    """
    url = f"{SD_WEBUI_URL}/sdapi/v1/txt2img"
    
    # Default negative prompt if none provided (optimized for anime/lo-fi as per project style)
    if not negative_prompt:
        negative_prompt = "nsfw, low quality, worst quality, bad anatomy, bad composition, text, watermark, signature"

    payload = {
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "steps": steps,
        "width": width,
        "height": height,
        "sampler_name": "Euler a",  # Fast and decent
        "batch_size": 1,
        "n_iter": 1,
        "cfg_scale": 7,
        "seed": -1
    }
    
    # Optional: Override model if specified
    # Note: Switching models via API takes time, so usually better to set it in WebUI settings
    
    try:
        print(f"[SD] Requesting image from {url}...")
        
        # Start generation in background if possible, or just use a short-ish timeout and retry/poll
        # Actually, txt2img is usually blocking in the API unless specifically handled.
        # To prevent timeout, we'll use a thread or just rely on the fact that we can't easily 
        # do non-blocking txt2img without custom extensions.
        
        # Alternative: use a session and poll progress in a loop while the post is running? 
        # No, requests is blocking. 
        
        # Best approach for this CLI: print something before and increase timeout, 
        # but the CLI agent has a hard 5min limit on silence.
        
        # Let's use a simple trick: use a very long timeout but we need the main loop to print.
        # Since I can't easily change how 'requests' works without major refactor, 
        # I will wrap the call in a way that allows progress printing.
        
        import threading
        
        response_container = []
        error_container = []
        
        def make_request():
            try:
                res = requests.post(url, json=payload, timeout=600)
                response_container.append(res)
            except Exception as e:
                error_container.append(e)
        
        thread = threading.Thread(target=make_request)
        thread.start()
        
        # Poll progress while waiting
        start_time = time.time()
        while thread.is_alive():
            time.sleep(10)
            elapsed = time.time() - start_time
            try:
                prog_res = requests.get(f"{SD_WEBUI_URL}/sdapi/v1/progress", timeout=5)
                if prog_res.status_code == 200:
                    prog_data = prog_res.json()
                    progress = prog_data.get("progress", 0) * 100
                    print(f"[SD] Generation progress: {progress:.1f}% ({elapsed:.0f}s elapsed)")
            except:
                print(f"[SD] Waiting for response... ({elapsed:.0f}s elapsed)")
            
            if elapsed > 600: # 10 mins max
                print("[SD] Timeout reached (600s)")
                break
        
        thread.join(timeout=1)
        
        if error_container:
            raise error_container[0]
            
        if not response_container:
            print("[SD] Failed to get response within timeout")
            return None
            
        response = response_container[0]
        
        if response.status_code != 200:
            print(f"[SD] Error: {response.status_code} - {response.text}")
            return None
            
        r = response.json()
        
        if "images" in r and r["images"]:
            # SD WebUI returns base64 strings
            image_b64 = r["images"][0]
            image_data = base64.b64decode(image_b64)
            
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(image_data)
                
            print(f"[SD] Image saved to {output_path}")
            return output_path
        else:
            print("[SD] No images returned in response.")
            return None
            
    except Exception as e:
        print(f"[SD] Connection failed: {e}")
        return None
