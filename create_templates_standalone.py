#!/usr/bin/env python3
"""
Standalone script to generate thumbnail templates
Can be run directly without dependencies
"""
from PIL import Image, ImageDraw
from pathlib import Path

# Template specifications
TEMPLATE_WIDTH = 1280
TEMPLATE_HEIGHT = 720

# Color codes for each template
TEMPLATE_COLORS = {
    '74AA9C': {
        'light': (157, 207, 193),  # RGB for #9DCFC1
        'main': (116, 170, 156),   # RGB for #74AA9C
        'dark': (90, 138, 124)     # RGB for #5A8A7C
    },
    'CC9B7A': {
        'light': (230, 197, 168),  # RGB for #E6C5A8
        'main': (204, 155, 122),   # RGB for #CC9B7A
        'dark': (166, 123, 90)     # RGB for #A67B5A
    },
    '669AFF': {
        'light': (153, 187, 255),  # RGB for #99BBFF
        'main': (102, 154, 255),   # RGB for #669AFF
        'dark': (77, 122, 230)     # RGB for #4D7AE6
    },
    '8C52FF': {
        'light': (179, 133, 255),  # RGB for #B385FF
        'main': (140, 82, 255),    # RGB for #8C52FF
        'dark': (107, 62, 204)     # RGB for #6B3ECC
    }
}

# Bar layout (matching the requirements)
TOP_BAR = {'y': 24, 'height': 76}
MIDDLE_BAR = {'y': 200, 'height': 302}
BOTTOM_BAR = {'y': 578, 'height': 100}


def create_template(color_code, output_path):
    """Create a thumbnail template with specified color scheme"""
    colors = TEMPLATE_COLORS[color_code]

    # Create base image with white background
    img = Image.new('RGB', (TEMPLATE_WIDTH, TEMPLATE_HEIGHT), 'white')
    draw = ImageDraw.Draw(img)

    # Draw top bar (light color)
    draw.rectangle(
        [(0, TOP_BAR['y']), (TEMPLATE_WIDTH, TOP_BAR['y'] + TOP_BAR['height'])],
        fill=colors['light']
    )

    # Draw middle bar (dark color for better contrast)
    draw.rectangle(
        [(0, MIDDLE_BAR['y']), (TEMPLATE_WIDTH, MIDDLE_BAR['y'] + MIDDLE_BAR['height'])],
        fill=colors['dark']
    )

    # Draw bottom bar (light color)
    draw.rectangle(
        [(0, BOTTOM_BAR['y']), (TEMPLATE_WIDTH, BOTTOM_BAR['y'] + BOTTOM_BAR['height'])],
        fill=colors['light']
    )

    # Add subtle gradient effect to middle bar for depth
    gradient_overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    gradient_draw = ImageDraw.Draw(gradient_overlay)

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

    # Add decorative corner accents
    accent_color = colors['main']
    draw = ImageDraw.Draw(img)

    # Top-left and top-right corners
    draw.rectangle([(0, 0), (60, 60)], fill=accent_color)
    draw.rectangle([(TEMPLATE_WIDTH - 60, 0), (TEMPLATE_WIDTH, 60)], fill=accent_color)

    # Save template
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, 'PNG', quality=95)
    print(f"✅ Created: {output_path}")


if __name__ == "__main__":
    print("Generating thumbnail templates...")
    print("=" * 60)

    templates_dir = Path("assets/templates")
    templates_dir.mkdir(parents=True, exist_ok=True)

    for color_code in TEMPLATE_COLORS.keys():
        output_path = templates_dir / f"thumbnail_template_color({color_code}).png"
        create_template(color_code, output_path)

    print("=" * 60)
    print(f"✅ All templates created in: {templates_dir}")
