"""
Thumbnail Prompt Generator - Creates optimized prompts for high CTR thumbnails

Analyzes news title and content to generate visually impactful thumbnail prompts
based on YouTube best practices research.
"""

import re
from typing import Dict, Optional, List, Any

# Visual mapping for common entities to ensure concrete, recognizable imagery
ENTITY_VISUAL_MAP = {
    "OpenAI": "OpenAI logo illustration, futuristic green glowing flower, anime style cyber interface",
    "ChatGPT": "ChatGPT logo icon, cute robot avatar illustration, manga style speech bubble",
    "Google": "Google G logo illustration, colorful data streams (blue red yellow green), anime cyber space",
    "Apple": "Apple logo illustration, clean white minimalist design, stylish vector art",
    "Microsoft": "Microsoft window logo illustration, blue crystal structure, bright digital art",
    "NVIDIA": "NVIDIA eye logo illustration, neon green circuit patterns, cyberpunk anime style",
    "Amazon": "Amazon smile logo illustration, cardboard box texture art, orange accents",
    "Tesla": "Tesla T logo illustration, sleek futuristic car silhouette, speed lines",
    "Elon Musk": "Elon Musk anime character illustration, confident expression, space rocket background",
    "Sam Altman": "Sam Altman anime character illustration, silicon valley background",
    "Disney": "Disney castle illustration (Kingdom Hearts style), magical sparkles, Mickey Mouse shape clouds, vibrant sunset",
    "Netflix": "Netflix red N logo illustration, cinematic popcorn art, bright red ribbon",
    "SoftBank": "SoftBank silver lines logo, anime style business setting",
    "Toyota": "Toyota logo illustration, futuristic car concept art, blue sky background",
    "Sony": "Sony logo, PlayStation controller buttons pop art",
    "Nintendo": "Nintendo red cap illustration, pixel art game world, bright primary colors",
}

def extract_numbers_from_text(text: str) -> List[str]:
    """Extract numbers from text (including Japanese numerals and percentages)"""
    # Extract Arabic numerals with units
    numbers = re.findall(r'\d+(?:[,.]\d+)?(?:%|億|万|千|円|ドル|人|倍|年|月|日)?', text)
    # Japanese numeric patterns
    jp_numbers = re.findall(r'[一二三四五六七八九十百千万億兆]+(?:円|ドル|人|倍|年|月|日)?', text)
    return numbers + jp_numbers


def extract_keywords(title: str) -> List[str]:
    """Extract important keywords from title for visual representation"""
    # Common impactful keywords for tech/AI news
    impact_keywords = [
        'AI', 'ChatGPT', 'OpenAI', 'Google', 'Apple', 'Microsoft', 'Amazon',
        'ディズニー', 'テスラ', 'イーロン・マスク', 'NVIDIA',
        '衝撃', '驚き', '激変', '革命', '崩壊', '暴露', '発表', '実現',
        '禁止', '規制', '投資', '買収', '提携', '独占', '暴落', '急騰'
    ]

    found = []
    for keyword in impact_keywords:
        if keyword in title:
            found.append(keyword)

    return found[:3]  # Top 3 keywords


def determine_visual_concept(title: str, keywords: List[str], named_entities: List[Dict[str, Any]]) -> str:
    """
    Determine the visual concept based on title, keywords, and SPECIFIC ENTITIES.
    Prioritizes concrete entity visuals over abstract concepts.
    """
    
    # 1. Identify primary visual subjects from entities
    visual_elements = []
    
    # Check passed named entities first
    for entity in named_entities:
        label = entity.get("label", "")
        # Fuzzy match against our map
        for key, visual in ENTITY_VISUAL_MAP.items():
            if key.lower() in label.lower() or label.lower() in key.lower():
                if visual not in visual_elements:
                    visual_elements.append(visual)
    
    # Also check title keywords if no entities found yet
    if not visual_elements:
        for key, visual in ENTITY_VISUAL_MAP.items():
            if key in title or key.lower() in title.lower():
                if visual not in visual_elements:
                    visual_elements.append(visual)

    # 2. Determine Composition Type
    composition = "centered single subject illustration"
    
    # "Vs" or "Partnership" scenario (2+ distinct entities)
    if len(visual_elements) >= 2:
        if any(w in title for w in ['提携', '買収', '投資', 'vs', '対決', '競争']):
            # Removed handshake to avoid grey skin / creepy hands
            composition = "anime style split screen composition, bright lightning bolt or magic sparkles connecting the two sides (VS style)"
        else:
            composition = "montage of connected icons, dynamic anime composition"
            
    # 3. Determine Mood/Atmosphere (Japanese Pop Culture Style)
    if any(word in title for word in ['衝撃', '驚き', '激変', '崩壊', '危険']):
        mood = "Anime style shock effect, purple and jagged impact lines, manga background speed lines, high energy"
    elif any(word in title for word in ['革命', '未来', '進化', '実現', '成功']):
        mood = "Sparkling anime sky background (Makoto Shinkai style), lens flare, bright blue and white, hopeful atmosphere"
    elif any(word in title for word in ['禁止', '規制', '問題', '裁判']):
        mood = "Pop art warning style, yellow and black stripes, bold graphic design, clear and readable"
    elif any(word in title for word in ['投資', '買収', 'お金', '利益']):
        mood = "Golden coins illustration, bright yellow sunburst background, Weekly Shonen Jump style victory vibe"
    else:
        mood = "Bright colorful anime background, pastel colors, cheerful and welcoming (Kawaii style)"

    # 4. Construct Final Visual Description
    if visual_elements:
        # We have concrete subjects
        subjects_str = " AND ".join(visual_elements[:2]) # Max 2 main elements to avoid clutter
        base_concept = f"{composition}. Featuring {subjects_str}. Atmosphere: {mood}"
    else:
        # Fallback to abstract concepts if no entities recognized
        if any(keyword in title for keyword in ['AI', '人工知能']):
            base_concept = f"Cute AI robot illustration, futuristic digital city background (anime style). {mood}"
        else:
            base_concept = f"Bright broadcast news studio illustration, anime style. {mood}"

    return base_concept


def generate_thumbnail_prompt(
    title: str,
    topic_category: str = "technology",
    thumbnail_text: Optional[str] = None,
    named_entities: List[Dict[str, Any]] = None,
    include_title_in_image: bool = True,
    topic_badge_text: Optional[str] = None
) -> Dict[str, any]:
    """
    Generate optimized thumbnail prompt for high CTR

    Args:
        title: News title
        topic_category: Category
        thumbnail_text: Optional custom text
        named_entities: List of identified entities (companies, people)
        include_title_in_image: Whether to include title text in the generated image
        topic_badge_text: Category badge text (e.g., "AI_NEWS")

    Returns:
        Dictionary with prompt and metadata
    """
    if named_entities is None:
        named_entities = []

    # Extract key elements
    numbers = extract_numbers_from_text(title)
    keywords = extract_keywords(title)

    # Determine emotion
    if any(word in title for word in ['衝撃', '驚き', '激変', 'やばい']):
        emotion = "shock"
    elif any(word in title for word in ['禁止', '規制', '危険', '崩壊']):
        emotion = "fear"
    elif any(word in title for word in ['革命', '実現', '成功', '最強']):
        emotion = "joy"
    else:
        emotion = "default"

    # Generate visual concept with entity awareness
    visual_concept = determine_visual_concept(title, keywords, named_entities)

    # Optimize thumbnail text
    if thumbnail_text is None:
        # Extract meaningful text from title
        # Priority: Entity names + numbers + action words

        # Get entity names (companies, people)
        entity_names = []
        for entity in named_entities[:2]:  # Max 2 entities
            label = entity.get("label", "")
            # Get short form (e.g., "OpenAI" not "OpenAI Corporation")
            short_name = label.split()[0] if label else ""
            if short_name and len(short_name) >= 2:
                entity_names.append(short_name)

        # Build thumbnail text
        parts = []

        # Add entities
        if entity_names:
            if len(entity_names) == 2:
                parts.append(f"{entity_names[0]}×{entity_names[1]}")
            else:
                parts.append(entity_names[0])

        # Add numbers with context
        if numbers:
            num = numbers[0]
            # Add unit if not present
            if num and not any(unit in num for unit in ['億', '万', 'ドル', '円', '%']):
                num = num + "億"
            parts.append(num)

        # Add action keywords
        action_words = ['投資', '買収', '提携', '発表', '開発', '発売', 'リリース']
        for action in action_words:
            if action in title:
                parts.append(action)
                break

        # Combine parts
        if parts:
            thumbnail_text = " ".join(parts)
        elif keywords:
            # Fallback to keywords
            thumbnail_text = " ".join(keywords[:2])
        else:
            # Last resort: first part of title
            # Remove brackets and take first meaningful part
            clean_title = title.replace('【', '').replace('】', '').replace('「', '').replace('」', '')
            words = [w for w in clean_title.split() if len(w) >= 2]
            thumbnail_text = " ".join(words[:3]) if words else clean_title[:15]

    # Ensure text isn't too long (allow slightly more for better context)
    thumbnail_text = thumbnail_text[:25]

    # Create DALL-E 3 / Nano Banana prompt (background only - text will be added with PIL)
    dalle_prompt = f"""Japanese Anime Style YouTube Thumbnail Background.

SCENE: {visual_concept}

STYLE GUIDE:
- **Japanese Anime / Manga Art Style** (Cel-shaded, 2D illustration)
- **Vibrant, Saturated Colors** (Cyan, Magenta, Yellow, bright Pastels)
- **NO Photorealism**, NO 3D Renders, NO realistic skin textures
- **NO Grey skin**, NO creepy details
- Clean, bold lines and shapes
- Bright lighting (Anime opening sequence vibe)
- **NO TEXT** - background image only (text will be added separately)
- Leave center area relatively clear for text overlay
- Aspect Ratio 16:9

Make it look like a high-quality key visual background for a popular anime or bright variety show."""

    return {
        "prompt": dalle_prompt,
        "thumbnail_text": thumbnail_text,
        "numbers": numbers,
        "keywords": keywords,
        "emotion": emotion,
        "visual_concept": visual_concept
    }


# Example usage
if __name__ == "__main__":
    test_titles = [
        "【衝撃】ディズニー、OpenAIに1300億円投資！",
        "ChatGPT、日本で規制か？政府が法案を発表",
        "イーロン・マスク、テスラで自動運転革命を実現！"
    ]
    
    # Dummy entities for test
    test_entities = [
        [{"label": "Disney"}, {"label": "OpenAI"}],
        [{"label": "ChatGPT"}],
        [{"label": "Elon Musk"}, {"label": "Tesla"}]
    ]

    for i, title in enumerate(test_titles):
        print(f"\n{'='*60}")
        print(f"Title: {title}")
        result = generate_thumbnail_prompt(title, named_entities=test_entities[i])
        print(f"Concept: {result['visual_concept']}")
