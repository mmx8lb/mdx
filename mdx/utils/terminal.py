"""Terminal utility functions"""

import shutil
import os

# Try to import wcwidth for accurate character width calculation
try:
    import wcwidth
    HAS_WCWIDTH = True
except ImportError:
    HAS_WCWIDTH = False

def get_terminal_size():
    """Get terminal screen size"""
    try:
        # Try to get size from shutil
        size = shutil.get_terminal_size()
        # Ensure we have reasonable values
        min_columns = 40
        min_lines = 10
        
        columns = max(size.columns, min_columns)
        lines = max(size.lines, min_lines)
        
        return os.terminal_size((columns, lines))
    except:
        # Fallback to reasonable default
        return os.terminal_size((80, 24))

def get_display_width(text: str) -> int:
    """Calculate display width of text, considering Chinese characters and special symbols"""
    width = 0
    for char in text:
        if HAS_WCWIDTH:
            # Use wcwidth library for accurate character width calculation
            char_width = wcwidth.wcwidth(char)
            if char_width > 0:
                width += char_width
            else:
                # For control characters or other non-printable characters
                width += 1
        else:
            # Fallback to simple character width calculation
            # Chinese characters and other wide characters
            if ord(char) > 127:
                width += 2
            else:
                # Regular ASCII characters, including border symbols
                width += 1
    return width