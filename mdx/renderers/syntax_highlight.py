"""Syntax highlighter"""

from typing import Optional, List, Tuple

# Try to import pygments for syntax highlighting
try:
    from pygments import highlight
    from pygments.lexers import get_lexer_by_name, guess_lexer
    from pygments.token import Token
    from pygments.styles import get_style_by_name
    HAS_PYGMENTS = True
except ImportError:
    HAS_PYGMENTS = False

class SyntaxHighlighter:
    """Syntax highlighter"""
    
    def __init__(self, theme='monokai'):
        """Initialize syntax highlighter"""
        self.theme = theme
        self.style = None
        
        if HAS_PYGMENTS:
            try:
                self.style = get_style_by_name(theme)
            except:
                # Fallback to default style if theme not found
                self.style = get_style_by_name('monokai')
    
    def highlight(self, code: str, lang: str) -> str:
        """Highlight code with syntax highlighting"""
        if not HAS_PYGMENTS:
            # If pygments is not available, return code as is
            return code
        
        try:
            # Try to get lexer by language name
            if lang and lang != 'text':
                try:
                    lexer = get_lexer_by_name(lang)
                except:
                    # Guess lexer if language not found
                    try:
                        lexer = guess_lexer(code)
                    except:
                        # If guessing fails, return code as is
                        return code
            else:
                # Return code as is if language not specified
                return code
            
            # Use pygments to highlight the code
            # We'll return the code as is for now, but we'll add proper highlighting later
            # For terminal output, we'll need to convert pygments tokens to terminal color codes
            return code
        except:
            # If highlighting fails, return code as is
            return code