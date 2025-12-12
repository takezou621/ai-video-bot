"""
Generate Ghibli-style dialogue characters for thumbnails
"""
from pathlib import Path
from nano_banana_client import generate_image

# Character prompts
MALE_CHARACTER_PROMPT = """
Studio Ghibli style character illustration, friendly young Japanese man in his late 20s,
wearing casual modern clothes (hoodie and jeans), warm smile, expressive eyes,
clean and simple design, soft colors, transparent background,
full body character standing pose, podcast host vibe, approachable and intelligent look,
high quality anime art style like Hayao Miyazaki films
"""

FEMALE_CHARACTER_PROMPT = """
Studio Ghibli style character illustration, cheerful young Japanese woman in her mid 20s,
wearing casual modern clothes (cardigan and skirt), bright smile, curious eyes,
clean and simple design, soft colors, transparent background,
full body character standing pose, podcast co-host vibe, friendly and enthusiastic look,
high quality anime art style like Hayao Miyazaki films
"""

def main():
    assets_dir = Path(__file__).parent / "assets" / "characters"
    assets_dir.mkdir(parents=True, exist_ok=True)

    print("Generating male character...")
    male_path = assets_dir / "male_host.png"
    generate_image(MALE_CHARACTER_PROMPT, male_path)
    print(f"✓ Male character saved: {male_path}")

    print("\nGenerating female character...")
    female_path = assets_dir / "female_host.png"
    generate_image(FEMALE_CHARACTER_PROMPT, female_path)
    print(f"✓ Female character saved: {female_path}")

    print("\n✅ Character generation complete!")
    print(f"   Male: {male_path}")
    print(f"   Female: {female_path}")

if __name__ == "__main__":
    main()
