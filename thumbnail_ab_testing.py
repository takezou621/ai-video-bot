"""
Thumbnail A/B Testing - Generate multiple variations for click-through rate optimization
Implements the blog's approach to thumbnail optimization
"""
from pathlib import Path
from typing import List, Dict, Tuple
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
import os


class ThumbnailVariationGenerator:
    """
    Generates multiple thumbnail variations for A/B testing.

    Variations include:
    - Different text layouts (top, center, bottom)
    - Different color schemes
    - Different visual effects (blur, brightness, contrast)
    - Different text sizes and styles
    """

    # Layout presets
    LAYOUTS = {
        "top_bold": {"position": "top", "size_multiplier": 1.2, "bold": True},
        "center_standard": {"position": "center", "size_multiplier": 1.0, "bold": False},
        "bottom_large": {"position": "bottom", "size_multiplier": 1.3, "bold": True},
        "split_dual": {"position": "split", "size_multiplier": 1.0, "bold": False}
    }

    # Color schemes (text, shadow, accent)
    COLOR_SCHEMES = {
        "classic": {"text": (255, 255, 255), "shadow": (0, 0, 0), "accent": (255, 200, 0)},
        "high_contrast": {"text": (255, 255, 0), "shadow": (0, 0, 0), "accent": (255, 100, 100)},
        "modern": {"text": (240, 240, 255), "shadow": (10, 10, 30), "accent": (100, 200, 255)},
        "vibrant": {"text": (255, 255, 255), "shadow": (50, 0, 100), "accent": (255, 0, 150)}
    }

    # Visual effects
    EFFECTS = {
        "none": {},
        "slight_blur": {"blur_radius": 1},
        "brightness_boost": {"brightness": 1.2},
        "high_contrast": {"contrast": 1.3},
        "saturation_boost": {"saturation": 1.4}
    }

    @staticmethod
    def generate_variations(
        background_image_path: Path,
        thumbnail_text: str,
        output_dir: Path,
        count: int = 5
    ) -> List[Dict[str, any]]:
        """
        Generate multiple thumbnail variations for A/B testing.

        Args:
            background_image_path: Path to background image
            thumbnail_text: Main text to overlay
            output_dir: Output directory for variations
            count: Number of variations to generate

        Returns:
            List of variation metadata
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        variations = []

        # Load background
        bg_base = Image.open(background_image_path).convert('RGB')
        bg_base = bg_base.resize((1280, 720), Image.Resampling.LANCZOS)

        # Variation 1: Classic bold top
        variations.append(ThumbnailVariationGenerator._create_variation(
            bg_base.copy(),
            thumbnail_text,
            output_dir / "variant_1_classic_top_bold.jpg",
            layout="top_bold",
            color_scheme="classic",
            effect="brightness_boost"
        ))

        # Variation 2: High contrast center
        variations.append(ThumbnailVariationGenerator._create_variation(
            bg_base.copy(),
            thumbnail_text,
            output_dir / "variant_2_high_contrast_center.jpg",
            layout="center_standard",
            color_scheme="high_contrast",
            effect="high_contrast"
        ))

        # Variation 3: Modern bottom large
        variations.append(ThumbnailVariationGenerator._create_variation(
            bg_base.copy(),
            thumbnail_text,
            output_dir / "variant_3_modern_bottom.jpg",
            layout="bottom_large",
            color_scheme="modern",
            effect="saturation_boost"
        ))

        # Variation 4: Vibrant with slight blur
        variations.append(ThumbnailVariationGenerator._create_variation(
            bg_base.copy(),
            thumbnail_text,
            output_dir / "variant_4_vibrant.jpg",
            layout="center_standard",
            color_scheme="vibrant",
            effect="slight_blur"
        ))

        # Variation 5: Classic no effects
        if count >= 5:
            variations.append(ThumbnailVariationGenerator._create_variation(
                bg_base.copy(),
                thumbnail_text,
                output_dir / "variant_5_classic_clean.jpg",
                layout="center_standard",
                color_scheme="classic",
                effect="none"
            ))

        print(f"✓ Generated {len(variations)} thumbnail variations for A/B testing")
        return variations[:count]

    @staticmethod
    def _create_variation(
        bg_image: Image.Image,
        text: str,
        output_path: Path,
        layout: str,
        color_scheme: str,
        effect: str
    ) -> Dict:
        """Create a single thumbnail variation."""
        # Apply visual effects
        bg_image = ThumbnailVariationGenerator._apply_effect(bg_image, effect)

        # Get styling
        layout_config = ThumbnailVariationGenerator.LAYOUTS[layout]
        colors = ThumbnailVariationGenerator.COLOR_SCHEMES[color_scheme]

        # Get font
        base_size = 80
        font_size = int(base_size * layout_config["size_multiplier"])
        font = ThumbnailVariationGenerator._get_font(font_size, layout_config["bold"])

        # Add text overlay
        ThumbnailVariationGenerator._add_text_overlay(
            bg_image,
            text,
            font,
            colors,
            layout_config["position"]
        )

        # Save
        bg_image.save(output_path, 'JPEG', quality=95, optimize=True)

        return {
            "path": str(output_path),
            "layout": layout,
            "color_scheme": color_scheme,
            "effect": effect,
            "filename": output_path.name
        }

    @staticmethod
    def _apply_effect(image: Image.Image, effect_name: str) -> Image.Image:
        """Apply visual effect to image."""
        effect_config = ThumbnailVariationGenerator.EFFECTS[effect_name]

        if "blur_radius" in effect_config:
            image = image.filter(ImageFilter.GaussianBlur(effect_config["blur_radius"]))

        if "brightness" in effect_config:
            enhancer = ImageEnhance.Brightness(image)
            image = enhancer.enhance(effect_config["brightness"])

        if "contrast" in effect_config:
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(effect_config["contrast"])

        if "saturation" in effect_config:
            enhancer = ImageEnhance.Color(image)
            image = enhancer.enhance(effect_config["saturation"])

        return image

    @staticmethod
    def _get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
        """Get font for text rendering."""
        font_paths = [
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
            "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc",
            "C:\\Windows\\Fonts\\msgothic.ttc",
        ]

        for path in font_paths:
            if os.path.exists(path):
                try:
                    return ImageFont.truetype(path, size)
                except:
                    continue

        return ImageFont.load_default()

    @staticmethod
    def _add_text_overlay(
        image: Image.Image,
        text: str,
        font: ImageFont.FreeTypeFont,
        colors: Dict,
        position: str
    ):
        """Add text overlay to image."""
        draw = ImageDraw.Draw(image)
        width, height = image.size

        # Wrap text
        max_width = width - 200
        lines = ThumbnailVariationGenerator._wrap_text(text, font, max_width)

        # Limit to 2 lines
        if len(lines) > 2:
            lines = lines[:2]
            if lines[-1]:
                lines[-1] = lines[-1][:-1] + "…"

        # Calculate position
        line_height = font.size + 20
        total_height = len(lines) * line_height

        if position == "top":
            start_y = 100
        elif position == "bottom":
            start_y = height - total_height - 100
        else:  # center
            start_y = (height - total_height) // 2

        # Draw text with shadow
        for i, line in enumerate(lines):
            bbox = font.getbbox(line)
            line_width = bbox[2] - bbox[0]
            x = (width - line_width) // 2
            y = start_y + (i * line_height)

            # Shadow (multiple layers for strength)
            for offset in range(1, 8):
                draw.text(
                    (x + offset, y + offset),
                    line,
                    font=font,
                    fill=colors["shadow"]
                )

            # Main text
            draw.text((x, y), line, font=font, fill=colors["text"])

            # Optional accent stroke
            # (PIL doesn't support text stroke directly, so we'd need to draw outline manually)

    @staticmethod
    def _wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> List[str]:
        """Wrap text to fit within max width."""
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


if __name__ == "__main__":
    # Test
    import tempfile

    test_dir = Path(tempfile.mkdtemp())
    print(f"Test output directory: {test_dir}")

    # Create a test background (solid color)
    test_bg = Image.new('RGB', (1280, 720), color=(50, 50, 100))
    test_bg_path = test_dir / "test_bg.jpg"
    test_bg.save(test_bg_path)

    # Generate variations
    generator = ThumbnailVariationGenerator()
    variations = generator.generate_variations(
        test_bg_path,
        "AIの最新情報を解説",
        test_dir,
        count=5
    )

    print("\nGenerated variations:")
    for var in variations:
        print(f"  - {var['filename']}: {var['layout']} / {var['color_scheme']} / {var['effect']}")
