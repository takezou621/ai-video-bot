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

# Character display settings
CHARACTER_HEIGHT = 320
CHARACTER_SPACING = 24
CHARACTER_MARGIN_LEFT = 60
CHARACTER_MARGIN_BOTTOM = 30
CHARACTER_SHADOW_OFFSET = (18, 18)
CHARACTER_SHADOW_BLUR = 18
CHARACTER_SHADOW_COLOR = (0, 0, 0, 160)

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


def _load_character_images(
    target_height: int = CHARACTER_HEIGHT,
    emotion: str = "default"
) -> Optional[Tuple[Image.Image, Image.Image]]:
    """Load and resize character images if available"""
    male_path, female_path = CHARACTER_VARIANTS.get(
        emotion,
        CHARACTER_VARIANTS["default"]
    )
    male_file = ASSETS_DIR / male_path
    female_file = ASSETS_DIR / female_path
    if not male_file.exists() or not female_file.exists():
        male_file = MALE_CHARACTER_PATH
        female_file = FEMALE_CHARACTER_PATH
        if not male_file.exists() or not female_file.exists():
            return None

    try:
        male_char = Image.open(male_file).convert('RGBA')
        female_char = Image.open(female_file).convert('RGBA')
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


def add_characters_to_thumbnail(
    thumbnail: Image.Image,
    add_characters: bool = True,
    characters: Optional[Tuple[Image.Image, Image.Image]] = None,
    layout: Optional[Dict] = None
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
    anchor = (layout or {}).get("character_anchor", "right")
    char_offset_y = (layout or {}).get("character_vertical_offset", 0)

    cluster_width = male_char.width + female_char.width - 80 + CHARACTER_SPACING
    cluster_height = CHARACTER_HEIGHT + 140
    if anchor == "right":
        cluster_x = THUMBNAIL_WIDTH - cluster_width - max(40, CHARACTER_MARGIN_LEFT)
    else:
        cluster_x = max(0, CHARACTER_MARGIN_LEFT - 40)
    cluster_y = THUMBNAIL_HEIGHT - CHARACTER_MARGIN_BOTTOM - cluster_height + char_offset_y

    bubble = Image.new('RGBA', (cluster_width + 120, cluster_height), (0, 0, 0, 0))
    bubble_draw = ImageDraw.Draw(bubble)
    bubble_draw.rounded_rectangle(
        [(0, 0), (bubble.width, bubble.height)],
        radius=60,
        fill=(255, 255, 255, 215)
    )
    bubble_draw.ellipse(
        (20, bubble.height - 80, bubble.width - 20, bubble.height - 10),
        fill=(0, 0, 0, 40)
    )

    thumbnail_rgba = thumbnail.convert('RGBA')
    thumbnail_rgba.alpha_composite(bubble, dest=(cluster_x, cluster_y))

    if anchor == "right":
        male_x = THUMBNAIL_WIDTH - CHARACTER_MARGIN_LEFT - male_char.width
        male_y = THUMBNAIL_HEIGHT - CHARACTER_MARGIN_BOTTOM - male_char.height + char_offset_y
        female_x = male_x - female_char.width + CHARACTER_SPACING
        female_y = male_y - 25
    else:
        male_x = CHARACTER_MARGIN_LEFT + 20
        male_y = THUMBNAIL_HEIGHT - CHARACTER_MARGIN_BOTTOM - male_char.height + char_offset_y
        female_x = male_x + male_char.width - 60
        female_y = male_y - 30

    thumbnail_rgba = _paste_with_shadow(thumbnail_rgba, male_char, (male_x, male_y))
    thumbnail_rgba = _paste_with_shadow(thumbnail_rgba, female_char, (female_x, female_y))

    # Convert back to RGB
    return thumbnail_rgba.convert('RGB')


def create_thumbnail(
    background_image_path: Path,
    thumbnail_text: str,
    subtitle_text: str = "",
    output_path: Path = None,
    accent_color_index: int = 0,
    add_characters: bool = True,
    topic_badge_text: str = "",
    badge_icon_path: Optional[Path] = None,
    layout_name: Optional[str] = None,
    image_prompt: Optional[str] = None
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
        topic_badge_text: Optional badge text for category
        badge_icon_path: Optional icon displayed near badge
        layout_name: Optional layout preset name (e.g., "three_bar_layout")
        image_prompt: Original prompt used for background generation (for AI text rendering)

    Returns:
        Path to generated thumbnail
    """
    if output_path is None:
        output_path = background_image_path.parent / "thumbnail.jpg"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # DIRECT AI GENERATION MODE
    # If using Nano Banana Pro and a prompt is provided, let the AI generate the text directly.
    # This skips all manual PIL composition (characters, text overlays, etc.)
    if USE_NANO_BANANA_PRO and image_prompt:
        print(f"🎨 Using Nano Banana Pro for full thumbnail generation (including text)...")
        
        # Sanitize text for prompt
        clean_title = thumbnail_text.replace("\n", " ")
        clean_subtitle = subtitle_text.replace("\n", " ")
        
        # Construct a prompt that instructs the model to render text
        full_prompt = (
            f"{image_prompt}. "
            f"Important: The image must clearly feature the Japanese text '{clean_title}' written in large, bold, elegant typography in the center or top area. "
            f"The style should be a high-quality YouTube thumbnail, eye-catching and vibrant. "
            f"Ensure the text is legible and integrated naturally into the composition."
        )
        if clean_subtitle:
            full_prompt += f" Also include smaller subtitle text: '{clean_subtitle}'."

        # Generate the image directly to output path
        result = generate_image(full_prompt, output_path)
        if result and result.exists():
            print(f"✅ AI-generated thumbnail created: {output_path}")
            return output_path
        else:
            print("⚠️ AI generation failed, falling back to standard composition.")

    # Standard Composition Logic (Fallback or if Nano Banana is disabled)
    sanitized_title = _craft_headline(thumbnail_text)
    sanitized_subtitle = _sanitize_text(subtitle_text, MAX_SUBTITLE_CHARS)
    emotion = _select_emotion(sanitized_title)
    characters = _load_character_images(emotion=emotion) if add_characters else None
    theme = _select_theme(topic_badge_text, accent_color_index)

    # Use specified layout or auto-select
    if layout_name:
        layout = _get_layout_by_name(layout_name)
        if not layout:
            print(f"Warning: Layout '{layout_name}' not found, using auto-selection")
            layout = _select_layout(sanitized_title, bool(characters))
    else:
        layout = _select_layout(sanitized_title, bool(characters))

    # Load and prepare background
    bg = Image.open(background_image_path).convert('RGB')

    # Resize to thumbnail dimensions
    bg = bg.resize((THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT), Image.Resampling.LANCZOS)

    # Apply slight blur and darken for better text readability
    bg = bg.filter(ImageFilter.GaussianBlur(radius=2))
    enhancer = ImageEnhance.Brightness(bg)
    bg = enhancer.enhance(0.6)  # Darken to 60%
    accent_color = theme.get("accent", ACCENT_COLORS[accent_color_index % len(ACCENT_COLORS)])

    # Apply pattern overlay (skip for three-bar layout)
    if not layout.get("three_bar_style"):
        bg = _apply_layout_patterns(bg, theme, layout.get("pattern", "standard"))

    # Apply three-bar layout if specified
    if layout.get("three_bar_style"):
        bg = _apply_three_bar_layout(bg, theme)

    # Create overlay for text (skip for three-bar layout)
    if not layout.get("three_bar_style"):
        overlay = Image.new('RGBA', bg.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        # Add colored accent bar at top
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
    if topic_badge_text:
        bg = _draw_topic_badge(
            bg,
            topic_badge_text,
            accent_color,
            badge_icon_path,
            badge_color=theme.get("badge")
        )
    bg = _apply_layout_decorations(bg, layout, theme)
    draw = ImageDraw.Draw(bg)

    # Get fonts
    title_font = get_japanese_font(TITLE_FONT_SIZE)
    subtitle_font = get_japanese_font(SUBTITLE_FONT_SIZE)

    # Calculate text positioning
    text_area = layout.get("text_area", {})
    text_start_x = text_area.get("x", 80)
    max_text_width = int(THUMBNAIL_WIDTH * text_area.get("width_ratio", 0.6))
    align_center = layout.get("text_align", "left") == "center"

    # Wrap text with typography constraints
    title_lines = wrap_text(
        sanitized_title,
        title_font,
        max_text_width,
        max_lines=MAX_TITLE_LINES
    )
    subtitle_lines = wrap_text(
        sanitized_subtitle,
        subtitle_font,
        max_text_width,
        max_lines=2
    ) if sanitized_subtitle else []

    title_line_height = layout.get("line_spacing", TITLE_FONT_SIZE + 10)
    subtitle_gap = layout.get("subtitle_gap", 24)
    subtitle_line_height = SUBTITLE_FONT_SIZE + 6
    subtitle_block = (subtitle_line_height * len(subtitle_lines)) + (subtitle_gap if subtitle_lines else 0)
    text_block_height = len(title_lines) * title_line_height + subtitle_block

    if text_area.get("vertical") == "center":
        start_y = max(120, (THUMBNAIL_HEIGHT - text_block_height) // 2)
    else:
        start_y = text_area.get("y", THUMBNAIL_HEIGHT - 350)

    # Create isolated text layer
    text_layer = Image.new('RGBA', bg.size, (0, 0, 0, 0))
    text_draw = ImageDraw.Draw(text_layer)

    # Optional backdrop for readability
    if layout.get("text_backdrop"):
        pad_x = 50
        pad_y = 40
        if align_center:
            center_x = THUMBNAIL_WIDTH // 2
            left = max(30, center_x - max_text_width // 2 - pad_x)
            right = min(THUMBNAIL_WIDTH - 30, center_x + max_text_width // 2 + pad_x)
        else:
            left = max(20, text_start_x - pad_x)
            right = min(THUMBNAIL_WIDTH - 20, text_start_x + max_text_width + pad_x)
        top = max(30, start_y - pad_y)
        bottom = min(THUMBNAIL_HEIGHT - 30, start_y + text_block_height + pad_y)
        bg = _stabilize_text_background(bg, (left, top, right, bottom), theme)
        backdrop = Image.new('RGBA', (right - left, bottom - top), (255, 255, 255, 255))
        text_layer.paste(backdrop, (left, top), backdrop)
        bg = _boost_title_highlight(bg, (left, top, right, bottom))

    # Draw main title
    current_y = start_y
    for line in title_lines:
        bbox = title_font.getbbox(line)
        text_width = bbox[2] - bbox[0]
        if align_center:
            x = (THUMBNAIL_WIDTH - text_width) // 2
        else:
            x = text_start_x

        add_text_with_shadow(
            text_draw, (x, current_y), line, title_font, TEXT_COLOR, shadow_offset=6
        )
        current_y += title_line_height

    # Draw subtitle if provided
    if subtitle_lines:
        current_y += subtitle_gap
        highlight_color = theme.get("highlight", accent_color)
        for line in subtitle_lines:
            bbox = subtitle_font.getbbox(line)
            text_width = bbox[2] - bbox[0]
            if align_center:
                x = (THUMBNAIL_WIDTH - text_width) // 2
            else:
                x = text_start_x

            add_text_with_shadow(
                text_draw, (x, current_y), line, subtitle_font, highlight_color, shadow_offset=4
            )
            current_y += subtitle_line_height

    # Composite text layer last to avoid overlap
    bg = Image.alpha_composite(bg.convert('RGBA'), text_layer).convert('RGB')
    draw = ImageDraw.Draw(bg)

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

    _evaluate_thumbnail_quality(title_lines, subtitle_lines, layout)

    # Add dialogue characters to layout-defined area
    if characters and add_characters:
        bg = add_characters_to_thumbnail(
            bg,
            add_characters=True,
            characters=characters,
            layout=layout
        )

    bg = bg.filter(ImageFilter.UnsharpMask(radius=1, percent=160, threshold=0))
    # Save thumbnail with YouTube size limit (2MB)
    # Start with quality=85, then reduce if needed
    quality = 85
    while quality >= 60:
        bg.save(output_path, 'JPEG', quality=quality, optimize=True)
        file_size = output_path.stat().st_size
        # YouTube limit is 2MB
        if file_size <= 2 * 1024 * 1024:
            print(f"Thumbnail created: {output_path} ({file_size / 1024:.0f}KB, quality={quality})")
            break
        quality -= 5
    else:
        # If still too large, resize and save again
        print(f"⚠️  Thumbnail too large, resizing...")
        bg = bg.resize((1280, 720), Image.Resampling.LANCZOS)
        bg.save(output_path, 'JPEG', quality=80, optimize=True)
        file_size = output_path.stat().st_size
        print(f"Thumbnail created (resized): {output_path} ({file_size / 1024:.0f}KB)")

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
