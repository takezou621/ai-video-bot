"""Generate only the male character"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Import after loading env
from generate_thumbnail_characters import generate_character_image

male_prompt = """
Studio Ghibli style anime character, young Japanese man in casual modern clothes,
friendly expression, warm smile, clean simple design, soft watercolor style,
standing pose with hand gesturing as if explaining something,
light background, white or very light blue background for easy compositing,
full body visible, podcast host appearance, approachable and intelligent,
Hayao Miyazaki film quality art
"""

assets_dir = Path(__file__).parent / "assets" / "characters"
assets_dir.mkdir(parents=True, exist_ok=True)

male_path = assets_dir / "male_host.png"

print("Generating male podcast host character...")
result = generate_character_image(male_prompt, male_path)

if result:
    print(f"✓ Male character saved: {male_path}")
else:
    print(f"✗ Failed to generate male character")
