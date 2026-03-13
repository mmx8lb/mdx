"""Table renderer"""

import curses
from typing import List, Dict, Any
from ..utils.terminal import get_display_width

class TableRenderer:
    """Table renderer"""
    
    def __init__(self, theme='monokai'):
        """Initialize table renderer"""
        self.theme = theme
    
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
    
    def render(self, stdscr, y: int, table_lines: List[str], width: int, is_current_result: bool = False, search_term: str = "") -> int:
        """Render table with proper border and line wrapping"""
        try:
            from ..parser import MarkdownParser
            parser = MarkdownParser("")
            table_data = parser.parse_table(table_lines)
            
            if not table_data:
                return y
            
            header = table_data['header']
            rows = table_data['rows']
            
            # 1. Get terminal dimensions (width is already provided)
            # 2. Calculate column widths based on content, considering Chinese characters
            col_widths = [get_display_width(h) for h in header]
            for row in rows:
                for i, cell in enumerate(row):
                    if i < len(col_widths):
                        col_widths[i] = max(col_widths[i], get_display_width(cell))
            
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
                    line_width = get_display_width(line)
                    if line_width > max_content_width:
                        # Truncate line to fit
                        truncated_line = ""
                        current_width = 0
                        for char in line:
                            char_width = get_display_width(char)
                            if current_width + char_width > max_content_width:
                                break
                            truncated_line += char
                            current_width += char_width
                        line = truncated_line
                    padded_line = f" {line} "
                    # Calculate padding needed based on display width
                    display_width = get_display_width(padded_line)
                    padding_needed = col_widths[i] - display_width
                    if padding_needed > 0:
                        padded_line += " " * padding_needed
                    header_row += padded_line
                    header_row += "│"
                if is_current_result and search_term:
                    # Highlight search term in current result
                    self._highlight_search_term(stdscr, y, 0, header_row[:width-1], search_term, curses.color_pair(9) | curses.A_BOLD)
                else:
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
                        line_width = get_display_width(line)
                        if line_width > max_content_width:
                            # Truncate line to fit
                            truncated_line = ""
                            current_width = 0
                            for char in line:
                                char_width = get_display_width(char)
                                if current_width + char_width > max_content_width:
                                    break
                                truncated_line += char
                                current_width += char_width
                            line = truncated_line
                        padded_line = f" {line} "
                        # Calculate padding needed based on display width
                        display_width = get_display_width(padded_line)
                        padding_needed = col_widths[i] - display_width
                        if padding_needed > 0:
                            padded_line += " " * padding_needed
                        row_str += padded_line
                        row_str += "│"
                    if is_current_result and search_term:
                        # Highlight search term in current result
                        self._highlight_search_term(stdscr, y, 0, row_str[:width-1], search_term, curses.color_pair(9))
                    else:
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
                    word_width = get_display_width(word)
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
                                char_width = get_display_width(char)
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