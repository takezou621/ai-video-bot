"""
Template-based Thumbnail Generator
Generates YouTube thumbnails using predefined color templates
Follows the GPTs thumbnail generation workflow
"""
import os
import re
from pathlib import Path
from typing import Dict, Tuple, Optional
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import anthropic
from dotenv import load_dotenv

load_dotenv()

# Template settings
TEMPLATE_DIR = Path(__file__).parent / "assets" / "templates"
TEMPLATE_WIDTH = 1280
TEMPLATE_HEIGHT = 720

# Available color codes
AVAILABLE_COLORS = ['74AA9C', 'CC9B7A', '669AFF', '8C52FF']

# Text bounding boxes (from requirements)
ABOVE_TEXT_BBOX = (171.5, 24, 731.4, 100.8)  # (x, y, width, height)
CENTER_TEXT_BBOX = (55, 200, 804, 302)
BELOW_TEXT_BBOX = (55.5, 578.4, 804.2, 100.8)

# Font settings
FONT_PATHS = [
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
    "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc",
]

MAX_FONT_SIZE = 100
MIN_FONT_SIZE = 10
TEXT_COLOR = "white"
SHADOW_COLOR = "black"
SHADOW_OFFSET = 2
SHADOW_BLUR = 5

# Character settings
ASSETS_DIR = Path(__file__).parent / "assets" / "characters"
CHARACTER_HEIGHT = 280  # Slightly smaller for template thumbnails
CHARACTER_SPACING = 20
CHARACTER_MARGIN_RIGHT = 60
CHARACTER_MARGIN_BOTTOM = 40


def get_bold_japanese_font(size: int) -> ImageFont.FreeTypeFont:
    """Get a bold Japanese font"""
    for path in FONT_PATHS:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except:
                continue
    # Fallback
    return ImageFont.load_default()


def make_white_transparent(image: Image.Image, threshold: int = 240) -> Image.Image:
    """
    Convert white/near-white background to transparent

    Args:
        image: Input image (RGB or RGBA)
        threshold: RGB value threshold for considering a pixel as white (default: 240)

    Returns:
        Image with transparent background (RGBA)
    """
    # Convert to RGBA if needed
    if image.mode != 'RGBA':
        image = image.convert('RGBA')

    # Get pixel data
    data = image.getdata()
    new_data = []

    for item in data:
        # Check if pixel is close to white
        if item[0] > threshold and item[1] > threshold and item[2] > threshold:
            # Make it transparent
            new_data.append((255, 255, 255, 0))
        else:
            # Keep original pixel
            new_data.append(item)

    # Update image data
    image.putdata(new_data)
    return image


def load_and_prepare_characters() -> Optional[Tuple[Image.Image, Image.Image]]:
    """
    Load and prepare character images with transparent backgrounds

    Returns:
        Tuple of (male_character, female_character) or None if not found
    """
    male_path = ASSETS_DIR / "male_host.png"
    female_path = ASSETS_DIR / "female_host.png"

    if not male_path.exists() or not female_path.exists():
        return None

    try:
        # Load images
        male_img = Image.open(male_path).convert('RGB')
        female_img = Image.open(female_path).convert('RGB')

        # Make backgrounds transparent
        male_img = make_white_transparent(male_img)
        female_img = make_white_transparent(female_img)

        # Resize to target height
        def resize_to_height(img: Image.Image, target_height: int) -> Image.Image:
            aspect_ratio = img.width / img.height
            new_width = int(target_height * aspect_ratio)
            return img.resize((new_width, target_height), Image.Resampling.LANCZOS)

        male_img = resize_to_height(male_img, CHARACTER_HEIGHT)
        female_img = resize_to_height(female_img, CHARACTER_HEIGHT)

        return male_img, female_img

    except Exception as e:
        print(f"Error loading character images: {e}")
        return None


def add_characters_to_template_thumbnail(
    thumbnail: Image.Image,
    characters: Tuple[Image.Image, Image.Image]
) -> Image.Image:
    """
    Add two character images to thumbnail (right side, transparent background)

    Args:
        thumbnail: Base thumbnail image (RGB)
        characters: Tuple of (male_character, female_character) images (RGBA)

    Returns:
        Thumbnail with characters composited
    """
    male_char, female_char = characters

    # Convert thumbnail to RGBA for compositing
    if thumbnail.mode != 'RGBA':
        thumbnail = thumbnail.convert('RGBA')

    # Calculate positions (right-aligned, bottom)
    # Both characters at same Y position (aligned at bottom)
    base_y = TEMPLATE_HEIGHT - CHARACTER_MARGIN_BOTTOM - CHARACTER_HEIGHT

    # Male character on the right
    male_x = TEMPLATE_WIDTH - CHARACTER_MARGIN_RIGHT - male_char.width
    male_y = base_y

    # Female character to the left of male (same Y position)
    female_x = male_x - female_char.width + CHARACTER_SPACING
    female_y = base_y  # Same Y as male

    # Paste characters with alpha channel
    thumbnail.paste(male_char, (male_x, male_y), male_char)
    thumbnail.paste(female_char, (female_x, female_y), female_char)

    return thumbnail


def generate_thumbnail_texts(title: str) -> Dict[str, str]:
    """
    Generate AboveText, CenterOfText, and BelowText from title using Claude API

    Args:
        title: YouTube video title

    Returns:
        Dictionary with 'above', 'center', 'below' keys
    """
    api_key = os.getenv('CLAUDE_API_KEY')
    if not api_key:
        print("Warning: CLAUDE_API_KEY not set, using fallback text generation")
        return _generate_texts_fallback(title)

    try:
        client = anthropic.Anthropic(api_key=api_key)

        prompt = f"""以下のYouTube動画タイトルから、サムネイル用のテキストを生成してください。

タイトル: {title}

以下の制約条件に従ってテキストを生成してください:

## AboveText（上部テキスト）
- タイトルからターゲット層や記事のレベルを推測する
- 10文字ほどで作成
- 例: "GPTs作成入門編"、"プログラミング未経験でもOK"

## CenterOfText（中央テキスト）
- タイトルから最も大切な部分を選択
- 18文字以内で作成
- 意味を崩さない箇所で改行を作るために「/n」を追加
- 例: "たった1分で/n自分用のGPTsを作成"、"YouTubeサムネを/n自動で一発作成"

## BelowText（下部テキスト）
- CenterOfTextで含められなかった部分を選択
- 6文字〜10文字以内で作成
- 例: "EasyGPTsMaker"、"GPTsの作り方"

重要: AboveText、CenterOfText、BelowTextは意味合いとして同じ文章を選択しないこと

以下のJSON形式で出力してください:
{{
  "above": "上部テキスト",
  "center": "中央テキスト/n改行あり",
  "below": "下部テキスト"
}}"""

        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            temperature=0.7,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = message.content[0].text

        # Extract JSON from response
        import json
        json_match = re.search(r'\{[^}]+\}', response_text, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
            # Replace /n with actual newlines
            result['center'] = result['center'].replace('/n', '\n')
            print(f"✅ Generated texts via Claude:")
            print(f"   Above: {result['above']}")
            print(f"   Center: {result['center'].replace(chr(10), '/n')}")
            print(f"   Below: {result['below']}")
            return result
        else:
            print("Warning: Could not parse Claude response, using fallback")
            return _generate_texts_fallback(title)

    except Exception as e:
        print(f"Warning: Claude API failed ({e}), using fallback")
        return _generate_texts_fallback(title)


def _generate_texts_fallback(title: str) -> Dict[str, str]:
    """Fallback text generation when Claude API is unavailable"""
    # Simple heuristic-based generation
    parts = title.split('！')
    if len(parts) >= 2:
        above = "必見"
        center = parts[0][:18].replace('！', '\n')
        below = parts[1][:10] if len(parts) > 1 else "解説"
    else:
        above = "注目"
        center = title[:18]
        below = "詳しく解説"

    # Add newline to center if needed
    if '\n' not in center and len(center) > 9:
        mid = len(center) // 2
        center = center[:mid] + '\n' + center[mid:]

    return {'above': above, 'center': center, 'below': below}


def draw_text_with_auto_size(
    draw: ImageDraw.Draw,
    text: str,
    bbox: Tuple[float, float, float, float],
    font_path_func,
    text_color: str,
    shadow_color: str,
    shadow_offset: int = SHADOW_OFFSET
):
    """
    Draw text with automatic font size adjustment to fit bounding box

    Args:
        draw: ImageDraw object
        text: Text to draw (may contain newlines)
        bbox: (x, y, width, height) bounding box
        font_path_func: Function to get font at given size
        text_color: Text color
        shadow_color: Shadow color
        shadow_offset: Shadow offset in pixels
    """
    x_start, y_start, width, height = bbox
    font_size = MAX_FONT_SIZE

    # Find optimal font size
    while font_size > MIN_FONT_SIZE:
        font = font_path_func(font_size)
        lines = text.split('\n')

        # Calculate total text dimensions
        line_heights = []
        max_line_width = 0

        for line in lines:
            bbox_result = font.getbbox(line)
            line_width = bbox_result[2] - bbox_result[0]
            line_height = bbox_result[3] - bbox_result[1]
            line_heights.append(line_height)
            max_line_width = max(max_line_width, line_width)

        # Add line spacing (20% of font size)
        total_text_height = sum(line_heights) + (len(lines) - 1) * font_size * 0.2

        if max_line_width <= width and total_text_height <= height:
            break
        font_size -= 1

    # Draw text centered in bounding box
    current_y = y_start + (height - total_text_height) / 2

    for i, line in enumerate(lines):
        bbox_result = font.getbbox(line)
        text_width = bbox_result[2] - bbox_result[0]
        text_x = x_start + (width - text_width) / 2
        text_y = current_y

        # Draw shadow
        shadow_position = (text_x + shadow_offset, text_y + shadow_offset)
        draw.text(shadow_position, line, font=font, fill=shadow_color)

        # Draw text
        draw.text((text_x, text_y), line, font=font, fill=text_color)

        current_y += line_heights[i] + font_size * 0.2


def create_template_thumbnail(
    title: str,
    color_code: str = '74AA9C',
    output_path: Optional[Path] = None,
    custom_texts: Optional[Dict[str, str]] = None,
    add_characters: bool = True
) -> Path:
    """
    Create a YouTube thumbnail using template-based approach

    Args:
        title: Video title (used to generate texts if custom_texts not provided)
        color_code: Color code for template selection (74AA9C, CC9B7A, 669AFF, 8C52FF)
        output_path: Output path for thumbnail
        custom_texts: Optional dict with 'above', 'center', 'below' keys
        add_characters: Add Ghibli-style dialogue characters (default: True)

    Returns:
        Path to generated thumbnail
    """
    # Validate color code
    if color_code not in AVAILABLE_COLORS:
        print(f"Warning: Invalid color code '{color_code}', defaulting to '74AA9C'")
        color_code = '74AA9C'

    # Generate or use custom texts
    if custom_texts:
        texts = custom_texts
        print(f"Using custom texts:")
        print(f"   Above: {texts['above']}")
        print(f"   Center: {texts['center'].replace(chr(10), '/n')}")
        print(f"   Below: {texts['below']}")
    else:
        texts = generate_thumbnail_texts(title)

    # Load template image
    template_path = TEMPLATE_DIR / f"thumbnail_template_color({color_code}).png"
    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")

    image = Image.open(template_path).convert("RGBA")
    print(f"✅ Loaded template: {template_path.name}")

    # Create shadow layer
    shadow_layer = Image.new('RGBA', image.size, (0, 0, 0, 0))
    draw_shadow = ImageDraw.Draw(shadow_layer)

    # Create text layer
    text_layer = Image.new('RGBA', image.size, (0, 0, 0, 0))
    draw_text_layer = ImageDraw.Draw(text_layer)

    # Draw each text with shadow
    draw_text_with_auto_size(
        draw_shadow, texts['above'], ABOVE_TEXT_BBOX,
        get_bold_japanese_font, TEXT_COLOR, SHADOW_COLOR
    )
    draw_text_with_auto_size(
        draw_shadow, texts['center'], CENTER_TEXT_BBOX,
        get_bold_japanese_font, TEXT_COLOR, SHADOW_COLOR
    )
    draw_text_with_auto_size(
        draw_shadow, texts['below'], BELOW_TEXT_BBOX,
        get_bold_japanese_font, TEXT_COLOR, SHADOW_COLOR
    )

    # Blur shadow
    blurred_shadow = shadow_layer.filter(ImageFilter.GaussianBlur(SHADOW_BLUR))

    # Composite shadow onto image
    image_with_shadow = Image.alpha_composite(image, blurred_shadow)

    # Draw actual text
    draw_text_with_auto_size(
        draw_text_layer, texts['above'], ABOVE_TEXT_BBOX,
        get_bold_japanese_font, TEXT_COLOR, SHADOW_COLOR
    )
    draw_text_with_auto_size(
        draw_text_layer, texts['center'], CENTER_TEXT_BBOX,
        get_bold_japanese_font, TEXT_COLOR, SHADOW_COLOR
    )
    draw_text_with_auto_size(
        draw_text_layer, texts['below'], BELOW_TEXT_BBOX,
        get_bold_japanese_font, TEXT_COLOR, SHADOW_COLOR
    )

    # Composite text onto image
    final_image = Image.alpha_composite(image_with_shadow, text_layer)

    # Add characters if requested
    if add_characters:
        characters = load_and_prepare_characters()
        if characters:
            final_image = add_characters_to_template_thumbnail(final_image, characters)
            print("✅ Two characters added to thumbnail (transparent background)")
        else:
            print("⚠️  Character images not found, skipping")

    # Save output
    if output_path is None:
        output_path = Path("output") / "template_thumbnail.png"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    final_image.convert("RGB").save(output_path, "PNG", quality=95)
    print(f"✅ Thumbnail saved: {output_path}")

    return output_path


if __name__ == "__main__":
    # Test with examples from requirements
    test_cases = [
        {
            "title": "1分で自分専用GPTsを作成！忙しいあなたに贈る『EasyGPTsMaker』活用術",
            "color": "74AA9C"
        },
        {
            "title": "プログラミング未経験でもできるYouTubeのサムネイルを一発で自動作成するGPTsの作り方",
            "color": "669AFF"
        },
        {
            "title": "日本のキャッシュレス革命！",
            "color": "CC9B7A"
        }
    ]

    print("Template Thumbnail Generator Test")
    print("=" * 60)

    output_dir = Path("test_output")
    output_dir.mkdir(exist_ok=True)

    for i, test in enumerate(test_cases, 1):
        print(f"\n[Test {i}/{len(test_cases)}]")
        print(f"Title: {test['title']}")
        print(f"Color: {test['color']}")

        output_path = output_dir / f"template_thumbnail_{i}.png"
        create_template_thumbnail(
            title=test['title'],
            color_code=test['color'],
            output_path=output_path
        )

    print("\n" + "=" * 60)
    print(f"✅ Test complete! Check: {output_dir}")
