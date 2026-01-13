"""
DEPRECATED: This module has been renamed to gemini_generator.py.

This file is kept for backward compatibility only.
Please import from gemini_generator.py instead.

The original module name was misleading because it uses Gemini API,
not Claude API, for all content generation.

Migration:
- Replace: from claude_generator import X
- With: from gemini_generator import X

Or simply use the new function names:
- generate_dialogue_script() (was generate_dialogue_script_with_claude)
- generate_metadata() (was generate_metadata_with_claude)
- generate_comments() (was generate_comments_with_claude)
"""

import warnings

# Show deprecation warning
warnings.warn(
    "claude_generator.py is deprecated. Please use gemini_generator.py instead. "
    "The module uses Gemini API, not Claude API.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export everything from gemini_generator
from gemini_generator import (
    # Core functions
    generate_dialogue_script,
    generate_metadata,
    generate_comments,
    # Backward compatibility aliases
    generate_dialogue_script_with_claude,
    generate_metadata_with_claude,
    generate_comments_with_claude,
    # Internal functions (if needed)
    _call_gemini,
    _clean_json_string,
    _fallback_metadata,
    _fallback_comments,
    _build_hook_context,
    _validate_hook_quality,
    _ensure_structured_hook,
)

__all__ = [
    'generate_dialogue_script',
    'generate_metadata',
    'generate_comments',
    'generate_dialogue_script_with_claude',
    'generate_metadata_with_claude',
    'generate_comments_with_claude',
]
