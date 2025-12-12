# Three-Bar Thumbnail Layout

## Overview

The three-bar thumbnail layout is a new preset inspired by modern YouTube thumbnail designs. It features three horizontal colored bars that provide distinct areas for:

1. **Top Bar** (Light color): Category badge or topic label
2. **Middle Bar** (Dark color): Main title text
3. **Bottom Bar** (Light color): Subtitle or supporting text

Characters are positioned on the right side of the thumbnail, creating a balanced composition.

## Reference Image

This layout is based on the reference thumbnail from:
https://assets.st-note.com/img/1724404783645-Xy3wLI5DnR.png

## Usage

### Basic Usage

To create a thumbnail with the three-bar layout, use the `layout_name` parameter:

```python
from pathlib import Path
from thumbnail_generator import create_thumbnail

create_thumbnail(
    background_image_path=Path("path/to/background.png"),
    thumbnail_text="YouTubeサムネを一発で自動作成",
    subtitle_text="GPTsの作り方",
    output_path=Path("output/thumbnail.jpg"),
    accent_color_index=0,
    add_characters=True,
    topic_badge_text="プログラミング不要",
    layout_name="three_bar_layout"  # Force three-bar layout
)
```

### Parameters

- `background_image_path`: Path to background image
- `thumbnail_text`: Main title text (displayed in middle dark bar)
- `subtitle_text`: Supporting text (displayed in bottom light bar)
- `topic_badge_text`: Category badge (displayed in top light bar)
- `layout_name`: **Set to "three_bar_layout"** to use this layout
- `add_characters`: Set to `True` to include characters on the right
- `accent_color_index`: Color theme index (0-3) that determines bar colors

### Color Themes

The bar colors are derived from the theme selected via `topic_badge_text` or `accent_color_index`:

- **経済** (Economics): Gold/yellow tones
- **テック** (Tech): Blue tones
- **カルチャー** (Culture): Pink tones
- **ライフ** (Lifestyle): Green tones

The layout automatically creates:
- Light bars (top/bottom): 120% brightness of theme accent color
- Dark bar (middle): 50% brightness of theme accent color

## Layout Structure

```
┌────────────────────────────────────────┐
│                                        │
│  [Top Light Bar - Category Badge]     │  ← Line 150-250
│                                        │
├────────────────────────────────────────┤
│                                        │
│  [Middle Dark Bar - Main Title]       │  ← Line 280-400
│                                        │
├────────────────────────────────────────┤
│                                        │
│  [Bottom Light Bar - Subtitle]        │  ← Line 420-520
│                                        │
│                          [Characters]  │  ← Right side
└────────────────────────────────────────┘
```

## Testing

Two test scripts are available:

### 1. Full Test (requires image generation)
```bash
docker compose run --rm ai-video-bot python test_three_bar_thumbnail.py
```

This generates a new background image and creates 3 thumbnail variants.

### 2. Quick Test (uses existing background)
```bash
docker compose run --rm ai-video-bot python test_thumbnail_with_three_bars.py
```

This uses an existing background from recent video generation.

## Implementation Details

### Files Modified

1. **thumbnail_generator.py**
   - Added `three_bar_layout` preset to `LAYOUT_PRESETS`
   - Added `_apply_three_bar_layout()` function to render the bars
   - Modified `create_thumbnail()` to accept `layout_name` parameter
   - Skip standard gradient overlays for three-bar style

### New Functions

```python
def _apply_three_bar_layout(
    image: Image.Image,
    theme: Dict[str, Tuple[int, int, int]]
) -> Image.Image:
    """
    Apply three horizontal bars layout
    - Top bar: Light color at y=150
    - Middle bar: Dark color at y=280
    - Bottom bar: Light color at y=420
    """
```

### Layout Preset Configuration

```python
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
    "three_bar_style": True  # Flag to trigger three-bar rendering
}
```

## Integration with Video Pipeline

To use this layout in the automated video pipeline, modify `advanced_video_pipeline.py`:

```python
# In step 8 (thumbnail generation)
thumbnail_path = create_thumbnail(
    background_image_path=bg_path,
    thumbnail_text=metadata.get('youtube_title', topic_text),
    subtitle_text=metadata.get('subtitle', ''),
    output_path=output_dir / "thumbnail.jpg",
    topic_badge_text=category or "動画",
    layout_name="three_bar_layout"  # Add this line
)
```

## Tips for Best Results

1. **Text Length**: Keep main title under 12 characters per line for readability
2. **Subtitle**: Use short supporting text (max 28 characters)
3. **Badge Text**: Use concise category labels (4-6 characters)
4. **Characters**: Always enable for this layout (`add_characters=True`)
5. **Color Themes**: Choose theme that matches your content category

## Example Output

The three-bar layout creates thumbnails with:
- Clear visual hierarchy (category → title → subtitle)
- Strong color contrast for clickability
- Character positioning that doesn't overlap text
- Consistent branding across videos

## Future Enhancements

Potential improvements:
- [ ] Add icon support in top bar
- [ ] Animated bar transitions
- [ ] Custom bar heights via parameters
- [ ] Gradient fills within bars
- [ ] Text shadows within bars for depth
