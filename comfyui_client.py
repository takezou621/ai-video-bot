"""
ComfyUI Client - Generate images using ComfyUI API
Supports Qwen Image Model (qwen_image_2512_fp8_e4m3fn)
"""
import os
import json
import uuid
import time
import requests
from pathlib import Path
from typing import Optional, Dict, Any

# Configuration
COMFYUI_URL = os.getenv("COMFYUI_URL", "http://127.0.0.1:8188")

# Default model configuration (Qwen Image)
DEFAULT_UNET = os.getenv("COMFYUI_UNET", "qwen_image_2512_fp8_e4m3fn.safetensors")
DEFAULT_CLIP = os.getenv("COMFYUI_CLIP", "qwen_2.5_vl_7b_fp8_scaled.safetensors")
DEFAULT_VAE = os.getenv("COMFYUI_VAE", "qwen_image_vae.safetensors")
DEFAULT_CLIP_TYPE = os.getenv("COMFYUI_CLIP_TYPE", "qwen_image")


def is_available() -> bool:
    """Check if ComfyUI is reachable."""
    try:
        response = requests.get(f"{COMFYUI_URL}/system_stats", timeout=3)
        return response.status_code == 200
    except Exception:
        return False


def get_workflow(
    prompt: str,
    width: int = 1024,
    height: int = 576,
    steps: int = 20,
    cfg: float = 7.0,
    seed: int = -1,
    negative_prompt: str = ""
) -> Dict[str, Any]:
    """
    Create a workflow for Qwen Image generation.
    Uses Qwen Image specific nodes for proper model compatibility.
    """
    if seed == -1:
        seed = int(time.time() * 1000) % (2**32)

    if not negative_prompt:
        negative_prompt = "nsfw, low quality, worst quality, bad anatomy, text, watermark"

    # Round dimensions to multiple of 16 (required by model)
    width = (width // 16) * 16
    height = (height // 16) * 16

    # Workflow nodes for Qwen Image model
    workflow = {
        # Load UNET (Diffusion Model)
        "1": {
            "class_type": "UNETLoader",
            "inputs": {
                "unet_name": DEFAULT_UNET,
                "weight_dtype": "fp8_e4m3fn"
            }
        },
        # Load CLIP with qwen_image type
        "2": {
            "class_type": "CLIPLoader",
            "inputs": {
                "clip_name": DEFAULT_CLIP,
                "type": DEFAULT_CLIP_TYPE
            }
        },
        # Load VAE
        "3": {
            "class_type": "VAELoader",
            "inputs": {
                "vae_name": DEFAULT_VAE
            }
        },
        # Empty Qwen Image Latent (with layers parameter)
        "4": {
            "class_type": "EmptyQwenImageLayeredLatentImage",
            "inputs": {
                "width": width,
                "height": height,
                "layers": 3,
                "batch_size": 1
            }
        },
        # Encode positive prompt with Qwen Image encoder
        "5": {
            "class_type": "TextEncodeQwenImageEdit",
            "inputs": {
                "prompt": prompt,
                "clip": ["2", 0]
            }
        },
        # Encode negative prompt with Qwen Image encoder
        "6": {
            "class_type": "TextEncodeQwenImageEdit",
            "inputs": {
                "prompt": negative_prompt,
                "clip": ["2", 0]
            }
        },
        # KSampler
        "7": {
            "class_type": "KSampler",
            "inputs": {
                "model": ["1", 0],
                "positive": ["5", 0],
                "negative": ["6", 0],
                "latent_image": ["4", 0],
                "seed": seed,
                "steps": steps,
                "cfg": cfg,
                "sampler_name": "euler",
                "scheduler": "simple",
                "denoise": 1.0
            }
        },
        # VAE Decode
        "8": {
            "class_type": "VAEDecode",
            "inputs": {
                "samples": ["7", 0],
                "vae": ["3", 0]
            }
        },
        # Save Image (to ComfyUI output folder)
        "9": {
            "class_type": "SaveImage",
            "inputs": {
                "images": ["8", 0],
                "filename_prefix": "comfyui_gen"
            }
        }
    }

    return workflow


def queue_prompt(workflow: Dict[str, Any], client_id: str = None) -> str:
    """
    Queue a prompt for execution.
    Returns the prompt_id.
    """
    if client_id is None:
        client_id = str(uuid.uuid4())

    payload = {
        "prompt": workflow,
        "client_id": client_id
    }

    response = requests.post(f"{COMFYUI_URL}/prompt", json=payload)
    response.raise_for_status()

    result = response.json()
    return result.get("prompt_id"), client_id


def wait_for_completion(prompt_id: str, client_id: str, timeout: int = 600) -> bool:
    """
    Wait for prompt execution to complete using HTTP polling.
    Returns True if successful.
    """
    start_time = time.time()
    last_print_time = start_time
    poll_interval = 2  # seconds

    while True:
        elapsed = time.time() - start_time

        if elapsed > timeout:
            print("[ComfyUI] Timeout waiting for completion")
            return False

        try:
            # Check queue status
            queue_response = requests.get(f"{COMFYUI_URL}/queue", timeout=5)
            if queue_response.status_code == 200:
                queue_data = queue_response.json()
                running = queue_data.get("queue_running", [])
                pending = queue_data.get("queue_pending", [])

                # Check if our prompt is still in queue
                prompt_in_queue = False
                for item in running + pending:
                    if len(item) > 1 and item[1] == prompt_id:
                        prompt_in_queue = True
                        break

                # If not in queue, check history
                if not prompt_in_queue:
                    history_response = requests.get(
                        f"{COMFYUI_URL}/history/{prompt_id}", timeout=5
                    )
                    if history_response.status_code == 200:
                        history = history_response.json()
                        if prompt_id in history:
                            status = history[prompt_id].get("status", {})
                            if status.get("completed"):
                                print("[ComfyUI] Generation completed")
                                return True
                            if status.get("status_str") == "error":
                                print(f"[ComfyUI] Execution error")
                                return False
                            # Completed successfully (outputs exist)
                            if history[prompt_id].get("outputs"):
                                print("[ComfyUI] Generation completed")
                                return True

            # Print progress periodically
            if time.time() - last_print_time > 10:
                print(f"[ComfyUI] Waiting... ({elapsed:.0f}s elapsed)")
                last_print_time = time.time()

        except requests.RequestException as e:
            print(f"[ComfyUI] Poll error: {e}")

        time.sleep(poll_interval)


def get_history(prompt_id: str) -> Dict:
    """Get execution history for a prompt."""
    response = requests.get(f"{COMFYUI_URL}/history/{prompt_id}")
    response.raise_for_status()
    return response.json()


def get_output_images(prompt_id: str) -> list:
    """Get output image paths from execution history."""
    history = get_history(prompt_id)

    if prompt_id not in history:
        return []

    outputs = history[prompt_id].get("outputs", {})
    images = []

    for node_id, output in outputs.items():
        if "images" in output:
            for img in output["images"]:
                images.append({
                    "filename": img.get("filename"),
                    "subfolder": img.get("subfolder", ""),
                    "type": img.get("type", "output")
                })

    return images


def download_image(image_info: Dict, output_path: Path) -> Optional[Path]:
    """Download an image from ComfyUI."""
    params = {
        "filename": image_info["filename"],
        "subfolder": image_info.get("subfolder", ""),
        "type": image_info.get("type", "output")
    }

    response = requests.get(f"{COMFYUI_URL}/view", params=params)

    if response.status_code == 200:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(response.content)
        return output_path

    return None


def generate_image(
    prompt: str,
    output_path: Path,
    width: int = 1024,
    height: int = 576,
    steps: int = 20,
    cfg: float = 7.0,
    seed: int = -1,
    negative_prompt: str = ""
) -> Optional[Path]:
    """
    Generate an image using ComfyUI.

    Args:
        prompt: Positive prompt for image generation
        output_path: Path to save the generated image
        width: Image width
        height: Image height
        steps: Sampling steps
        cfg: CFG scale
        seed: Random seed (-1 for random)
        negative_prompt: Negative prompt

    Returns:
        Path to the saved image or None if failed.
    """
    if not is_available():
        print("[ComfyUI] Not available")
        return None

    print(f"[ComfyUI] Generating image: {prompt[:60]}...")
    print(f"[ComfyUI] Size: {width}x{height}, Steps: {steps}, CFG: {cfg}")

    try:
        # Create workflow
        workflow = get_workflow(
            prompt=prompt,
            width=width,
            height=height,
            steps=steps,
            cfg=cfg,
            seed=seed,
            negative_prompt=negative_prompt
        )

        # Queue prompt
        prompt_id, client_id = queue_prompt(workflow)
        print(f"[ComfyUI] Queued prompt: {prompt_id}")

        # Wait for completion
        if not wait_for_completion(prompt_id, client_id):
            print("[ComfyUI] Generation failed")
            return None

        # Get output images
        images = get_output_images(prompt_id)

        if not images:
            print("[ComfyUI] No images in output")
            return None

        # Download first image
        result = download_image(images[0], Path(output_path))

        if result:
            print(f"[ComfyUI] Image saved to {output_path}")
            return result
        else:
            print("[ComfyUI] Failed to download image")
            return None

    except Exception as e:
        print(f"[ComfyUI] Error: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    print("=== ComfyUI Client Test ===\n")

    print(f"ComfyUI URL: {COMFYUI_URL}")
    print(f"Available: {is_available()}")

    if is_available():
        # Test generation
        test_prompt = (
            "Lo-fi anime style podcast studio background, warm ambient lighting, "
            "comfortable desk with microphone, bookshelves, city view through window, "
            "cozy atmosphere, soft pastel colors, Makoto Shinkai style"
        )

        test_output = Path("/tmp/comfyui_test/test_image.png")

        result = generate_image(
            prompt=test_prompt,
            output_path=test_output,
            width=1152,
            height=648,
            steps=20
        )

        if result:
            print(f"\n✓ Test passed! Image saved to: {result}")
        else:
            print("\n✗ Test failed")
    else:
        print("\nComfyUI is not running. Start it first.")
