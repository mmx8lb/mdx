"""Markdown renderer module"""

import curses
import shutil
import os
from typing import List, Tuple, Dict, Any
from .parser import MarkdownParser

# Try to import wcwidth for accurate character width calculation
try:
    import wcwidth
    HAS_WCWIDTH = True
except ImportError:
    HAS_WCWIDTH = False


class TerminalRenderer:
    """Terminal renderer for Markdown"""
    
    def __init__(self):
        self.theme = {
            'header': {
                1: (curses.COLOR_CYAN, -1),
                2: (curses.COLOR_BLUE, -1),
                3: (curses.COLOR_GREEN, -1),
                4: (curses.COLOR_YELLOW, -1),
                5: (curses.COLOR_RED, -1),
                6: (curses.COLOR_MAGENTA, -1)
            },
            'list': (curses.COLOR_MAGENTA, -1),
            'blockquote': (curses.COLOR_GREEN, -1),
            'code': (curses.COLOR_YELLOW, -1),
            'table': (curses.COLOR_CYAN, -1),
            'hr': (curses.COLOR_WHITE, -1)
        }
        self.cache = {}
        self.last_scroll = -1
        self.last_height = 0
        self.last_width = 0
    
    def get_screen_size(self):
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
    
    def render(self, stdscr, parsed_content: List[Tuple[str, Any]], scroll: int = 0):
        """Render parsed content to terminal with optimized rendering"""
        curses.curs_set(0)
        
        try:
            # Get screen size
            size = self.get_screen_size()
            height = size.lines
            width = size.columns
            content_height = height - 5
            total = len(parsed_content)
            
            # Initialize colors only once
            if not hasattr(self, 'colors_initialized'):
                if curses.has_colors():
                    curses.start_color()
                    curses.use_default_colors()
                    
                    # Initialize color pairs
                    for i, (fg, bg) in enumerate([
                        (curses.COLOR_CYAN, -1),    # 1: header 1
                        (curses.COLOR_BLUE, -1),    # 2: header 2
                        (curses.COLOR_GREEN, -1),   # 3: header 3
                        (curses.COLOR_YELLOW, -1),  # 4: header 4
                        (curses.COLOR_RED, -1),     # 5: header 5-6
                        (curses.COLOR_MAGENTA, -1), # 6: list
                        (curses.COLOR_GREEN, -1),   # 7: blockquote
                        (curses.COLOR_YELLOW, -1),  # 8: code
                        (curses.COLOR_CYAN, -1),    # 9: table
                        (curses.COLOR_WHITE, -1)    # 10: hr
                    ], 1):
                        try:
                            curses.init_pair(i, fg, bg)
                        except:
                            pass
                self.colors_initialized = True
            
            # Only clear screen if necessary (e.g., first render or screen size changed)
            if (self.last_height != height or self.last_width != width or 
                self.last_scroll == -1):
                stdscr.clear()
            
            # Header
            try:
                # Clear header area
                stdscr.move(0, 0)
                stdscr.clrtoeol()
                stdscr.addstr(0, 0, " MDX - Markdown Viewer ", curses.A_REVERSE | curses.A_BOLD)
                
                stdscr.move(1, 0)
                stdscr.clrtoeol()
                stdscr.addstr(1, 0, f" {scroll + 1}-{min(scroll + content_height, total)}/{total} | j/k滚动 q退出 ", curses.A_DIM)
                
                stdscr.move(2, 0)
                stdscr.clrtoeol()
                stdscr.addstr(2, 0, "─" * (width - 1), curses.A_DIM)
            except:
                pass
            
            # Content area
            y = 3
            idx = 0
            
            # Clear content area
            for i in range(3, height - 1):
                try:
                    stdscr.move(i, 0)
                    stdscr.clrtoeol()
                except:
                    pass
            
            # Render content
            for item_type, content in parsed_content:
                if idx < scroll:
                    idx += 1
                    continue
                
                if y >= height - 2:
                    break
                
                try:
                    if item_type == 'header':
                        level, title = content
                        color_pair = min(level, 5)
                        stdscr.addstr(y, 0, f"{'#' * level} {title}", curses.color_pair(color_pair) | curses.A_BOLD)
                        y += 1
                    elif item_type == 'list_item':
                        list_type, item_content = content
                        marker = '•' if list_type == 'unordered' else '1.'
                        stdscr.addstr(y, 2, marker, curses.color_pair(6))
                        stdscr.addstr(y, 5, item_content)
                        y += 1
                    elif item_type == 'blockquote':
                        stdscr.addstr(y, 2, '>', curses.color_pair(7))
                        stdscr.addstr(y, 4, content, curses.color_pair(7))
                        y += 1
                    elif item_type == 'code_block':
                        lang, lines = content
                        y = self._render_code_block(stdscr, y, lang, lines, width)
                    elif item_type == 'table':
                        y = self._render_table(stdscr, y, content, width)
                    elif item_type == 'hr':
                        stdscr.addstr(y, 0, "─" * (width - 1), curses.color_pair(10))
                        y += 1
                    else:  # text
                        stdscr.addstr(y, 0, content[:width-1])
                        y += 1
                except Exception as e:
                    # Display error message for debugging
                    try:
                        stdscr.addstr(y, 0, f"Error rendering {item_type}: {str(e)}")
                        y += 1
                    except:
                        pass
                
                idx += 1
            
            # Progress bar
            try:
                stdscr.move(height - 2, 0)
                stdscr.clrtoeol()
                
                if total > content_height:
                    bar_width = min(40, width - 10)
                    prog = scroll / (total - content_height)
                    filled = int(bar_width * prog)
                    bar = "█" * filled + "░" * (bar_width - filled)
                    stdscr.addstr(height - 2, 0, f"│{bar}│ {int(prog * 100)}%", curses.A_DIM)
            except:
                pass
            
            # Refresh only once at the end
            stdscr.refresh()
            
            # Update last state
            self.last_scroll = scroll
            self.last_height = height
            self.last_width = width
        except Exception as e:
            # Display overall error
            try:
                stdscr.clear()
                stdscr.addstr(0, 0, f"Error: {str(e)}", curses.A_REVERSE | curses.A_BOLD)
                stdscr.refresh()
            except:
                pass
    
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
            if self._get_display_width(line) <= max_width:
                # Line fits, no wrapping needed
                lines.append(line)
            else:
                # Line is too long, we need to split it
                # For table lines, we'll split at spaces or after border characters
                words = line.split()
                current_line = ""
                current_width = 0
                
                for word in words:
                    word_width = self._get_display_width(word)
                    space_width = self._get_display_width(" ")
                    
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
                            char_width = self._get_display_width(char)
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
                char_width = self._get_display_width(char)
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
    
    def _render_code_block(self, stdscr, y: int, lang: str, lines: List[str], width: int):
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
            if self._get_display_width(header_line) > available_width:
                # Truncate header line to fit
                truncated_header = ""
                current_width = 0
                for char in header_line:
                    char_width = self._get_display_width(char)
                    if current_width + char_width > available_width:
                        break
                    truncated_header += char
                    current_width += char_width
                header_line = truncated_header
            
            # Ensure header line has the same width as border line
            header_width = self._get_display_width(header_line)
            border_width = self._get_display_width(border_line)
            if header_width < border_width:
                # Add padding to match border line width
                padding_needed = border_width - header_width
                header_line = header_line[:-1] + " " * padding_needed + "|"
            elif header_width > border_width:
                # Truncate to match border line width
                truncated_header = ""
                current_width = 0
                for char in header_line:
                    char_width = self._get_display_width(char)
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
                        char_width = self._get_display_width(char)
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
                    display_width = self._get_display_width(display_line)
                    border_width = self._get_display_width(border_line)
                    
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
                            char_width = self._get_display_width(char)
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
                    
                    stdscr.addstr(y, 1, display_line, curses.color_pair(8))
                    y += 1
            else:
                # For regular code blocks, use the original wrapping approach
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
                        # Calculate padding based on display width
                        display_width = self._get_display_width(wrapped_line)
                        padding_needed = (available_width - 4) - display_width
                        if padding_needed > 0:
                            padded_line = wrapped_line + " " * padding_needed
                        else:
                            # Truncate if needed
                            truncated_line = ""
                            current_width = 0
                            for char in wrapped_line:
                                char_width = self._get_display_width(char)
                                if current_width + char_width > (available_width - 4):
                                    break
                                truncated_line += char
                                current_width += char_width
                            padded_line = truncated_line
                        
                        # Create display line with consistent width
                        display_line = "| " + padded_line + " |"
                        # Ensure display line fits
                        if self._get_display_width(display_line) > available_width:
                            # Truncate display line to fit
                            truncated_display = ""
                            current_width = 0
                            for char in display_line:
                                char_width = self._get_display_width(char)
                                if current_width + char_width > available_width:
                                    break
                                truncated_display += char
                                current_width += char_width
                            display_line = truncated_display
                        
                        # Ensure display line has the same width as border line
                        # Calculate width difference
                        display_width = self._get_display_width(display_line)
                        border_width = self._get_display_width(border_line)
                        if display_width < border_width:
                            # Add padding to match border line width
                            padding_needed = border_width - display_width
                            display_line = display_line[:-1] + " " * padding_needed + "|"
                        elif display_width > border_width:
                            # Truncate to match border line width
                            truncated_display = ""
                            current_width = 0
                            for char in display_line:
                                char_width = self._get_display_width(char)
                                if current_width + char_width > border_width:
                                    break
                                truncated_display += char
                                current_width += char_width
                            # Ensure we end with a closing pipe
                            if not truncated_display.endswith("|"):
                                truncated_display = truncated_display[:-1] + "|"
                            display_line = truncated_display
                        
                        stdscr.addstr(y, 1, display_line, curses.color_pair(8))
                        y += 1
            
            # Bottom border
            stdscr.addstr(y, 1, border_line, curses.color_pair(8))
            y += 1
        except:
            pass
        
        return y
    
    def _get_display_width(self, text: str) -> int:
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
    
    def _render_table(self, stdscr, y: int, table_lines: List[str], width: int):
        """Render table with proper border and line wrapping"""
        try:
            parser = MarkdownParser("")
            table_data = parser.parse_table(table_lines)
            
            if not table_data:
                return y
            
            header = table_data['header']
            rows = table_data['rows']
            
            # 1. Get terminal dimensions (width is already provided)
            # 2. Calculate column widths based on content, considering Chinese characters
            col_widths = [self._get_display_width(h) for h in header]
            for row in rows:
                for i, cell in enumerate(row):
                    if i < len(col_widths):
                        col_widths[i] = max(col_widths[i], self._get_display_width(cell))
            
            # 3. Adjust column widths to fit terminal width
            # Add padding for better rendering (1 character on each side)
            padding = 1  # 1 character padding on each side
            # Calculate effective width, leaving 2 characters margin on each side
            effective_width = width - 4
            
            # Calculate total required width including borders and separators
            # Borders: 2 characters (left and right)
            # Separators: len(col_widths) - 1 characters
            border_width = 2 + (len(col_widths) - 1)
            total_content_width = effective_width - border_width
            
            if total_content_width > 0:
                # Add padding to column widths
                padded_col_widths = [w + (padding * 2) for w in col_widths]
                total_padded_width = sum(padded_col_widths)
                
                if total_padded_width > total_content_width:
                    # Scale columns proportionally
                    total_col_width = sum(col_widths)
                    new_col_widths = []
                    # Calculate minimum width per column
                    min_width = max(4, int(total_content_width / len(col_widths)))
                    for w in col_widths:
                        # Calculate proportional width
                        proportional_width = int((w / total_col_width) * (total_content_width - (padding * 2 * len(col_widths))))
                        # Ensure minimum width
                        new_width = max(min_width - (padding * 2), proportional_width)
                        new_width = max(2, new_width)  # Ensure minimum content width
                        new_col_widths.append(new_width)
                    col_widths = new_col_widths
            
            # 4. Process cells for line wrapping
            # Wrap header cells
            header_lines = self._wrap_table_cells(header, col_widths)
            # Wrap all row cells
            wrapped_rows = []
            for row in rows:
                wrapped_rows.append(self._wrap_table_cells(row, col_widths))
            
            # 5. Generate rendering conditions and render
            # Draw top border
            top_border = "┌"
            for i, w in enumerate(col_widths):
                top_border += "─" * w
                if i < len(col_widths) - 1:
                    top_border += "┬"
            top_border += "┐"
            stdscr.addstr(y, 0, top_border[:width-1], curses.color_pair(9))
            y += 1
            
            # Draw header
            for line_idx in range(len(header_lines[0])):
                header_row = "│"
                for i, lines in enumerate(header_lines):
                    line = lines[line_idx] if line_idx < len(lines) else ""
                    # Add padding around cell content, but ensure it fits
                    padding = 1
                    max_content_width = col_widths[i] - (padding * 2)
                    # Calculate display width of line
                    line_width = self._get_display_width(line)
                    if line_width > max_content_width:
                        # Truncate line to fit
                        truncated_line = ""
                        current_width = 0
                        for char in line:
                            char_width = self._get_display_width(char)
                            if current_width + char_width > max_content_width:
                                break
                            truncated_line += char
                            current_width += char_width
                        line = truncated_line
                    padded_line = f" {line} "
                    # Calculate padding needed based on display width
                    display_width = self._get_display_width(padded_line)
                    padding_needed = col_widths[i] - display_width
                    if padding_needed > 0:
                        padded_line += " " * padding_needed
                    header_row += padded_line
                    header_row += "│"
                stdscr.addstr(y, 0, header_row[:width-1], curses.color_pair(9) | curses.A_BOLD)
                y += 1
            
            # Draw separator
            separator = "├"
            for i, w in enumerate(col_widths):
                separator += "─" * w
                if i < len(col_widths) - 1:
                    separator += "┼"
            separator += "┤"
            stdscr.addstr(y, 0, separator[:width-1], curses.color_pair(9))
            y += 1
            
            # Draw rows
            for idx, wrapped_row in enumerate(wrapped_rows):
                for line_idx in range(len(wrapped_row[0])):
                    row_str = "│"
                    for i, lines in enumerate(wrapped_row):
                        line = lines[line_idx] if line_idx < len(lines) else ""
                        # Add padding around cell content, but ensure it fits
                        padding = 1
                        max_content_width = col_widths[i] - (padding * 2)
                        # Calculate display width of line
                        line_width = self._get_display_width(line)
                        if line_width > max_content_width:
                            # Truncate line to fit
                            truncated_line = ""
                            current_width = 0
                            for char in line:
                                char_width = self._get_display_width(char)
                                if current_width + char_width > max_content_width:
                                    break
                                truncated_line += char
                                current_width += char_width
                            line = truncated_line
                        padded_line = f" {line} "
                        # Calculate padding needed based on display width
                        display_width = self._get_display_width(padded_line)
                        padding_needed = col_widths[i] - display_width
                        if padding_needed > 0:
                            padded_line += " " * padding_needed
                        row_str += padded_line
                        row_str += "│"
                    stdscr.addstr(y, 0, row_str[:width-1], curses.color_pair(9))
                    y += 1
                
                # Draw separator between rows (except last row)
                if idx < len(wrapped_rows) - 1:
                    row_sep = "├"
                    for i, w in enumerate(col_widths):
                        row_sep += "─" * w
                        if i < len(col_widths) - 1:
                            row_sep += "┼"
                    row_sep += "┤"
                    stdscr.addstr(y, 0, row_sep[:width-1], curses.color_pair(9))
                    y += 1
            
            # Draw bottom border
            bottom_border = "└"
            for i, w in enumerate(col_widths):
                bottom_border += "─" * w
                if i < len(col_widths) - 1:
                    bottom_border += "┴"
            bottom_border += "┘"
            stdscr.addstr(y, 0, bottom_border[:width-1], curses.color_pair(9))
            y += 1
        except Exception as e:
            # If table rendering fails, just display the table lines as text
            for line in table_lines:
                try:
                    stdscr.addstr(y, 0, line[:width-1])
                    y += 1
                except:
                    pass
        
        return y
    
    def _wrap_table_cells(self, cells: List[str], col_widths: List[int]) -> List[List[str]]:
        """Wrap table cells into multiple lines based on column widths"""
        wrapped_cells = []
        max_lines = 1
        
        # Wrap each cell and determine maximum number of lines
        for i, cell in enumerate(cells):
            if i < len(col_widths):
                # Use full column width for wrapping (padding is added during rendering)
                width = col_widths[i]
                lines = []
                words = cell.split()
                current_line = []
                current_length = 0
                
                for word in words:
                    word_width = self._get_display_width(word)
                    if current_length + word_width + 1 <= width:
                        current_line.append(word)
                        current_length += word_width + 1
                    else:
                        if current_line:
                            lines.append(' '.join(current_line))
                        # If word is longer than width, split it
                        if word_width > width:
                            # Split word by characters, considering display width
                            current_word = ''
                            current_word_width = 0
                            for char in word:
                                char_width = self._get_display_width(char)
                                if current_word_width + char_width > width:
                                    lines.append(current_word)
                                    current_word = char
                                    current_word_width = char_width
                                else:
                                    current_word += char
                                    current_word_width += char_width
                            if current_word:
                                lines.append(current_word)
                            current_line = []
                            current_length = 0
                        else:
                            current_line = [word]
                            current_length = word_width + 1
                
                if current_line:
                    lines.append(' '.join(current_line))
                
                # Ensure we have at least one line
                if not lines:
                    lines.append('')
                
                wrapped_cells.append(lines)
                max_lines = max(max_lines, len(lines))
            else:
                wrapped_cells.append([cell])
        
        # Pad all cells to have the same number of lines
        for i, lines in enumerate(wrapped_cells):
            while len(lines) < max_lines:
                lines.append('')
        
        return wrapped_cells
