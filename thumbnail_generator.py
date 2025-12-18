"""
Thumbnail Generator - Creates YouTube thumbnails
Background: NanoBanana Pro
Text Overlay: PIL (reliable text rendering)
"""
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from typing import Optional
from nano_banana_client import generate_image

# Environment
USE_NANO_BANANA_PRO = os.getenv("USE_NANO_BANANA_PRO", "false").lower() == "true"

# Thumbnail dimensions (YouTube recommended: 1280x720)
THUMBNAIL_WIDTH = 1280
THUMBNAIL_HEIGHT = 720

# Text styling
TITLE_FONT_SIZE = 80
SUBTITLE_FONT_SIZE = 48
TEXT_COLOR = (255, 255, 255)
SHADOW_COLOR = (0, 0, 0)
MAX_TITLE_CHARS_PER_LINE = 18


def get_japanese_font(size: int):
    """Get a bold font that supports Japanese"""
    font_paths = [
        # Linux (Docker)
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        # macOS
        "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc",
        "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",
        # Windows
        "C:\\Windows\\Fonts\\msgothic.ttc",
    ]

    for path in font_paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except:
                continue

    # Fallback
    try:
        return ImageFont.truetype("DejaVuSans-Bold.ttf", size)
    except:
        return ImageFont.load_default()


def analyze_background_brightness(image: Image.Image, region: tuple = None) -> float:
    """
    Analyze the brightness of an image region.

    Args:
        image: PIL Image
        region: (x1, y1, x2, y2) tuple for region to analyze, or None for center region

    Returns:
        Average brightness (0.0 = black, 1.0 = white)
    """
    # Default to center region for text placement
    if region is None:
        width, height = image.size
        region = (
            width // 4,
            height // 3,
            3 * width // 4,
            2 * height // 3
        )

    # Crop to region
    x1, y1, x2, y2 = region
    cropped = image.crop((x1, y1, x2, y2))

    # Convert to grayscale
    gray = cropped.convert('L')

    # Calculate average brightness
    pixels = list(gray.getdata())
    avg_brightness = sum(pixels) / len(pixels) / 255.0

    return avg_brightness


def select_text_color(bg_brightness: float) -> tuple:
    """
    Select text color based on background brightness for maximum contrast.

    Args:
        bg_brightness: Background brightness (0.0 - 1.0)

    Returns:
        (R, G, B) tuple for text color
    """
    # If background is bright, use dark text
    # If background is dark, use white text
    # Threshold at 0.5 (middle brightness)

    if bg_brightness > 0.5:
        # Bright background -> dark text
        return (0, 0, 0)  # Black
    else:
        # Dark background -> white text
        return (255, 255, 255)  # White


def select_shadow_color(text_color: tuple) -> tuple:
    """
    Select shadow color based on text color for contrast.

    Args:
        text_color: (R, G, B) tuple

    Returns:
        (R, G, B) tuple for shadow color
    """
    # If text is white, use black shadow
    # If text is black, use white shadow
    r, g, b = text_color
    brightness = (r + g + b) / 3

    if brightness > 127:
        return (0, 0, 0)  # Black shadow for white text
    else:
        return (255, 255, 255)  # White shadow for black text


def wrap_text(text: str, font, max_width: int) -> list:
    """Wrap text to fit within max_width"""
    lines = []
    current_line = ""

    for char in text:
        test_line = current_line + char
        bbox = font.getbbox(test_line)
        if bbox[2] - bbox[0] <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = char

    if current_line:
        lines.append(current_line)

    return lines or [""]


def add_text_with_shadow(
    draw: ImageDraw.Draw,
    position: tuple,
    text: str,
    font: ImageFont.FreeTypeFont,
    text_color: tuple,
    shadow_offset: int = 6
):
    """Draw text with strong shadow for readability"""
    x, y = position

    # Draw shadow (multiple layers for stronger effect)
    for offset in range(1, shadow_offset + 1):
        draw.text((x + offset, y + offset), text, font=font, fill=SHADOW_COLOR)

    # Draw main text
    draw.text(position, text, font=font, fill=text_color)


def create_thumbnail(
    background_image_path: Path,
    thumbnail_text: str = "",
    subtitle_text: str = "",
    output_path: Path = None,
    accent_color_index: int = 0,
    topic_badge_text: str = "",
    badge_icon_path: Optional[Path] = None,
    layout_name: Optional[str] = None,
    image_prompt: Optional[str] = None,
    emotion: Optional[str] = None,
    image_model: Optional[str] = None
) -> Path:
    """
    Create a YouTube thumbnail with NanoBanana background + PIL text overlay.

    Args:
        background_image_path: Path to background image (used if not generating with NanoBanana)
        thumbnail_text: Main text to overlay
        subtitle_text: Optional subtitle text
        output_path: Output path for thumbnail
        accent_color_index: Accent color index (for compatibility)
        topic_badge_text: Badge text (for compatibility)
        badge_icon_path: Badge icon (not used)
        layout_name: Layout preset (not used)
        image_prompt: Prompt for NanoBanana to generate background (without text instructions)
        emotion: Emotion hint (not used)
        image_model: Specific model to use for image generation (e.g., 'gpt-image-1.5')

    Returns:
        Path to generated thumbnail
    """
    if output_path is None:
        output_path = background_image_path.parent / "thumbnail.jpg"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Step 1: Generate or load background image
    bg: Image.Image
    if image_prompt:
        # Always attempt to generate background if an image_prompt is given
        print(f"Generating background image with prompt: {image_prompt[:50]}...")
        # nano_banana_client.generate_image will handle USE_NANO_BANANA_PRO and model selection
        generated_image_path = generate_image(image_prompt, output_path, model=image_model)
        
        if generated_image_path and generated_image_path.exists():
            bg = Image.open(generated_image_path).convert('RGB')
        else:
            print(f"Image generation failed, falling back to provided background: {background_image_path}")
            # Fallback to the provided path if image generation failed
            bg = Image.open(background_image_path).convert('RGB')
    else:
        # No image_prompt, so just load the provided background image
        print(f"Loading background from: {background_image_path}")
        bg = Image.open(background_image_path).convert('RGB')

    # Resize to YouTube thumbnail dimensions
    bg = bg.resize((THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT), Image.Resampling.LANCZOS)

    # Step 2: Add text overlay with PIL (reliable text rendering)
    if thumbnail_text:
        print(f"Adding text overlay: {thumbnail_text}")

        # Analyze background brightness to select appropriate text color
        bg_brightness = analyze_background_brightness(bg)
        text_color = select_text_color(bg_brightness)
        shadow_color = select_shadow_color(text_color)

        print(f"  Background brightness: {bg_brightness:.2f} (0=dark, 1=bright)")
        print(f"  Selected text color: {'White' if text_color == (255, 255, 255) else 'Black'}")

        draw = ImageDraw.Draw(bg)

        # Get font
        title_font = get_japanese_font(TITLE_FONT_SIZE)

        # Wrap text to fit width (leave margins)
        max_text_width = THUMBNAIL_WIDTH - 200  # 100px margin on each side
        lines = wrap_text(thumbnail_text, title_font, max_text_width)

        # Limit to 2 lines max
        if len(lines) > 2:
            lines = lines[:2]
            if lines[-1]:
                lines[-1] = lines[-1][:-1] + "…"

        # Calculate vertical position (center or bottom third)
        line_height = TITLE_FONT_SIZE + 20
        total_text_height = len(lines) * line_height
        start_y = (THUMBNAIL_HEIGHT - total_text_height) // 2

        # Draw each line with shadow
        for i, line in enumerate(lines):
            # Get line width for centering
            bbox = title_font.getbbox(line)
            line_width = bbox[2] - bbox[0]
            x = (THUMBNAIL_WIDTH - line_width) // 2
            y = start_y + (i * line_height)

            # Draw shadow
            for offset in range(1, 7):
                draw.text((x + offset, y + offset), line, font=title_font, fill=shadow_color)

            # Draw main text
            draw.text((x, y), line, font=title_font, fill=text_color)

        print(f"✓ Text overlay added: {len(lines)} lines")

    # Optional: Add badge/category label in top-left corner
    if topic_badge_text:
        draw = ImageDraw.Draw(bg)
        badge_font = get_japanese_font(32)
        badge_text = topic_badge_text.upper()[:10]  # Limit length

        # Draw badge background
        badge_padding = 15
        bbox = badge_font.getbbox(badge_text)
        badge_width = bbox[2] - bbox[0] + (badge_padding * 2)
        badge_height = bbox[3] - bbox[1] + (badge_padding * 2)

        # Semi-transparent background
        badge_bg = Image.new('RGBA', (badge_width, badge_height), (0, 0, 0, 180))
        bg.paste(badge_bg, (30, 30), badge_bg)

        # Draw badge text
        draw.text(
            (30 + badge_padding, 30 + badge_padding),
            badge_text,
            font=badge_font,
            fill=(255, 200, 100)  # Orange-yellow color
        )

        print(f"✓ Badge added: {badge_text}")

    # Save thumbnail
    bg.save(output_path, 'JPEG', quality=95, optimize=True)

    print(f"✓ Thumbnail saved: {output_path}")

    return output_path


def create_multiple_thumbnail_variants(
    background_image_path: Path,
    thumbnail_text: str,
    subtitle_text: str = "",
    output_dir: Path = None,
    count: int = 3
) -> list:
    """
    Create multiple thumbnail variants.

    Args:
        background_image_path: Path to background image
        thumbnail_text: Main text
        subtitle_text: Optional subtitle
        output_dir: Output directory
        count: Number of variants to create

    Returns:
        List of paths to generated thumbnails
    """
    if output_dir is None:
        output_dir = background_image_path.parent

    thumbnails = []
    for i in range(count):
        output_path = output_dir / f"thumbnail_variant_{i+1}.jpg"
        create_thumbnail(
            background_image_path,
            thumbnail_text,
            subtitle_text,
            output_path,
            accent_color_index=i
        )
        thumbnails.append(output_path)

    print(f"Created {len(thumbnails)} thumbnail variants")
    return thumbnails


if __name__ == "__main__":
    # Test thumbnail generation
    test_dir = Path("test_output")
    test_dir.mkdir(exist_ok=True)

    # Example: Generate background with NanoBanana, add text with PIL
    test_image_prompt = (
        "YouTube thumbnail anime style: "
        "Modern tech newsroom with dynamic lighting, "
        "OpenAI and Amazon logos, golden coins, lightning effects. "
        "Vibrant colors, high contrast, cinematic. "
        "NO TEXT - background only."
    )

    # Create thumbnail
    thumbnail_path = create_thumbnail(
        background_image_path=test_dir / "fallback_bg.png",
        output_path=test_dir / "test_thumbnail_with_text_gpt_image_1_5.jpg",
        thumbnail_text="OpenAI 最新情報総まとめ",
        topic_badge_text="AI_NEWS",
        image_prompt=test_image_prompt,
        image_model="gpt-image-1.5" # Use the new model
    )

    print(f"\n✓ Test complete! Thumbnail saved to: {thumbnail_path}")
    print(f"  USE_NANO_BANANA_PRO = {USE_NANO_BANANA_PRO}")
    print("  Background: NanoBanana (or DALL-E)")
    print("  Text: PIL overlay (reliable)")
