"""
Info-Card Generator
Generates high-quality graphics for AI benchmarks and specs
"""
from PIL import Image, ImageDraw, ImageFont
import os
from pathlib import Path
from typing import Dict, List, Any

# Settings
CARD_WIDTH = 1200
CARD_HEIGHT = 800
BG_COLOR = (20, 24, 35, 230)  # Dark blue-gray with transparency
ACCENT_COLOR = (120, 200, 255) # Light blue
TEXT_COLOR = (255, 255, 255)
SECONDARY_TEXT = (180, 190, 210)

def create_benchmark_card(
    title: str,
    benchmarks: List[Dict[str, Any]],
    output_path: Path
):
    """
    Create a benchmark comparison card image
    benchmarks: [{"name": "MMLU", "value": "88.7%", "comparison": "+2.1%"}, ...]
    """
    # Create image
    img = Image.new('RGBA', (CARD_WIDTH, CARD_HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw background box with rounded corners
    padding = 40
    draw.rounded_rectangle(
        [padding, padding, CARD_WIDTH - padding, CARD_HEIGHT - padding],
        radius=30,
        fill=BG_COLOR,
        outline=ACCENT_COLOR,
        width=3
    )
    
    # Load fonts
    font_path = _find_font()
    if font_path:
        title_font = ImageFont.truetype(font_path, 60)
        label_font = ImageFont.truetype(font_path, 40)
        value_font = ImageFont.truetype(font_path, 50)  # Same font, larger size
    else:
        # Use default font if no font file found
        title_font = ImageFont.load_default()
        label_font = ImageFont.load_default()
        value_font = ImageFont.load_default()
    
    # Draw title
    draw.text((padding + 60, padding + 60), title, font=title_font, fill=ACCENT_COLOR)
    
    # Draw horizontal line
    draw.line([padding + 60, padding + 140, CARD_WIDTH - padding - 60, padding + 140], fill=SECONDARY_TEXT, width=1)
    
    # Draw benchmarks
    y_offset = padding + 180
    for i, bench in enumerate(benchmarks):
        name = bench.get("name", "Unknown")
        value = bench.get("value", "N/A")
        comp = bench.get("comparison", "")
        
        # Name label
        draw.text((padding + 80, y_offset), name, font=label_font, fill=TEXT_COLOR)
        
        # Value
        val_x = padding + 500
        draw.text((val_x, y_offset - 5), value, font=value_font, fill=TEXT_COLOR)
        
        # Comparison (green if positive)
        if comp:
            comp_color = (100, 255, 100) if "+" in comp else (255, 100, 100)
            draw.text((val_x + 250, y_offset), f"({comp})", font=label_font, fill=comp_color)
            
        y_offset += 100
        if i < len(benchmarks) - 1:
             draw.line([padding + 80, y_offset - 20, CARD_WIDTH - padding - 80, y_offset - 20], fill=(60, 70, 90), width=1)

    # Save
    img.save(output_path)
    print(f"Benchmark card saved to {output_path}")
    return output_path

def _find_font() -> str:
    font_paths = [
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",
        "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "msgothic.ttc"
    ]
    for p in font_paths:
        if os.path.exists(p):
            return p
    # Return None to use default font as fallback
    return None

if __name__ == "__main__":
    # Test
    test_bench = [
        {"name": "MMLU", "value": "88.7%", "comparison": "+2.1%"},
        {"name": "HumanEval", "value": "90.2%", "comparison": "+5.4%"},
        {"name": "GSM8K", "value": "95.0%", "comparison": "+1.2%"},
        {"name": "MATH", "value": "52.3%", "comparison": "-0.5%"}
    ]
    create_benchmark_card("GPT-4o Benchmarks", test_bench, Path("test_card.png"))
