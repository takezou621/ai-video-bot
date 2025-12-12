"""
Generate thumbnail template images with specified color codes
Creates 4 template variations based on the reference layout
"""
from PIL import Image, ImageDraw
from pathlib import Path

# Template specifications
TEMPLATE_WIDTH = 1280
TEMPLATE_HEIGHT = 720

# Color codes for each template
TEMPLATE_COLORS = {
    '74AA9C': {
        'light': '#9DCFC1',  # Lighter version for top/bottom bars
        'main': '#74AA9C',   # Main color for middle bar
        'dark': '#5A8A7C'    # Darker version
    },
    'CC9B7A': {
        'light': '#E6C5A8',
        'main': '#CC9B7A',
        'dark': '#A67B5A'
    },
    '669AFF': {
        'light': '#99BBFF',
        'main': '#669AFF',
        'dark': '#4D7AE6'
    },
    '8C52FF': {
        'light': '#B385FF',
        'main': '#8C52FF',
        'dark': '#6B3ECC'
    }
}

# Bar layout (matching the reference image)
TOP_BAR = {
    'y': 24,
    'height': 76
}

MIDDLE_BAR = {
    'y': 200,
    'height': 302
}

BOTTOM_BAR = {
    'y': 578,
    'height': 100
}


def hex_to_rgb(hex_color: str) -> tuple:
    """Convert hex color to RGB tuple"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def create_template(color_code: str, output_path: Path):
    """
    Create a thumbnail template with specified color scheme

    Args:
        color_code: Color code key (e.g., '74AA9C')
        output_path: Path to save the template image
    """
    colors = TEMPLATE_COLORS[color_code]

    # Create base image with white background
    img = Image.new('RGB', (TEMPLATE_WIDTH, TEMPLATE_HEIGHT), 'white')
    draw = ImageDraw.Draw(img)

    # Draw top bar (light color)
    top_color = hex_to_rgb(colors['light'])
    draw.rectangle(
        [(0, TOP_BAR['y']), (TEMPLATE_WIDTH, TOP_BAR['y'] + TOP_BAR['height'])],
        fill=top_color
    )

    # Draw middle bar (main/dark color)
    middle_color = hex_to_rgb(colors['dark'])
    draw.rectangle(
        [(0, MIDDLE_BAR['y']), (TEMPLATE_WIDTH, MIDDLE_BAR['y'] + MIDDLE_BAR['height'])],
        fill=middle_color
    )

    # Draw bottom bar (light color)
    bottom_color = hex_to_rgb(colors['light'])
    draw.rectangle(
        [(0, BOTTOM_BAR['y']), (TEMPLATE_WIDTH, BOTTOM_BAR['y'] + BOTTOM_BAR['height'])],
        fill=bottom_color
    )

    # Add subtle gradient effect to middle bar for depth
    gradient_overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    gradient_draw = ImageDraw.Draw(gradient_overlay)

    # Subtle top-to-bottom gradient on middle bar
    for i in range(MIDDLE_BAR['height']):
        y = MIDDLE_BAR['y'] + i
        alpha = int(30 * (i / MIDDLE_BAR['height']))  # 0 to 30
        gradient_draw.rectangle(
            [(0, y), (TEMPLATE_WIDTH, y + 1)],
            fill=(0, 0, 0, alpha)
        )

    # Composite gradient
    img = img.convert('RGBA')
    img = Image.alpha_composite(img, gradient_overlay)
    img = img.convert('RGB')

    # Add decorative corner accents (matching reference style)
    accent_color = hex_to_rgb(colors['main'])
    draw = ImageDraw.Draw(img)

    # Top-left corner
    draw.rectangle([(0, 0), (60, 60)], fill=accent_color)

    # Top-right corner
    draw.rectangle([(TEMPLATE_WIDTH - 60, 0), (TEMPLATE_WIDTH, 60)], fill=accent_color)

    # Save template
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, 'PNG', quality=95)
    print(f"✅ Created template: {output_path}")


def generate_all_templates():
    """Generate all 4 color template variations"""
    print("Generating thumbnail templates...")
    print("=" * 60)

    # Create templates directory
    templates_dir = Path(__file__).parent / "assets" / "templates"
    templates_dir.mkdir(parents=True, exist_ok=True)

    # Generate each template
    for color_code in TEMPLATE_COLORS.keys():
        output_path = templates_dir / f"thumbnail_template_color({color_code}).png"
        create_template(color_code, output_path)

    print("\n" + "=" * 60)
    print(f"✅ All templates created in: {templates_dir}")
    print("\nGenerated templates:")
    for color_code in TEMPLATE_COLORS.keys():
        print(f"  - thumbnail_template_color({color_code}).png")


if __name__ == "__main__":
    generate_all_templates()
