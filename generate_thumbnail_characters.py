"""
Generate Ghibli-style dialogue characters for thumbnails using DALL-E 3
"""
import os
import base64
import requests
import time
from pathlib import Path
from PIL import Image
from io import BytesIO

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def generate_character_image(prompt: str, output_path: Path, max_retries: int = 3):
    """Generate square character image using DALL-E 3"""
    if not OPENAI_API_KEY:
        print("Warning: No OPENAI_API_KEY found, skipping character generation")
        return None

    url = "https://api.openai.com/v1/images/generations"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "dall-e-3",
        "prompt": prompt,
        "n": 1,
        "size": "1024x1024",  # Square size for character portraits
        "response_format": "b64_json",
        "quality": "standard"
    }

    for attempt in range(max_retries):
        try:
            print(f"  Generating image (attempt {attempt+1}/{max_retries})...")
            r = requests.post(url, headers=headers, json=payload, timeout=120)
            data = r.json()

            if "error" in data:
                error_msg = data["error"].get("message", "Unknown API error")
                if "rate_limit" in error_msg.lower():
                    wait_time = 65
                    print(f"  Rate limit hit, waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                print(f"  API Error: {error_msg}")
                return None

            img_b64 = data["data"][0]["b64_json"]
            img_bytes = base64.b64decode(img_b64)

            # Save image
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(img_bytes)

            return output_path

        except Exception as e:
            print(f"  Error: {e}")
            if attempt < max_retries - 1:
                time.sleep(5)
                continue
            return None

    return None


def main():
    """Generate both male and female podcast host characters"""
    from dotenv import load_dotenv

    # Load environment
    load_dotenv()

    assets_dir = Path(__file__).parent / "assets" / "characters"
    assets_dir.mkdir(parents=True, exist_ok=True)

    # Character prompts - designed for thumbnail overlay
    male_prompt = """
    Studio Ghibli style anime character, young Japanese man in casual modern clothes,
    friendly expression, warm smile, clean simple design, soft watercolor style,
    standing pose with hand gesturing as if explaining something,
    light background, white or very light blue background for easy compositing,
    full body visible, podcast host appearance, approachable and intelligent,
    Hayao Miyazaki film quality art
    """

    female_prompt = """
    Studio Ghibli style anime character, young Japanese woman in casual modern clothes,
    cheerful expression, bright smile, clean simple design, soft watercolor style,
    standing pose with hand raised as if asking a question,
    light background, white or very light pink background for easy compositing,
    full body visible, podcast co-host appearance, friendly and curious,
    Hayao Miyazaki film quality art
    """

    print("="*60)
    print("Generating Thumbnail Characters")
    print("="*60)

    # Generate male character
    print("\n[1/2] Generating male podcast host character...")
    male_path = assets_dir / "male_host.png"
    result = generate_character_image(male_prompt, male_path)
    if result:
        print(f"  ✓ Male character saved: {male_path}")
    else:
        print(f"  ✗ Failed to generate male character")

    # Wait between requests to avoid rate limits
    print("\n  Waiting 10 seconds before next generation...")
    time.sleep(10)

    # Generate female character
    print("\n[2/2] Generating female podcast host character...")
    female_path = assets_dir / "female_host.png"
    result = generate_character_image(female_prompt, female_path)
    if result:
        print(f"  ✓ Female character saved: {female_path}")
    else:
        print(f"  ✗ Failed to generate female character")

    print("\n" + "="*60)
    print("Character Generation Complete!")
    print("="*60)
    print(f"\nGenerated files:")
    if male_path.exists():
        print(f"  - {male_path}")
    if female_path.exists():
        print(f"  - {female_path}")


if __name__ == "__main__":
    main()
