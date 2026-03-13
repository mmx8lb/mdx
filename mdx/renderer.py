"""Markdown renderer module"""

import curses
from typing import List, Tuple, Dict, Any
from .utils.terminal import get_terminal_size, get_display_width
from .utils.cache import Cache
from .renderers.code_renderer import CodeRenderer
from .renderers.table_renderer import TableRenderer
from .themes.default import AVAILABLE_THEMES


class TerminalRenderer:
    """Terminal renderer for Markdown"""
    
    def __init__(self, theme='monokai'):
        """Initialize terminal renderer"""
        # Get theme from available themes
        self.theme = AVAILABLE_THEMES.get(theme, AVAILABLE_THEMES['monokai'])
        self.cache = Cache(max_size=100)
        self.last_scroll = -1
        self.last_height = 0
        self.last_width = 0
        self.code_renderer = CodeRenderer(theme)
        self.table_renderer = TableRenderer(theme)
    
    def _highlight_search_term(self, stdscr, y, x, text, search_term, default_attr=0):
        """Highlight search term in text"""
        if not search_term:
            stdscr.addstr(y, x, text, default_attr)
            return
        
        import re
        from .utils.terminal import get_display_width
        
        # Find all occurrences of search term
        if search_term.isascii():
            # Case-insensitive search for ASCII
            pattern = re.compile(re.escape(search_term), re.IGNORECASE)
        else:
            # Case-sensitive search for non-ASCII
            pattern = re.compile(re.escape(search_term))
        
        # Find all matches
        matches = list(pattern.finditer(text))
        
        if not matches:
            # No matches found, just display the text
            stdscr.addstr(y, x, text, default_attr)
            return
        
        current_pos = 0
        current_width = 0
        
        for match in matches:
            # Get text before this match
            before_text = text[current_pos:match.start()]
            
            # Calculate display width of text before match
            before_width = get_display_width(before_text)
            
            # Calculate display width of matched text
            matched_text = match.group()
            matched_width = get_display_width(matched_text)
            
            # Add text before match
            if before_text:
                stdscr.addstr(y, x + current_width, before_text, default_attr)
            
            # Add matched text with highlight
            stdscr.addstr(y, x + current_width + before_width, matched_text, curses.A_REVERSE | default_attr)
            
            # Update current position and width
            current_pos = match.end()
            current_width += before_width + matched_width
        
        # Add remaining text
        remaining_text = text[current_pos:]
        if remaining_text:
            stdscr.addstr(y, x + current_width, remaining_text, default_attr)
    
    def render(self, stdscr, parsed_content: List[Tuple[str, Any]], scroll: int = 0, search_term: str = "", search_results: List[int] = [], current_result_index: int = -1, dev_mode: bool = False):
        """Render parsed content to terminal with optimized rendering"""
        curses.curs_set(0)
        
        try:
            # Get screen size
            size = get_terminal_size()
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
                    color_map = {
                        'header1': 1,
                        'header2': 2,
                        'header3': 3,
                        'header4': 4,
                        'header5': 5,
                        'header6': 5,
                        'list': 6,
                        'blockquote': 7,
                        'code': 8,
                        'table': 9,
                        'hr': 10
                    }
                    
                    # Map theme colors to color pairs
                    for name, pair in color_map.items():
                        if name.startswith('header'):
                            level = int(name[-1])
                            fg, bg = self.theme['header'].get(level, (curses.COLOR_WHITE, -1))
                        else:
                            fg, bg = self.theme.get(name, (curses.COLOR_WHITE, -1))
                        
                        try:
                            curses.init_pair(pair, fg, bg)
                        except:
                            pass
                self.colors_initialized = True
            
            # Only clear screen if necessary (e.g., first render or screen size changed)
            if (self.last_height != height or self.last_width != width or 
                self.last_scroll == -1):
                stdscr.clear()
            
            # Content area
            y = 0
            idx = 0
            content_height = height - 1  # 底部只留1行空间
            
            # Clear content area
            for i in range(height - 1):
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
                
                if y >= height - 1:
                    break
                
                try:
                    # Generate cache key
                    cache_key = f"{item_type}:{content}:{width}"
                    
                    # Check if this item is in cache
                    cached_item = self.cache.get(cache_key)
                    
                    # Check if this is a search result
                    is_search_result = idx in search_results and search_results
                    is_current_result = is_search_result and search_results.index(idx) == current_result_index
                    
                    if cached_item:
                        # Use cached rendering
                        for line in cached_item:
                            if y >= height - 1:
                                break
                            try:
                                if is_current_result and search_term:
                                    # Highlight search term in current result
                                    self._highlight_search_term(stdscr, y, 0, line, search_term)
                                else:
                                    stdscr.addstr(y, 0, line)
                                y += 1
                            except:
                                pass
                    else:
                        # Render and cache the item
                        rendered_lines = []
                        if item_type == 'header':
                            level, title = content
                            color_pair = min(level, 5)
                            line = f"{'#' * level} {title}"
                            rendered_lines.append(line)
                            if is_current_result and search_term:
                                # Highlight search term in current result
                                self._highlight_search_term(stdscr, y, 0, line, search_term, curses.color_pair(color_pair) | curses.A_BOLD)
                            else:
                                stdscr.addstr(y, 0, line, curses.color_pair(color_pair) | curses.A_BOLD)
                            y += 1
                        elif item_type == 'list_item':
                            list_type, item_content = content
                            marker = '•' if list_type == 'unordered' else '1.'
                            line = f"  {marker}   {item_content}"
                            rendered_lines.append(line)
                            if is_current_result and search_term:
                                # Highlight search term in current result
                                self._highlight_search_term(stdscr, y, 0, line, search_term)
                            else:
                                stdscr.addstr(y, 2, marker, curses.color_pair(6))
                                stdscr.addstr(y, 5, item_content)
                            y += 1
                        elif item_type == 'blockquote':
                            line = f"  >   {content}"
                            rendered_lines.append(line)
                            if is_current_result and search_term:
                                # Highlight search term in current result
                                self._highlight_search_term(stdscr, y, 0, line, search_term)
                            else:
                                stdscr.addstr(y, 2, '>', curses.color_pair(7))
                                stdscr.addstr(y, 4, content, curses.color_pair(7))
                            y += 1
                        elif item_type == 'code_block':
                            lang, lines = content
                            start_y = y
                            y = self.code_renderer.render(stdscr, y, lang, lines, width, is_current_result, search_term)
                            # For code blocks, we don't cache as they're complex
                        elif item_type == 'table':
                            start_y = y
                            y = self.table_renderer.render(stdscr, y, content, width, is_current_result, search_term)
                            # For tables, we don't cache as they're complex
                        elif item_type == 'hr':
                            line = "─" * (width - 1)
                            rendered_lines.append(line)
                            stdscr.addstr(y, 0, line, curses.color_pair(10))
                            y += 1
                        else:  # text
                            line = content[:width-1]
                            rendered_lines.append(line)
                            if is_current_result and search_term:
                                # Highlight search term in current result
                                self._highlight_search_term(stdscr, y, 0, line, search_term)
                            else:
                                stdscr.addstr(y, 0, line)
                            y += 1
                        
                        # Cache the rendered lines for simple items
                        if rendered_lines and item_type not in ['code_block', 'table']:
                            self.cache.set(cache_key, rendered_lines)
                except Exception as e:
                    # Display error message for debugging
                    try:
                        stdscr.addstr(y, 0, f"Error rendering {item_type}: {str(e)}")
                        y += 1
                    except:
                        pass
                
                idx += 1
            
            # Clear bottom area (only the last line)
            try:
                stdscr.move(height - 1, 0)
                stdscr.clrtoeol()
            except:
                pass
            
            # Progress bar with status
            try:
                # Build status string
                base_status = f" {scroll + 1}-{min(scroll + content_height, total)}/{total} | j/k滚动 q退出 "
                
                # Add search status if applicable
                search_status = ""
                if search_term:
                    if search_results:
                        search_status = f" | 搜索: '{search_term}' ({current_result_index + 1}/{len(search_results)})"
                    else:
                        search_status = f" | 搜索: '{search_term}' (无结果)"
                
                full_status = base_status + search_status
                
                if total > content_height:
                    bar_width = min(40, width - len(full_status) - 10)  # 为状态信息留出空间
                    if bar_width < 10:
                        bar_width = 10  # Minimum bar width
                    prog = scroll / (total - content_height)
                    filled = int(bar_width * prog)
                    bar = "█" * filled + "░" * (bar_width - filled)
                    # 计算状态信息的位置，放在进度条后面
                    status_pos = bar_width + 6  # 进度条宽度 + 边框和空格
                    stdscr.addstr(height - 1, 0, f"│{bar}│ {int(prog * 100)}%", curses.A_DIM)
                    if status_pos < width:
                        # Truncate status if it's too long
                        available_width = width - status_pos
                        if len(full_status) > available_width:
                            full_status = full_status[:available_width - 3] + "..."
                        stdscr.addstr(height - 1, status_pos, full_status, curses.A_DIM)
                else:
                    # 只有状态信息，没有进度条
                    # Truncate status if it's too long
                    if len(full_status) > width:
                        full_status = full_status[:width - 3] + "..."
                    stdscr.addstr(height - 1, 0, full_status, curses.A_DIM)
            except:
                pass
            
            # Refresh only once at the end
            stdscr.refresh()
            
            # Display debug information in development mode
            if dev_mode:
                try:
                    # Calculate debug window size and position
                    debug_width = min(60, width // 2)
                    debug_height = min(15, height // 3)
                    debug_x = width - debug_width - 2
                    debug_y = 2
                    
                    # Create debug window
                    debug_win = curses.newwin(debug_height, debug_width, debug_y, debug_x)
                    debug_win.box()
                    debug_win.addstr(0, 2, " Debug Information ", curses.A_BOLD)
                    
                    # Display debug information
                    debug_lines = [
                        f"Scroll: {scroll}",
                        f"Search term: {repr(search_term)}",
                        f"Search results: {search_results}",
                        f"Current result: {current_result_index}",
                        f"Total results: {len(search_results)}",
                        f"Terminal size: {width}x{height}",
                        f"Content items: {len(parsed_content)}"
                    ]
                    
                    for i, line in enumerate(debug_lines):
                        if i + 1 < debug_height - 1:
                            try:
                                debug_win.addstr(i + 1, 2, line[:debug_width - 4])
                            except:
                                pass
                    
                    # Refresh debug window
                    debug_win.refresh()
                except:
                    pass
            
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
