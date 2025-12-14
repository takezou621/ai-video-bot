"""
Thumbnail Generator - Creates eye-catching YouTube thumbnails
Inspired by best practices from high-performing economics/tech channels
"""
import os
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from typing import Tuple, Optional, Dict, List
from nano_banana_client import generate_image

# Environment
USE_NANO_BANANA_PRO = os.getenv("USE_NANO_BANANA_PRO", "false").lower() == "true"

# Thumbnail dimensions (YouTube recommended: 1280x720)
THUMBNAIL_WIDTH = 1280
THUMBNAIL_HEIGHT = 720

# Character assets
ASSETS_DIR = Path(__file__).parent / "assets" / "characters"
MALE_CHARACTER_PATH = ASSETS_DIR / "male_host.png"
FEMALE_CHARACTER_PATH = ASSETS_DIR / "female_host.png"
CHARACTER_VARIANTS = {
    "default": ("male_host.png", "female_host.png"),
    "shock": ("male_host_shock.png", "female_host_shock.png"),
    "fear": ("male_host_anxious.png", "female_host_anxious.png"),
    "joy": ("male_host_happy.png", "female_host_happy.png")
}

# Character display settings (Legacy - Removed)
# Text styling / typography constraints
TITLE_FONT_SIZE = 80
SUBTITLE_FONT_SIZE = 48
TEXT_COLOR = (255, 255, 255)
SHADOW_COLOR = (0, 0, 0)
MAX_TITLE_LINES = 2
MAX_TITLE_CHARS_PER_LINE = 12
MAX_SUBTITLE_CHARS = 28
MAX_HEADLINE_CHARS = 6
MIN_HEADLINE_CHARS = 4

ACCENT_COLORS = [
    (255, 200, 100),  # Orange
    (100, 200, 255),  # Blue
    (255, 150, 150),  # Pink
    (150, 255, 150),  # Green
]

BADGE_COLORS = [
    (255, 90, 90),
    (90, 180, 255),
    (255, 220, 120),
    (145, 255, 190),
]

PATTERN_OPACITY = 90
EMOTIONAL_KEYWORDS = [
    "危険", "衝撃", "暴露", "裏側", "最強", "地獄", "緊急",
    "神回", "やばい", "本音", "崩壊", "逆転", "暴落"
]
EMOTION_MAP = [
    ("危険", "fear"),
    ("崩壊", "fear"),
    ("暴落", "fear"),
    ("衝撃", "shock"),
    ("逆転", "joy"),
    ("最強", "joy"),
    ("やばい", "shock"),
    ("神回", "joy"),
    ("暴露", "shock")
]

THEME_LIBRARY: Dict[str, Dict[str, Tuple[int, int, int]]] = {
    "経済": {
        "accent": (255, 214, 137),
        "highlight": (255, 170, 77),
        "shadow": (15, 20, 30),
        "badge": (255, 236, 200),
    },
    "テック": {
        "accent": (129, 223, 255),
        "highlight": (120, 150, 255),
        "shadow": (12, 18, 28),
        "badge": (210, 240, 255),
    },
    "カルチャー": {
        "accent": (255, 170, 190),
        "highlight": (255, 115, 150),
        "shadow": (26, 10, 20),
        "badge": (255, 220, 235),
    },
    "ライフ": {
        "accent": (180, 255, 195),
        "highlight": (115, 215, 160),
        "shadow": (15, 28, 20),
        "badge": (220, 255, 230),
    }
}

LAYOUT_PRESETS: List[Dict] = [
    {
        "name": "left_text_right_characters",
        "text_area": {"x": 90, "y": 210, "width_ratio": 0.52},
        "text_align": "left",
        "line_spacing": TITLE_FONT_SIZE + 12,
        "subtitle_gap": 30,
        "pattern": "standard",
        "character_anchor": "right",
        "text_backdrop": True,
        "allows_characters": True
    },
    {
        "name": "badge_stack",
        "text_area": {"x": 120, "y": 200, "width_ratio": 0.50},
        "text_align": "left",
        "line_spacing": TITLE_FONT_SIZE + 16,
        "subtitle_gap": 28,
        "pattern": "standard",
        "character_anchor": "right",
        "text_backdrop": True,
        "badge_stack": True,
        "allows_characters": True
    },
    {
        "name": "center_focus",
        "text_area": {"x": 120, "y": 240, "width_ratio": 0.6, "vertical": "center"},
        "text_align": "left",
        "line_spacing": TITLE_FONT_SIZE + 18,
        "subtitle_gap": 26,
        "pattern": "diagonal",
        "character_anchor": "right",
        "text_backdrop": True,
        "allows_characters": True
    },
    {
        "name": "before_after_split",
        "text_area": {"x": 160, "y": 220, "width_ratio": 0.55},
        "text_align": "left",
        "line_spacing": TITLE_FONT_SIZE + 12,
        "subtitle_gap": 22,
        "pattern": "stripe",
        "character_anchor": "left",
        "text_backdrop": True,
        "before_after_labels": ("BEFORE", "AFTER"),
        "allows_characters": True
    },
    {
        "name": "minimal_no_characters",
        "text_area": {"x": 140, "y": 260, "width_ratio": 0.7, "vertical": "center"},
        "text_align": "center",
        "line_spacing": TITLE_FONT_SIZE + 18,
        "subtitle_gap": 20,
        "pattern": "stripe",
        "character_anchor": None,
        "text_backdrop": False,
        "allows_characters": False
    },
    {
        "name": "three_bar_layout",
        "text_area": {"x": 60, "y": 270, "width_ratio": 0.50},
        "text_align": "left",
        "line_spacing": TITLE_FONT_SIZE + 10,
        "subtitle_gap": 0,
        "pattern": "none",
        "character_anchor": "right",
        "text_backdrop": False,
        "allows_characters": True,
        "three_bar_style": True
    }
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


def wrap_text(text: str, font, max_width: int, max_lines: Optional[int] = None) -> list:
    """Wrap text to fit within max_width and limit the number of lines"""
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

    if max_lines and len(lines) > max_lines:
        lines = lines[:max_lines]
        if lines:
            lines[-1] = lines[-1].rstrip("…")  # avoid duplicate ellipsis
            lines[-1] = lines[-1][:-1] + "…" if len(lines[-1]) >= 1 else "…"

    return lines or [""]


def _sanitize_text(text: str, max_chars: int) -> str:
    cleaned = (text or "").replace("\n", "").strip()
    if len(cleaned) <= max_chars:
        return cleaned
    return cleaned[: max(0, max_chars - 1)] + "…"


def _craft_headline(text: str) -> str:
    base = (text or "").replace("　", "").replace(" ", "")
    for sep in ["｜", "|", "／", "/", "・", "、", "。", "!", "？", "?"]:
        if sep in base:
            base = base.split(sep)[0]
            break
    base = base.strip()
    if not base:
        base = "速報"
    if len(base) > MAX_HEADLINE_CHARS:
        base = base[:MAX_HEADLINE_CHARS]
    if len(base) < MIN_HEADLINE_CHARS:
        base = base + "!" * (MIN_HEADLINE_CHARS - len(base))
    if not any(word in base for word in EMOTIONAL_KEYWORDS):
        base = EMOTIONAL_KEYWORDS[hash(base) % len(EMOTIONAL_KEYWORDS)] + base[-(MAX_HEADLINE_CHARS - 2):]
        base = base[:MAX_HEADLINE_CHARS]
    return base


def _select_emotion(headline: str) -> str:
    for keyword, emotion in EMOTION_MAP:
        if keyword in headline:
            return emotion
    return "default"


def _select_theme(topic_badge_text: str, accent_index: int) -> Dict[str, Tuple[int, int, int]]:
    normalized = (topic_badge_text or "").strip()
    for key, theme in THEME_LIBRARY.items():
        if key and key in normalized:
            return dict(theme)
    accent = ACCENT_COLORS[accent_index % len(ACCENT_COLORS)]
    highlight = ACCENT_COLORS[(accent_index + 1) % len(ACCENT_COLORS)]
    badge = BADGE_COLORS[accent_index % len(BADGE_COLORS)]
    return {
        "accent": accent,
        "highlight": highlight,
        "shadow": (12, 12, 18),
        "badge": badge
    }


def _get_layout_by_name(name: str) -> Optional[Dict]:
    for layout in LAYOUT_PRESETS:
        if layout.get("name") == name:
            return dict(layout)
    return None


def _select_layout(thumbnail_text: str, add_characters: bool) -> Dict:
    candidates = [
        layout for layout in LAYOUT_PRESETS
        if add_characters or not layout.get("allows_characters", True)
    ]
    if not candidates:
        candidates = LAYOUT_PRESETS

    text = (thumbnail_text or "").lower()
    keywords_before_after = ["vs", "ｖｓ", "vs.", "対決", "比較", "before", "after", "ビフォー", "アフター"]
    if any(k in text for k in keywords_before_after):
        layout = _get_layout_by_name("before_after_split")
        if layout and (add_characters or layout.get("allows_characters", True)):
            return layout

    if sum(c.isdigit() for c in text) >= 2:
        layout = _get_layout_by_name("badge_stack")
        if layout and (add_characters or layout.get("allows_characters", True)):
            return layout

    idx = abs(hash(text)) % len(candidates)
    return dict(candidates[idx])


def _evaluate_thumbnail_quality(title_lines: List[str], subtitle_lines: List[str], layout: Dict):
    warnings = []
    total_chars = sum(len(line) for line in title_lines)
    if total_chars > MAX_TITLE_LINES * MAX_TITLE_CHARS_PER_LINE + 2:
        warnings.append("Headline is wordy; trim固有名詞 or split into subtitle")
    if len(title_lines) > MAX_TITLE_LINES:
        warnings.append("Headline exceeds max lines")
    if subtitle_lines and len("".join(subtitle_lines)) > MAX_SUBTITLE_CHARS:
        warnings.append("Subtitle is verbose")
    if layout.get("pattern") == "stripe" and not subtitle_lines:
        warnings.append("Stripe layout works best with subtitle - consider adding short補足")
    if warnings:
        print("⚠️ Thumbnail QA warnings:")
        for w in warnings:
            print(f"   - {w}")


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


def _apply_gradient_overlay(image: Image.Image, accent_color: Tuple[int, int, int]) -> Image.Image:
    overlay = Image.new('RGBA', image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    for y in range(image.height):
        ratio = y / image.height
        alpha = int(160 * ratio)
        color = (
            int(accent_color[0] * (1 - ratio) + 20 * ratio),
            int(accent_color[1] * (1 - ratio) + 20 * ratio),
            int(accent_color[2] * (1 - ratio) + 20 * ratio),
            alpha
        )
        draw.rectangle([(0, y), (image.width, y + 1)], fill=color)
    return Image.alpha_composite(image.convert('RGBA'), overlay).convert('RGB')


def _add_pattern_overlay(image: Image.Image, accent_color: Tuple[int, int, int]) -> Image.Image:
    pattern = Image.new('RGBA', image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(pattern)
    spacing = 120
    color = (*accent_color, PATTERN_OPACITY)
    for x in range(-image.height, image.width, spacing):
        draw.polygon([
            (x, 0),
            (x + 40, 0),
            (x + image.height + 40, image.height),
            (x + image.height, image.height)
        ], fill=color)
    return Image.alpha_composite(image.convert('RGBA'), pattern).convert('RGB')


def _draw_topic_badge(
    image: Image.Image,
    text: str,
    accent_color: Tuple[int, int, int],
    icon_path: Optional[Path] = None,
    badge_color: Optional[Tuple[int, int, int]] = None
) -> Image.Image:
    if not text:
        return

    draw = ImageDraw.Draw(image)
    badge_width = 360
    badge_height = 90
    x, y = 50, 40
    radius = 30

    # Shadow
    shadow = Image.new('RGBA', image.size, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.rounded_rectangle(
        [(x + 6, y + 6), (x + badge_width + 6, y + badge_height + 6)],
        radius=radius,
        fill=(0, 0, 0, 90)
    )
    image = Image.alpha_composite(image.convert('RGBA'), shadow).convert('RGB')
    draw = ImageDraw.Draw(image)
    fill_rgba = (badge_color or accent_color) + (230,)
    draw.rounded_rectangle(
        [(x, y), (x + badge_width, y + badge_height)],
        radius=radius,
        fill=fill_rgba,
        outline=(255, 255, 255),
        width=4
    )

    badge_font = get_japanese_font(42)
    badge_text = text[:12].upper()
    bbox = badge_font.getbbox(badge_text)
    text_width = bbox[2] - bbox[0]
    draw.text(
        (x + (badge_width - text_width) // 2, y + 18),
        badge_text,
        font=badge_font,
        fill=(0, 0, 0)
    )

    if icon_path and icon_path.exists():
        try:
            icon = Image.open(icon_path).convert('RGBA')
            icon = icon.resize((64, 64), Image.Resampling.LANCZOS)
            image.paste(icon, (x - 20, y - 20), icon)
        except Exception:
            pass
    return image


def _add_diagonal_stripe(image: Image.Image, color: Tuple[int, int, int]) -> Image.Image:
    overlay = Image.new('RGBA', image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    stripe_color = color + (140,)
    draw.polygon(
        [
            (-100, 200),
            (image.width, -200),
            (image.width + 100, 120),
            (0, image.height + 200)
        ],
        fill=stripe_color
    )
    return Image.alpha_composite(image.convert('RGBA'), overlay).convert('RGB')


def _apply_layout_patterns(
    image: Image.Image,
    theme: Dict[str, Tuple[int, int, int]],
    pattern_type: str = "standard"
) -> Image.Image:
    accent_color = theme.get("accent", ACCENT_COLORS[0])
    highlight_color = theme.get("highlight", accent_color)
    stylized = _apply_gradient_overlay(image, accent_color)
    if pattern_type == "diagonal":
        stylized = _add_pattern_overlay(stylized, highlight_color)
    elif pattern_type == "stripe":
        stylized = _add_diagonal_stripe(stylized, highlight_color)
    else:
        stylized = _add_pattern_overlay(stylized, accent_color)
    glow = Image.new('RGBA', stylized.size, (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    glow_draw.ellipse(
        (THUMBNAIL_WIDTH - 500, -100, THUMBNAIL_WIDTH + 100, 400),
        fill=accent_color + (120,)
    )
    stylized = Image.alpha_composite(stylized.convert('RGBA'), glow).convert('RGB')
    return stylized


def _apply_layout_decorations(
    image: Image.Image,
    layout: Dict,
    theme: Dict[str, Tuple[int, int, int]]
) -> Image.Image:
    draw = ImageDraw.Draw(image)
    accent = theme.get("accent", (255, 255, 255))
    highlight = theme.get("highlight", accent)

    if layout.get("badge_stack"):
        stack_width = 90
        stack_height = 260
        x = 40
        y = 140
        draw.rounded_rectangle(
            [(x, y), (x + stack_width, y + stack_height)],
            radius=30,
            fill=theme.get("shadow", (30, 30, 30)),
            outline=None
        )
        draw.rectangle(
            [(x, y), (x + stack_width, y + stack_height // 2)],
            fill=accent
        )
        badge_font = get_japanese_font(28)
        draw.text(
            (x + 12, y + 12),
            "POINT",
            font=badge_font,
            fill=(20, 20, 20)
        )

    if layout.get("before_after_labels"):
        labels = layout["before_after_labels"]
        center = THUMBNAIL_WIDTH // 2
        draw.line(
            [(center, 100), (center, THUMBNAIL_HEIGHT - 100)],
            fill=accent,
            width=10
        )
        label_font = get_japanese_font(34)
        before_box = (center - 170, 90, center - 20, 150)
        after_box = (center + 20, THUMBNAIL_HEIGHT - 150, center + 170, THUMBNAIL_HEIGHT - 90)
        draw.rounded_rectangle(before_box, radius=30, fill=accent)
        draw.rounded_rectangle(after_box, radius=30, fill=highlight)
        draw.text(
            (before_box[0] + 20, before_box[1] + 10),
            labels[0],
            font=label_font,
            fill=(0, 0, 0)
        )
        draw.text(
            (after_box[0] + 20, after_box[1] + 10),
            labels[1],
            font=label_font,
            fill=(0, 0, 0)
        )

    return image


def _stabilize_text_background(
    image: Image.Image,
    rect: Tuple[int, int, int, int],
    theme: Dict[str, Tuple[int, int, int]]
) -> Image.Image:
    x1, y1, x2, y2 = rect
    x1 = max(0, x1)
    y1 = max(0, y1)
    x2 = min(image.width, x2)
    y2 = min(image.height, y2)
    if x2 <= x1 or y2 <= y1:
        return image
    shadow = theme.get("shadow", (8, 12, 22))
    fill_color = (240, 240, 245)
    solid = Image.new('RGB', (x2 - x1, y2 - y1), fill_color)
    image.paste(solid, (x1, y1))
    return image


def _boost_title_highlight(
    image: Image.Image,
    rect: Tuple[int, int, int, int]
) -> Image.Image:
    x1, y1, x2, y2 = rect
    x1 = max(0, x1)
    y1 = max(0, y1)
    x2 = min(image.width, x2)
    y2 = min(image.height, y2)
    if x2 <= x1 or y2 <= y1:
        return image
    region = image.crop((x1, y1, x2, y2)).convert("L")
    boost = Image.new('RGB', (x2 - x1, y2 - y1), (255, 255, 255))
    alpha = Image.new('L', (x2 - x1, y2 - y1), 220)
    image.paste(boost, (x1, y1), alpha)
    return image


def _apply_three_bar_layout(
    image: Image.Image,
    theme: Dict[str, Tuple[int, int, int]]
) -> Image.Image:
    """
    Apply three horizontal bars layout (top category, middle title, bottom subtitle)
    Similar to the reference image with colored bars
    """
    overlay = Image.new('RGBA', image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Get theme colors
    accent = theme.get("accent", (100, 200, 200))
    highlight = theme.get("highlight", accent)

    # Calculate darker and lighter versions
    dark_color = tuple(max(0, int(c * 0.5)) for c in accent)  # 50% darker
    light_color = tuple(min(255, int(c * 1.2)) for c in accent)  # 20% lighter

    # Bar dimensions
    bar_height = 100
    top_bar_y = 150
    middle_bar_y = 280
    bottom_bar_y = 420

    # Draw top bar (light color)
    draw.rounded_rectangle(
        [(0, top_bar_y), (THUMBNAIL_WIDTH, top_bar_y + bar_height)],
        radius=0,
        fill=light_color + (200,)
    )

    # Draw middle bar (dark color)
    draw.rounded_rectangle(
        [(0, middle_bar_y), (THUMBNAIL_WIDTH, middle_bar_y + bar_height + 20)],
        radius=0,
        fill=dark_color + (220,)
    )

    # Draw bottom bar (light color)
    draw.rounded_rectangle(
        [(0, bottom_bar_y), (THUMBNAIL_WIDTH, bottom_bar_y + bar_height)],
        radius=0,
        fill=light_color + (200,)
    )

    return Image.alpha_composite(image.convert('RGBA'), overlay).convert('RGB')


import re

def draw_text_line_with_highlight(
    draw: ImageDraw.Draw,
    xy: Tuple[int, int],
    text: str,
    base_font: ImageFont.FreeTypeFont,
    text_color: Tuple[int, int, int],
    highlight_color: Tuple[int, int, int],
    shadow_offset: int = 4
):
    """Draw a line of text with numbers highlighted"""
    # Regex to capture numbers with units (including Japanese numerals)
    # Matches: 100, 100%, 100万, 1.5倍, etc.
    pattern = r'(\d+(?:[,.]\d+)?(?:%|億|万|千|円|ドル|人|倍|年|月|日|代)?)'
    
    parts = re.split(pattern, text)
    x, y = xy
    
    for part in parts:
        if not part:
            continue
            
        # Check if part is a number match
        is_number = re.match(pattern, part)
        
        color = highlight_color if is_number else text_color
        
        # Draw shadow (stronger for numbers)
        s_off = shadow_offset + 2 if is_number else shadow_offset
        for off in range(1, s_off + 1):
             draw.text((x + off, y + off), part, font=base_font, fill=SHADOW_COLOR)
             
        # Draw text
        draw.text((x, y), part, font=base_font, fill=color)
        
        # Advance X
        bbox = base_font.getbbox(part)
        w = bbox[2] - bbox[0]
        x += w


def create_thumbnail(
    background_image_path: Path,
    thumbnail_text: str = "", # Keep for compatibility, but won't be drawn
    subtitle_text: str = "", # Keep for compatibility, but won't be drawn
    output_path: Path = None,
    accent_color_index: int = 0, # Keep for compatibility, but won't be used
    topic_badge_text: str = "", # Keep for compatibility, but won't be drawn
    badge_icon_path: Optional[Path] = None, # Keep for compatibility, but won't be used
    layout_name: Optional[str] = None, # Keep for compatibility, but won't be used
    image_prompt: Optional[str] = None,
    emotion: Optional[str] = None # Keep for compatibility, but won't be used
) -> Path:
    """
    Create a YouTube thumbnail. If image_prompt is provided and USE_NANO_BANANA_PRO is true,
    it generates the background using NanoBanana. Otherwise, it loads from background_image_path.
    No additional processing or text overlay is performed on the image.

    Args:
        background_image_path: Path to background image (used if not generating with NanoBanana).
        thumbnail_text: Main text (ignored if image_prompt is used for NanoBanana).
        subtitle_text: Optional subtitle text (ignored if image_prompt is used for NanoBanana).
        output_path: Output path for thumbnail.
        accent_color_index: Index of accent color (ignored).
        topic_badge_text: Optional badge text for category (ignored).
        badge_icon_path: Optional icon displayed near badge (ignored).
        layout_name: Optional layout preset name (ignored).
        image_prompt: Prompt for NanoBanana to generate the background image and title.
        emotion: Explicit emotion (ignored).

    Returns:
        Path to generated thumbnail
    """
    if output_path is None:
        output_path = background_image_path.parent / "thumbnail.jpg"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    bg: Image.Image
    if USE_NANO_BANANA_PRO and image_prompt:
        # Generate image using NanoBanana
        print(f"Generating background image with NanoBanana Pro using prompt: {image_prompt}")
        generated_image_path = generate_image(image_prompt, output_path)
        if not generated_image_path or not generated_image_path.exists():
            print(f"NanoBanana Pro failed to generate image, falling back to existing background: {background_image_path}")
            bg = Image.open(background_image_path).convert('RGB')
        else:
            bg = Image.open(generated_image_path).convert('RGB')
    else:
        # Load from provided path
        bg = Image.open(background_image_path).convert('RGB')

    # Resize to thumbnail dimensions (YouTube recommended: 1280x720)
    bg = bg.resize((THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT), Image.Resampling.LANCZOS)

    # Save thumbnail
    bg.save(output_path, 'JPEG', quality=90, optimize=True) # Use a fixed quality since no post-processing

    print(f"Thumbnail created: {output_path}")

    return output_path


def create_multiple_thumbnail_variants(
    background_image_path: Path,
    thumbnail_text: str,
    subtitle_text: str = "",
    output_dir: Path = None,
    count: int = 3
) -> list:
    """
    Create multiple thumbnail variants with different accent colors

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
    from nano_banana_client import generate_image

    # Generate a test background with text using NanoBanana
    test_dir = Path("test_output")
    test_dir.mkdir(exist_ok=True)

    test_image_prompt = "YouTube thumbnail: Japanese man shocked by 'Economic News Explained', with text '経済ニュース解説' on it, bright, clear, dynamic. No additional text overlays, use a professional font."
    
    # Create thumbnail using the image_prompt for NanoBanana generation
    create_thumbnail(
        background_image_path=test_dir / "fallback_bg.png", # Fallback image in case NanoBanana fails
        output_path=test_dir / "test_thumbnail_nanobanana.jpg",
        image_prompt=test_image_prompt,
        # Other arguments are ignored now
    )

    print("Test complete!")
