import os
from pathlib import Path

# Mock environment if not set
if "SD_WEBUI_URL" not in os.environ:
    # Check if we are likely in docker
    if os.path.exists("/.dockerenv"):
        os.environ["SD_WEBUI_URL"] = "http://stable-diffusion:3000"
    else:
        os.environ["SD_WEBUI_URL"] = "http://localhost:7860"

import sd_client

def test_sd_generation():
    url = os.environ["SD_WEBUI_URL"]
    print(f"Testing Stable Diffusion Integration at {url}...")
    
    if not sd_client.is_available():
        print(f"❌ SD WebUI is not reachable at {url}")
        print("   (This is expected if running outside Docker or if SD container is not up)")
        return

    output_path = Path("outputs/tests/sd_test.png")
    prompt = "A futuristic city with flying cars, anime style, highly detailed, 8k"
    
    print(f"Generating image for: '{prompt}'")
    result = sd_client.generate_image_sd(prompt, output_path)
    
    if result and result.exists():
        print(f"✅ Success! Image saved to: {result}")
    else:
        print("❌ Failed to generate image.")

if __name__ == "__main__":
    test_sd_generation()
