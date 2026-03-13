"""Code block renderer"""

import curses
from typing import List
from ..utils.terminal import get_display_width
from .syntax_highlight import SyntaxHighlighter

class CodeRenderer:
    """Code block renderer"""
    
    def __init__(self, theme='monokai'):
        """Initialize code renderer"""
        self.theme = theme
        self.syntax_highlighter = SyntaxHighlighter(theme)
    
    def _highlight_search_term(self, stdscr, y, x, text, search_term, default_attr=0):
        """Highlight search term in text"""
        if not search_term:
            stdscr.addstr(y, x, text, default_attr)
            return
        
        import re
        # Find all occurrences of search term
        if search_term.isascii():
            # Case-insensitive search for ASCII
            pattern = re.compile(re.escape(search_term), re.IGNORECASE)
        else:
            # Case-sensitive search for non-ASCII
            pattern = re.compile(re.escape(search_term))
        
        pos = 0
        for match in pattern.finditer(text):
            # Add text before match
            stdscr.addstr(y, x + pos, text[pos:match.start()], default_attr)
            # Add matched text with highlight
            stdscr.addstr(y, x + match.start(), match.group(), curses.A_REVERSE | default_attr)
            pos = match.end()
        
        # Add remaining text
        if pos < len(text):
            stdscr.addstr(y, x + pos, text[pos:], default_attr)
    
    def render(self, stdscr, y: int, lang: str, lines: List[str], width: int, is_current_result: bool = False, search_term: str = "") -> int:
        """Render code block with proper wrapping"""
        try:
            # Calculate actual available width for the entire code block
            # Leave 1 character margin on each side
            available_width = width - 2
            available_width = max(10, available_width)  # Minimum width
            
            # Calculate content width (excluding borders and padding)
            # Total overhead per line: 4 characters (| | at start and end)
            content_width = available_width - 4
            content_width = max(6, content_width)  # Minimum content width
            
            # Create consistent border line
            # Use a fixed width for border line to ensure consistency
            border_line = "|" + "-" * (available_width - 2) + "|"
            
            # Create language header line
            lang_padded = lang.ljust(content_width)
            header_line = "| " + lang_padded + " |"
            # Ensure header line fits
            if get_display_width(header_line) > available_width:
                # Truncate header line to fit
                truncated_header = ""
                current_width = 0
                for char in header_line:
                    char_width = get_display_width(char)
                    if current_width + char_width > available_width:
                        break
                    truncated_header += char
                    current_width += char_width
                header_line = truncated_header
            
            # Ensure header line has the same width as border line
            header_width = get_display_width(header_line)
            border_width = get_display_width(border_line)
            if header_width < border_width:
                # Add padding to match border line width
                padding_needed = border_width - header_width
                header_line = header_line[:-1] + " " * padding_needed + "|"
            elif header_width > border_width:
                # Truncate to match border line width
                truncated_header = ""
                current_width = 0
                for char in header_line:
                    char_width = get_display_width(char)
                    if current_width + char_width > border_width:
                        break
                    truncated_header += char
                    current_width += char_width
                # Ensure we end with a closing pipe
                if not truncated_header.endswith("|"):
                    truncated_header = truncated_header[:-1] + "|"
                header_line = truncated_header
            
            # Top border
            stdscr.addstr(y, 1, border_line, curses.color_pair(8))
            y += 1
            
            # Language header
            stdscr.addstr(y, 1, header_line, curses.color_pair(8) | curses.A_BOLD)
            y += 1
            
            # Separator
            stdscr.addstr(y, 1, border_line, curses.color_pair(8))
            y += 1
            
            # Check if this code block contains a text table
            contains_table = any(any(char in '┌┬┐├┼┤└┴┘─│' for char in line) for line in lines)
            
            if contains_table:
                # For code blocks containing tables, use a different rendering approach
                for line in lines:
                    # Skip empty lines
                    if not line.strip():
                        # Add empty line with proper formatting
                        empty_line = "| " + " " * (available_width - 4) + " |"
                        stdscr.addstr(y, 1, empty_line, curses.color_pair(8))
                        y += 1
                        continue
                    
                    # For table lines, preserve the original structure as much as possible
                    # Calculate the available content width
                    content_width = available_width - 4
                    
                    # Process the line to fit within content_width while preserving structure
                    processed_line = ""
                    current_width = 0
                    
                    # Process each character in the line
                    for char in line:
                        char_width = get_display_width(char)
                        if current_width + char_width <= content_width:
                            processed_line += char
                            current_width += char_width
                        else:
                            # Stop when we reach the content width
                            break
                    
                    # Add padding to make the line fill the content area
                    padding_needed = content_width - current_width
                    if padding_needed > 0:
                        processed_line += " " * padding_needed
                    
                    # Create display line with consistent width
                    display_line = "| " + processed_line + " |"
                    
                    # Ensure display line has the exact same width as border line
                    # Calculate width difference
                    display_width = get_display_width(display_line)
                    border_width = get_display_width(border_line)
                    
                    # Force the display line to match the border line width exactly
                    if display_width != border_width:
                        # Create a new display line with the exact border width
                        new_display_line = "|"
                        current_width = 1  # Account for the opening pipe
                        
                        # Add space after opening pipe
                        new_display_line += " "
                        current_width += 1
                        
                        # Add content, ensuring we don't exceed the available width
                        content_chars = []
                        content_width_used = 0
                        max_content_width = border_width - 3  # Subtract opening and closing pipes with spaces
                        
                        for char in line:
                            char_width = get_display_width(char)
                            if content_width_used + char_width <= max_content_width:
                                content_chars.append(char)
                                content_width_used += char_width
                            else:
                                break
                        
                        # Add the content
                        new_display_line += ''.join(content_chars)
                        current_width += content_width_used
                        
                        # Add padding to reach the border width
                        remaining_width = border_width - current_width
                        if remaining_width > 0:
                            new_display_line += " " * remaining_width
                        
                        # Ensure we end with a closing pipe
                        if not new_display_line.endswith("|"):
                            # If we're short, add the closing pipe
                            if len(new_display_line) < border_width:
                                new_display_line += "|"
                            else:
                                # If we're over, truncate and add closing pipe
                                new_display_line = new_display_line[:border_width-1] + "|"
                        
                        display_line = new_display_line
                    
                    if is_current_result and search_term:
                        # Highlight search term in current result
                        self._highlight_search_term(stdscr, y, 1, display_line, search_term, curses.color_pair(8))
                    else:
                        stdscr.addstr(y, 1, display_line, curses.color_pair(8))
                    y += 1
            else:
                # For regular code blocks, use syntax highlighting
                for line in lines:
                    # Skip empty lines
                    if not line.strip():
                        # Add empty line with proper formatting
                        empty_line = "| " + " " * (available_width - 4) + " |"
                        stdscr.addstr(y, 1, empty_line, curses.color_pair(8))
                        y += 1
                        continue
                    
                    # Wrap line based on actual available width
                    wrapped_lines = self._wrap_code_line(line, available_width - 4)
                    
                    for wrapped_line in wrapped_lines:
                        # Apply syntax highlighting
                        highlighted_line = self.syntax_highlighter.highlight(wrapped_line, lang)
                        
                        # Calculate padding based on display width
                        display_width = get_display_width(highlighted_line)
                        padding_needed = (available_width - 4) - display_width
                        if padding_needed > 0:
                            padded_line = highlighted_line + " " * padding_needed
                        else:
                            # Truncate if needed
                            truncated_line = ""
                            current_width = 0
                            for char in highlighted_line:
                                char_width = get_display_width(char)
                                if current_width + char_width > (available_width - 4):
                                    break
                                truncated_line += char
                                current_width += char_width
                            padded_line = truncated_line
                        
                        # Create display line with consistent width
                        display_line = "| " + padded_line + " |"
                        # Ensure display line fits
                        if get_display_width(display_line) > available_width:
                            # Truncate display line to fit
                            truncated_display = ""
                            current_width = 0
                            for char in display_line:
                                char_width = get_display_width(char)
                                if current_width + char_width > available_width:
                                    break
                                truncated_display += char
                                current_width += char_width
                            display_line = truncated_display
                        
                        # Ensure display line has the same width as border line
                        # Calculate width difference
                        display_width = get_display_width(display_line)
                        border_width = get_display_width(border_line)
                        if display_width < border_width:
                            # Add padding to match border line width
                            padding_needed = border_width - display_width
                            display_line = display_line[:-1] + " " * padding_needed + "|"
                        elif display_width > border_width:
                            # Truncate to match border line width
                            truncated_display = ""
                            current_width = 0
                            for char in display_line:
                                char_width = get_display_width(char)
                                if current_width + char_width > border_width:
                                    break
                                truncated_display += char
                                current_width += char_width
                            # Ensure we end with a closing pipe
                            if not truncated_display.endswith("|"):
                                truncated_display = truncated_display[:-1] + "|"
                            display_line = truncated_display
                        
                        # Use code color for code blocks
                        if is_current_result and search_term:
                            # Highlight search term in current result
                            self._highlight_search_term(stdscr, y, 1, display_line, search_term, curses.color_pair(8))
                        else:
                            stdscr.addstr(y, 1, display_line, curses.color_pair(8))
                        y += 1
            
            # Bottom border
            stdscr.addstr(y, 1, border_line, curses.color_pair(8))
            y += 1
        except:
            pass
        
        return y
    
    def _wrap_code_line(self, line: str, max_width: int) -> List[str]:
        """Wrap code line to fit within max width, considering Chinese characters"""
        lines = []
        current_line = ""
        current_width = 0
        
        # Check if this line is part of a text table
        is_table_line = any(char in '┌┬┐├┼┤└┴┘─│' for char in line)
        
        if is_table_line:
            # For table lines, we need to handle them differently
            # If the line is too long, we'll split it at appropriate positions
            if get_display_width(line) <= max_width:
                # Line fits, no wrapping needed
                lines.append(line)
            else:
                # Line is too long, we need to split it
                # For table lines, we'll split at spaces or after border characters
                words = line.split()
                current_line = ""
                current_width = 0
                
                for word in words:
                    word_width = get_display_width(word)
                    space_width = get_display_width(" ")
                    
                    if current_line and current_width + space_width + word_width <= max_width:
                        current_line += " " + word
                        current_width += space_width + word_width
                    elif word_width <= max_width:
                        if current_line:
                            lines.append(current_line)
                        current_line = word
                        current_width = word_width
                    else:
                        # Word is too long, split it character by character
                        for char in word:
                            char_width = get_display_width(char)
                            if current_width + char_width <= max_width:
                                current_line += char
                                current_width += char_width
                            else:
                                lines.append(current_line)
                                current_line = char
                                current_width = char_width
                
                if current_line:
                    lines.append(current_line)
        else:
            # For non-table lines, use the original character-by-character wrapping
            for char in line:
                char_width = get_display_width(char)
                if current_width + char_width <= max_width:
                    current_line += char
                    current_width += char_width
                else:
                    lines.append(current_line)
                    current_line = char
                    current_width = char_width
            
            if current_line:
                lines.append(current_line)
        
        return lines