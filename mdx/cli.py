#!/usr/bin/env python3
"""
MDX - A beautiful Markdown viewer for terminal with code execution support
Uses curses for smooth rendering
"""

import os
import sys
import subprocess
import curses
import shutil
from pathlib import Path
from typing import List, Tuple, Optional
import re


class CodeBlock:
    """Represents a code block in markdown"""
    def __init__(self, language: str, code: str, line_number: int):
        self.language = language
        self.code = code
        self.line_number = line_number


class MDXViewer:
    """Main viewer class with curses rendering"""
    
    def __init__(self, filepath: str, execute: bool = False, theme: str = "monokai"):
        self.filepath = Path(filepath)
        if not self.filepath.exists():
            print(f"Error: File not found: {filepath}")
            sys.exit(1)
        
        self.execute = execute
        self.theme = theme
        self.content = self.filepath.read_text()
        self.lines = self.content.split('\n')
        self.code_blocks: List[CodeBlock] = []
        self._extract_code_blocks()
        
        # Remove code blocks from display lines
        self.display_lines = self._remove_code_blocks_from_lines(self.lines)
        
        # Cache
        self._word_count = len(self.content.split())
        
        # Scroll position
        self.scroll_offset = 0
        
        # Search state
        self.search_term = ""
        self.search_matches: List[int] = []
        self.search_current = 0
    
    def _extract_code_blocks(self):
        """Extract all code blocks"""
        in_code_block = False
        current_lang = ""
        current_code = []
        start_line = 0
        
        for i, line in enumerate(self.lines):
            stripped = line.strip()
            if stripped.startswith('```'):
                if not in_code_block:
                    in_code_block = True
                    current_lang = stripped[3:].strip() or "text"
                    current_code = []
                    start_line = i + 1
                else:
                    in_code_block = False
                    self.code_blocks.append(CodeBlock(current_lang, '\n'.join(current_code), start_line))
                    current_lang = ""
                    current_code = []
            elif in_code_block:
                current_code.append(line)
    
    def _remove_code_blocks_from_lines(self, lines: List[str]) -> List[str]:
        """Remove code blocks from lines"""
        result = []
        in_block = False
        
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('```'):
                in_block = not in_block
                continue
            if not in_block:
                result.append(line)
        
        return result
    
    def _colorize_line(self, line: str, width: int):
        """Parse markdown line and return colored segments
        Returns: [(text, curses_attr), ...]
        """
        segments = []
        stripped = line.strip()
        
        # Heading (# ## ###)
        if stripped.startswith('######'):
            title = stripped[6:].strip()  # Remove ######
            return [(title[:width], curses.A_BOLD | curses.color_pair(5))]
        elif stripped.startswith('#####'):
            title = stripped[5:].strip()
            return [(title[:width], curses.A_BOLD | curses.color_pair(4))]
        elif stripped.startswith('####'):
            title = stripped[4:].strip()
            return [(title[:width], curses.A_BOLD | curses.color_pair(3))]
        elif stripped.startswith('###'):
            title = stripped[3:].strip()
            return [(title[:width], curses.A_BOLD | curses.color_pair(2))]
        elif stripped.startswith('##'):
            title = stripped[2:].strip()
            return [(title[:width], curses.A_BOLD | curses.color_pair(1))]
        elif stripped.startswith('#'):
            title = stripped[1:].strip()
            return [(title[:width], curses.A_BOLD | curses.color_pair(1))]
        
        # Horizontal rule (--- or ***)
        if stripped.startswith('---') or stripped.startswith('***'):
            return [('─' * (width - 1), curses.A_DIM)]
        
        # List items (- * 1. )
        if stripped.startswith('- ') or stripped.startswith('* '):
            indent = len(line) - len(line.lstrip())
            content = line.lstrip()[2:]  # Remove "- " or "* "
            return [
                (line[:indent + 2], curses.color_pair(6)),
                (content[:width - indent - 2], 0)
            ]
        
        # Numbered list (1. 2. )
        import re
        num_match = re.match(r'^(\s*)(\d+)\.\s+(.*)$', line)
        if num_match:
            indent = len(num_match.group(1))
            num = num_match.group(2)
            rest = num_match.group(3)
            return [
                (line[:indent] + num + ".", curses.color_pair(6)),
                (rest[:width - indent - len(num) - 2], 0)
            ]
        
        # Table separator (|---|---|)
        if stripped.startswith('|') and all(c in '|-' for c in stripped.replace('|', '')):
            return [('─' * (width - 1), curses.A_DIM)]
        
        # Table (| col | col |)
        if '|' in line and not stripped.startswith('|'):
            parts = line.split('|')
            result = []
            x = 0
            for j, part in enumerate(parts):
                if j > 0:
                    result.append(('|', 0))
                attr = curses.color_pair(7) if 0 < j < len(parts) - 1 else 0
                result.append((part, attr))
            return result
        
        # Bold (**text**) and Italic (*text*)
        if '**' in line or '*' in line:
            segments = []
            last_end = 0
            # Find all **text**
            for match in re.finditer(r'\*\*(.+?)\*\*', line):
                if match.start() > last_end:
                    segments.append((line[last_end:match.start()], 0))
                segments.append((match.group(1), curses.A_BOLD))  # Show text without **
                last_end = match.end()
            # Find single *text* (not **)
            for match in re.finditer(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', line):
                if match.start() > last_end:
                    segments.append((line[last_end:match.start()], 0))
                segments.append((match.group(1), curses.A_ITALIC))
                last_end = match.end()
            if last_end < len(line):
                segments.append((line[last_end:], 0))
            if segments:
                return segments
        
        # Default
        return [(line[:width], 0)]
    
    def _get_screen_size(self):
        """Get current terminal size"""
        try:
            return shutil.get_terminal_size()
        except:
            return os.terminal_size((80, 24))
    
    def render(self, stdscr, force=False):
        """Render using curses - optimized for smooth scrolling"""
        # Get current screen size
        size = self._get_screen_size()
        height, width = size.lines, size.columns
        
        # Check if resize needed
        if not hasattr(self, '_last_height') or self._last_height != height:
            self._last_height = height
            force = True
        
        # Only clear if forced (first draw or resize)
        if force:
            stdscr.clear()
        
        # Reserve space for header (3 lines) and footer
        content_height = height - 5
        
        total_lines = len(self.display_lines)
        start = self.scroll_offset
        end = min(start + content_height, total_lines)
        
        # Draw header
        title = self.filepath.name[:width-10]
        stdscr.addstr(0, 0, " " * (width - 1))
        stdscr.addstr(0, 0, f" {title} ", curses.A_REVERSE | curses.A_BOLD)
        
        info = f" {self._word_count} words | {start+1}-{end}/{total_lines} | j/k:滚动 q:退出 /:搜索 t:目录 "
        stdscr.addstr(1, 0, " " * (width - 1))
        stdscr.addstr(1, 0, info[:width-1], curses.A_DIM)
        
        # Draw separator
        sep = "─" * (width - 1)
        stdscr.addstr(2, 0, sep, curses.A_DIM)
        
        # Erase content area only (not whole screen)
        for i in range(3, height - 2):
            stdscr.addstr(i, 0, " " * (width - 1))
        
        # Draw content with colors
        for i in range(start, end):
            line_idx = i - start + 3
            if line_idx >= height - 2:
                break
            
            line = self.display_lines[i]
            if not line:
                continue
            
            # Get colored segments
            segments = self._colorize_line(line, width)
            
            x = 0
            for text, attr in segments:
                if x >= width - 1:
                    break
                text = text[:width - x - 1]
                try:
                    stdscr.addstr(line_idx, x, text, attr)
                except:
                    pass
                x += len(text)
        
        # Progress bar
        if total_lines > content_height:
            bar_width = min(40, width - 10)
            progress = start / (total_lines - content_height)
            filled = int(bar_width * progress)
            bar = "█" * filled + "░" * (bar_width - filled)
            prog = f"│{bar}│ {int(progress*100)}%"
            stdscr.addstr(height - 2, 0, prog, curses.A_DIM)
        
        # Use noutrefresh for double buffering
        stdscr.noutrefresh()
        curses.doupdate()
    
    def scroll_down(self, lines: int = 1):
        """Scroll down"""
        size = self._get_screen_size()
        content_height = size.lines - 5
        max_scroll = max(0, len(self.display_lines) - content_height)
        self.scroll_offset = min(max_scroll, self.scroll_offset + lines)
    
    def scroll_up(self, lines: int = 1):
        """Scroll up"""
        self.scroll_offset = max(0, self.scroll_offset - lines)
    
    def scroll_to_top(self):
        """Scroll to top"""
        self.scroll_offset = 0
    
    def scroll_to_bottom(self):
        """Scroll to bottom"""
        size = self._get_screen_size()
        content_height = size.lines - 5
        max_scroll = max(0, len(self.display_lines) - content_height)
        self.scroll_offset = max_scroll
    
    def do_search(self, stdscr):
        """Search dialog"""
        stdscr.addstr(curses.LINES - 1, 0, "/" + " " * (curses.COLS - 2), curses.A_REVERSE)
        stdscr.clrtoeol()
        curses.echo()
        
        stdscr.addstr(curses.LINES - 1, 1, "/")
        search_term = stdscr.getstr(curses.LINES - 1, 2, 50).decode('utf-8')
        
        curses.noecho()
        
        if search_term:
            self.search_term = search_term
            self.search_matches = []
            for i, line in enumerate(self.display_lines, 1):
                if search_term.lower() in line.lower():
                    self.search_matches.append(i)
            
            if self.search_matches:
                self.search_current = 0
                self.scroll_offset = max(0, self.search_matches[0] - 1)
    
    def next_search(self):
        """Next search match"""
        if self.search_matches:
            self.search_current = (self.search_current + 1) % len(self.search_matches)
            self.scroll_offset = max(0, self.search_matches[self.search_current] - 1)
    
    def prev_search(self):
        """Previous search match"""
        if self.search_matches:
            self.search_current = (self.search_current - 1) % len(self.search_matches)
            self.scroll_offset = max(0, self.search_matches[self.search_current] - 1)
    
    def show_toc(self, stdscr):
        """Show table of contents"""
        toc = []
        for i, line in enumerate(self.lines):
            match = re.match(r'^(#{1,6})\s+(.+)$', line)
            if match:
                level = len(match.group(1))
                title = match.group(2).strip()
                toc.append((i + 1, level, title))
        
        stdscr.clear()
        height, width = stdscr.getmaxyx()
        
        stdscr.addstr(0, 0, " Table of Contents ", curses.A_REVERSE | curses.A_BOLD)
        stdscr.addstr(1, 0, "─" * (width - 1), curses.A_DIM)
        
        for i, (line_num, level, title) in enumerate(toc[:height - 4]):
            indent = "  " * (level - 1)
            text = f"{line_num:4d}  {indent}{title}"[:width-1]
            stdscr.addstr(i + 2, 0, text)
        
        stdscr.addstr(height - 1, 0, " Press any key to continue... ", curses.A_REVERSE)
        stdscr.refresh()
        stdscr.getch()
    
    def show_help(self, stdscr):
        """Show help"""
        stdscr.clear()
        height, width = stdscr.getmaxyx()
        
        help_text = """
 MDX Help
 ──────────────────────
 j / ↓      向下滚动一行
 k / ↑      向上滚动一行
 空格 / PgDn  向下一页
 b / PgUp    向上一页
 g           跳转开头
 G           跳转结尾
 /           搜索
 n           下一个搜索
 t           目录
 q           退出
 ──────────────────────
        """
        
        for i, line in enumerate(help_text.split('\n')):
            if i < height - 1:
                stdscr.addstr(i + 1, 0, line[:width-1])
        
        stdscr.addstr(height - 1, 0, " Press any key to continue... ", curses.A_REVERSE)
        stdscr.refresh()
        stdscr.getch()
    
    def execute_code_blocks(self, stdscr):
        """Execute code blocks"""
        height, width = stdscr.getmaxyx()
        
        stdscr.clear()
        stdscr.addstr(0, 0, " Executing Code Blocks ", curses.A_REVERSE | curses.A_BOLD)
        
        row = 2
        for i, block in enumerate(self.code_blocks):
            if row >= height - 3:
                break
            
            stdscr.addstr(row, 0, f"--- Block {i+1}: {block.language} ---")
            row += 1
            
            # Show code
            code_lines = block.code.split('\n')[:5]
            for line in code_lines:
                if row < height - 3:
                    stdscr.addstr(row, 0, f"  {line}"[:width-1])
                    row += 1
            
            # Execute
            result = ""
            if block.language in ["bash", "sh", "shell", ""]:
                try:
                    r = subprocess.run(block.code, shell=True, capture_output=True, text=True, timeout=5)
                    result = r.stdout or r.stderr
                except:
                    result = "Error"
            elif block.language == "python":
                try:
                    r = subprocess.run(["python3", "-c", block.code], capture_output=True, text=True, timeout=5)
                    result = r.stdout or r.stderr
                except:
                    result = "Error"
            
            if result and row < height - 3:
                for line in result.split('\n')[:3]:
                    stdscr.addstr(row, 0, f"  > {line}"[:width-1], curses.A_DIM)
                    row += 1
            row += 1
        
        stdscr.addstr(height - 1, 0, " Press any key to continue... ", curses.A_REVERSE)
        stdscr.refresh()
        stdscr.getch()
    
    def interactive(self, stdscr):
        """Interactive mode with curses"""
        curses.curs_set(0)  # Hide cursor
        stdscr.nodelay(True)  # Non-blocking input
        
        # Initialize colors
        if curses.has_colors():
            curses.start_color()
            curses.use_default_colors()
            # Color pairs: (fg, bg)
            # 1: Cyan for h1
            curses.init_pair(1, curses.COLOR_CYAN, -1)
            # 2: Blue for h2
            curses.init_pair(2, curses.COLOR_BLUE, -1)
            # 3: Green for h3
            curses.init_pair(3, curses.COLOR_GREEN, -1)
            # 4: Yellow for h4
            curses.init_pair(4, curses.COLOR_YELLOW, -1)
            # 5: Red for h5/h6
            curses.init_pair(5, curses.COLOR_RED, -1)
            # 6: Magenta for list bullets
            curses.init_pair(6, curses.COLOR_MAGENTA, -1)
            # 7: Cyan for table content
            curses.init_pair(7, curses.COLOR_CYAN, -1)
        
        self.render(stdscr, force=True)
        
        while True:
            # Check for terminal resize
            size = self._get_screen_size()
            
            try:
                key = stdscr.getch()
                if key == -1:
                    continue
                
                # Handle special keys
                if key == ord('q'):
                    break
                elif key in [ord('j'), ord('J'), curses.KEY_DOWN]:
                    self.scroll_down(1)
                elif key in [ord('k'), ord('K'), curses.KEY_UP]:
                    self.scroll_up(1)
                elif key == ord(' '):
                    size = self._get_screen_size()
                    self.scroll_down(size.lines - 5)
                elif key in [ord('b'), ord('B'), curses.KEY_PPAGE]:
                    size = self._get_screen_size()
                    self.scroll_up(size.lines - 5)
                elif key in [ord('g')]:
                    self.scroll_to_top()
                elif key in [ord('G')]:
                    self.scroll_to_bottom()
                elif key == ord('/'):
                    self.do_search(stdscr)
                elif key in [ord('n'), ord('N')]:
                    if key == ord('n'):
                        self.next_search()
                    else:
                        self.prev_search()
                elif key in [ord('t'), ord('T')]:
                    self.show_toc(stdscr)
                elif key in [ord('h'), ord('H')]:
                    self.show_help(stdscr)
                elif key in [ord('e'), ord('E')]:
                    self.execute_code_blocks(stdscr)
                
                self.render(stdscr)
                
            except curses.error:
                pass
        
        curses.endwin()


def main():
    import click
    
    @click.command()
    @click.argument('file', type=click.Path(exists=True))
    @click.option('--execute', '-e', is_flag=True, help='Execute code blocks')
    @click.option('--toc', '-t', is_flag=True, help='Show table of contents')
    @click.option('--theme', '-m', default='monokai', help='Syntax highlighting theme')
    @click.option('--interactive', '-i', is_flag=True, help='Interactive mode')
    @click.option('--search', '-s', type=str, help='Search in file')
    @click.version_option(version='0.6.0', prog_name='mdx')
    def cli(file: str, execute: bool, toc: bool, theme: str, interactive: bool, search: str):
        """
        MDX - A beautiful Markdown viewer for terminal (curses-based)
        
        Use -i for interactive mode (like less)
        """
        viewer = MDXViewer(file, execute=execute, theme=theme)
        
        if search:
            # Search only
            for i, line in enumerate(viewer.display_lines, 1):
                if search.lower() in line.lower():
                    print(f"{i:4d}: {line}")
        elif toc:
            # Show TOC - use rich for pretty display
            try:
                from rich.console import Console
                from rich.table import Table
                console = Console()
                
                toc = []
                for i, line in enumerate(viewer.lines):
                    match = re.match(r'^(#{1,6})\s+(.+)$', line)
                    if match:
                        level = len(match.group(1))
                        title = match.group(2).strip()
                        toc.append((i + 1, level, title))
                
                if toc:
                    table = Table(title="Table of Contents")
                    table.add_column("Line", style="dim", width=6)
                    table.add_column("Title", style="cyan")
                    
                    for line_num, level, title in toc:
                        indent = "  " * (level - 1)
                        table.add_row(str(line_num), f"{indent}{title}")
                    
                    console.print(table)
            except:
                # Fallback
                for i, line in enumerate(viewer.lines):
                    match = re.match(r'^(#{1,6})\s+(.+)$', line)
                    if match:
                        print(f"{i+1}: {match.group(2)}")
        elif interactive:
            # Interactive mode with curses
            def run_interactive(stdscr):
                viewer.interactive(stdscr)
            curses.wrapper(run_interactive)
        else:
            # Default: show all content
            for line in viewer.display_lines:
                if line.strip():
                    print(line)
    
    cli()


if __name__ == '__main__':
    main()
