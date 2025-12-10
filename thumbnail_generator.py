"""
Thumbnail Generator - Creates eye-catching YouTube thumbnails
Based on the blog's automated thumbnail generation
"""
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from typing import Tuple, Optional


# Thumbnail dimensions (YouTube recommended: 1280x720)
THUMBNAIL_WIDTH = 1280
THUMBNAIL_HEIGHT = 720

# Character assets
ASSETS_DIR = Path(__file__).parent / "assets" / "characters"
MALE_CHARACTER_PATH = ASSETS_DIR / "male_host.png"
FEMALE_CHARACTER_PATH = ASSETS_DIR / "female_host.png"

# Character display settings
CHARACTER_HEIGHT = 400  # Large size for visibility
CHARACTER_SPACING = 20  # Space between characters
CHARACTER_MARGIN_RIGHT = 40  # Right margin
CHARACTER_MARGIN_BOTTOM = 20  # Bottom margin
CHARACTER_SHADOW_OFFSET = (18, 18)
CHARACTER_SHADOW_BLUR = 18
CHARACTER_SHADOW_COLOR = (0, 0, 0, 160)

# Text styling
TITLE_FONT_SIZE = 80
SUBTITLE_FONT_SIZE = 48
TEXT_COLOR = (255, 255, 255)
SHADOW_COLOR = (0, 0, 0)
ACCENT_COLORS = [
    (255, 200, 100),  # Orange
    (100, 200, 255),  # Blue
    (255, 150, 150),  # Pink
    (150, 255, 150),  # Green
]


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
    position: Tuple[int, int],
    text: str,
    font: ImageFont.FreeTypeFont,
    text_color: Tuple[int, int, int],
    shadow_offset: int = 4
):
    """Draw text with shadow for better readability"""
    x, y = position

    # Draw shadow (multiple layers for stronger effect)
    for offset in range(1, shadow_offset + 1):
        draw.text((x + offset, y + offset), text, font=font, fill=SHADOW_COLOR)

    # Draw main text
    draw.text(position, text, font=font, fill=text_color)


def _load_character_images(target_height: int = CHARACTER_HEIGHT) -> Optional[Tuple[Image.Image, Image.Image]]:
    """Load and resize character images if available"""
    if not MALE_CHARACTER_PATH.exists() or not FEMALE_CHARACTER_PATH.exists():
        return None

    try:
        male_char = Image.open(MALE_CHARACTER_PATH).convert('RGBA')
        female_char = Image.open(FEMALE_CHARACTER_PATH).convert('RGBA')
    except Exception as e:
        print(f"Warning: Failed to load character images: {e}")
        return None

    def resize_character(char_img: Image.Image) -> Image.Image:
        aspect_ratio = char_img.width / char_img.height
        new_width = int(target_height * aspect_ratio)
        return char_img.resize((new_width, target_height), Image.Resampling.LANCZOS)

    return resize_character(male_char), resize_character(female_char)


def _paste_with_shadow(
    base: Image.Image,
    char_img: Image.Image,
    position: Tuple[int, int],
    shadow_offset: Tuple[int, int] = CHARACTER_SHADOW_OFFSET,
    blur_radius: int = CHARACTER_SHADOW_BLUR
) -> Image.Image:
    """Paste character with a soft drop shadow to blend with background"""
    mask = char_img.split()[-1]
    shadow_layer = Image.new('RGBA', base.size, (0, 0, 0, 0))

    shadow_img = Image.new('RGBA', char_img.size, CHARACTER_SHADOW_COLOR)
    shadow_layer.paste(
        shadow_img,
        (position[0] + shadow_offset[0], position[1] + shadow_offset[1]),
        mask
    )
    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(blur_radius))
    base = Image.alpha_composite(base, shadow_layer)
    base.paste(char_img, position, mask)
    return base


def add_characters_to_thumbnail(
    thumbnail: Image.Image,
    add_characters: bool = True,
    characters: Optional[Tuple[Image.Image, Image.Image]] = None
) -> Image.Image:
    """
    Add Ghibli-style dialogue characters to the bottom-right corner

    Args:
        thumbnail: Base thumbnail image
        add_characters: Whether to add characters (default: True)

    Returns:
        Thumbnail with characters composited
    """
    if not add_characters:
        return thumbnail

    if characters is None:
        characters = _load_character_images()
    if not characters:
        print("Warning: Character images not found, skipping character overlay")
        return thumbnail

    male_char, female_char = characters

    # Calculate positions (bottom-right corner)
    # Place female on the right, male on the left
    female_x = THUMBNAIL_WIDTH - CHARACTER_MARGIN_RIGHT - female_char.width
    male_x = female_x - CHARACTER_SPACING - male_char.width
    char_y = THUMBNAIL_HEIGHT - CHARACTER_MARGIN_BOTTOM - CHARACTER_HEIGHT

    # Convert thumbnail to RGBA for compositing
    thumbnail_rgba = thumbnail.convert('RGBA')

    # Composite characters
    thumbnail_rgba = _paste_with_shadow(thumbnail_rgba, male_char, (male_x, char_y))
    thumbnail_rgba = _paste_with_shadow(thumbnail_rgba, female_char, (female_x, char_y))

    # Convert back to RGB
    return thumbnail_rgba.convert('RGB')


def create_thumbnail(
    background_image_path: Path,
    thumbnail_text: str,
    subtitle_text: str = "",
    output_path: Path = None,
    accent_color_index: int = 0,
    add_characters: bool = True
) -> Path:
    """
    Create a YouTube thumbnail with text overlay and character images

    Args:
        background_image_path: Path to background image
        thumbnail_text: Main text (large, eye-catching)
        subtitle_text: Optional subtitle text
        output_path: Output path for thumbnail
        accent_color_index: Index of accent color (0-3)
        add_characters: Add Ghibli-style dialogue characters (default: True)

    Returns:
        Path to generated thumbnail
    """
    if output_path is None:
        output_path = background_image_path.parent / "thumbnail.jpg"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Preload characters if needed (also used for text layout)
    characters = _load_character_images() if add_characters else None

    # Load and prepare background
    bg = Image.open(background_image_path).convert('RGB')

    # Resize to thumbnail dimensions
    bg = bg.resize((THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT), Image.Resampling.LANCZOS)

    # Apply slight blur and darken for better text readability
    bg = bg.filter(ImageFilter.GaussianBlur(radius=2))
    enhancer = ImageEnhance.Brightness(bg)
    bg = enhancer.enhance(0.6)  # Darken to 60%

    # Create overlay for text
    overlay = Image.new('RGBA', bg.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Add colored accent bar at top
    accent_color = ACCENT_COLORS[accent_color_index % len(ACCENT_COLORS)]
    draw.rectangle([(0, 0), (THUMBNAIL_WIDTH, 20)], fill=accent_color + (230,))

    # Add semi-transparent gradient overlay at bottom for text background
    gradient_height = 400
    for i in range(gradient_height):
        alpha = int((i / gradient_height) * 180)
        y = THUMBNAIL_HEIGHT - gradient_height + i
        draw.rectangle(
            [(0, y), (THUMBNAIL_WIDTH, y + 1)],
            fill=(0, 0, 0, alpha)
        )

    # Composite overlay
    bg_rgba = bg.convert('RGBA')
    bg = Image.alpha_composite(bg_rgba, overlay).convert('RGB')
    draw = ImageDraw.Draw(bg)

    # Get fonts
    title_font = get_japanese_font(TITLE_FONT_SIZE)
    subtitle_font = get_japanese_font(SUBTITLE_FONT_SIZE)

    # Calculate text positioning
    text_margin = 60
    character_block_width = 0
    if characters:
        character_block_width = (
            characters[0].width + characters[1].width +
            CHARACTER_SPACING + CHARACTER_MARGIN_RIGHT + 60
        )

    if character_block_width:
        max_text_width = THUMBNAIL_WIDTH - character_block_width - text_margin
    else:
        max_text_width = THUMBNAIL_WIDTH - (text_margin * 2)

    # Wrap main text
    title_lines = wrap_text(thumbnail_text, title_font, max_text_width)

    # Calculate total height
    title_line_height = TITLE_FONT_SIZE + 10
    total_title_height = len(title_lines) * title_line_height

    # Starting Y position (centered in bottom half)
    start_y = THUMBNAIL_HEIGHT - 350

    # Draw main title
    current_y = start_y
    for line in title_lines:
        bbox = title_font.getbbox(line)
        text_width = bbox[2] - bbox[0]
        if character_block_width:
            x = text_margin
        else:
            x = (THUMBNAIL_WIDTH - text_width) // 2

        add_text_with_shadow(
            draw, (x, current_y), line, title_font, TEXT_COLOR, shadow_offset=6
        )
        current_y += title_line_height

    # Draw subtitle if provided
    if subtitle_text:
        current_y += 20  # Gap between title and subtitle
        subtitle_lines = wrap_text(subtitle_text, subtitle_font, max_text_width)

        for line in subtitle_lines:
            bbox = subtitle_font.getbbox(line)
            text_width = bbox[2] - bbox[0]
            if character_block_width:
                x = text_margin
            else:
                x = (THUMBNAIL_WIDTH - text_width) // 2

            add_text_with_shadow(
                draw, (x, current_y), line, subtitle_font, accent_color, shadow_offset=4
            )
            current_y += SUBTITLE_FONT_SIZE + 5

    # Add decorative corner elements
    corner_size = 40
    draw.rectangle(
        [(0, 0), (corner_size, corner_size)],
        fill=accent_color
    )
    draw.rectangle(
        [(THUMBNAIL_WIDTH - corner_size, 0), (THUMBNAIL_WIDTH, corner_size)],
        fill=accent_color
    )

    # Add dialogue characters to bottom-right
    if add_characters:
        bg = add_characters_to_thumbnail(bg, add_characters=True, characters=characters)

    # Save thumbnail
    bg.save(output_path, 'JPEG', quality=95, optimize=True)
    print(f"Thumbnail created: {output_path}")

    return output_path


def create_multiple_thumbnail_variants(
    background_image_path: Path,
    thumbnail_text: str,
    subtitle_text: str = "",
    output_dir: Path = None,
    count: int = 3,
    add_characters: bool = True
) -> list:
    """
    Create multiple thumbnail variants with different accent colors

    Args:
        background_image_path: Path to background image
        thumbnail_text: Main text
        subtitle_text: Optional subtitle
        output_dir: Output directory
        count: Number of variants to create
        add_characters: Add dialogue characters (default: True)

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
            accent_color_index=i,
            add_characters=add_characters
        )
        thumbnails.append(output_path)

    print(f"Created {len(thumbnails)} thumbnail variants")
    return thumbnails


if __name__ == "__main__":
    # Test thumbnail generation
    from nano_banana_client import generate_image

    # Generate a test background
    test_dir = Path("test_output")
    test_dir.mkdir(exist_ok=True)

    bg_path = test_dir / "test_bg.png"
    generate_image("Cozy Japanese room, Lo-fi anime style, warm lighting", bg_path)

    # Create thumbnail
    create_thumbnail(
        bg_path,
        "経済ニュース解説",
        "最新トレンドを分析",
        test_dir / "test_thumbnail.jpg"
    )

    print("Test complete!")
