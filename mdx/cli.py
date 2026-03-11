#!/usr/bin/env python3
"""
MDX - A beautiful Markdown viewer for terminal with code execution support
"""

import os
import sys
import subprocess
import shlex
from pathlib import Path
from typing import List, Tuple, Optional
import re
import tty
import termios

try:
    from rich.console import Console
    from rich.syntax import Syntax
    from rich.markdown import Markdown, MarkdownElement
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from rich import box
    from rich.style import Style
    from rich.theme import Theme
except ImportError:
    print("Error: rich library not found. Install with: pip install rich")
    sys.exit(1)

console = Console()


class CodeBlock:
    """Represents a code block in markdown"""
    def __init__(self, language: str, code: str, line_number: int):
        self.language = language
        self.code = code
        self.line_number = line_number


class MDXViewer:
    """Main viewer class with proper markdown rendering"""
    
    def __init__(self, filepath: str, execute: bool = False, theme: str = "monokai"):
        self.filepath = Path(filepath)
        if not self.filepath.exists():
            console.print(f"[red]Error: File not found: {filepath}[/red]")
            sys.exit(1)
        
        self.execute = execute
        self.theme = theme
        self.content = self.filepath.read_text()
        self.lines = self.content.split('\n')
        self.code_blocks: List[CodeBlock] = []
        self._extract_code_blocks()
        
        # Pagination state
        self.current_page = 0
        self.lines_per_page = console.height - 12
    
    def _extract_code_blocks(self):
        """Extract all code blocks with their language"""
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
    
    def _remove_code_blocks(self, content: str) -> str:
        """Remove code blocks from content for display"""
        lines = content.split('\n')
        result = []
        in_block = False
        
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('```'):
                in_block = not in_block
                continue
            if not in_block:
                result.append(line)
        
        return '\n'.join(result)
    
    def render(self, start_line: int = 0):
        """Render the markdown file with proper formatting"""
        console.clear()
        
        # Calculate pagination
        total_pages = max(1, (len(self.lines) + self.lines_per_page - 1) // self.lines_per_page)
        self.current_page = min(start_line // self.lines_per_page, total_pages - 1)
        
        # Get page content
        start = self.current_page * self.lines_per_page
        end = min(start + self.lines_per_page, len(self.lines))
        page_lines = self.lines[start:end]
        
        # Print header
        word_count = len(self.content.split())
        console.print(Panel(
            f"[bold cyan]{self.filepath.name}[/bold cyan]",
            subtitle=f"📄 {word_count} words | {len(self.code_blocks)} code blocks | "
                    f"Page {self.current_page + 1}/{total_pages} | Lines {start+1}-{end}",
            box=box.DOUBLE,
            style="cyan"
        ))
        console.print()
        
        # Render page content
        page_content = '\n'.join(page_lines)
        content_without_code = self._remove_code_blocks(page_content)
        
        md = Markdown(content_without_code, code_theme=self.theme)
        console.print(md)
        
        # Show progress bar
        self._render_progress_bar(start, end)
        
        # Show navigation hint
        console.print()
        console.print("[dim]↑↓/j/k: 翻页 | g/G: 开头/结尾 | t: 目录 | /: 搜索 | q: 退出 | n: 下一个搜索 | e: 执行代码块[/dim]")
        
        if self.execute and self.code_blocks:
            self._execute_code_blocks()
    
    def _render_progress_bar(self, start: int, end: int):
        """Render a progress bar"""
        total = len(self.lines)
        bar_width = 30
        filled = int(bar_width * end / total)
        bar = "█" * filled + "░" * (bar_width - filled)
        console.print(f"[dim]|{bar}| {start+1}-{end}/{total}[/dim]")
    
    def _render_content(self, start_line: int = 0):
        """Render markdown content with proper styling"""
        content = self._remove_code_blocks(self.content)
        md = Markdown(content, code_theme=self.theme)
        console.print(md)
    
    def show_toc(self):
        """Show table of contents"""
        toc = []
        for i, line in enumerate(self.lines):
            match = re.match(r'^(#{1,6})\s+(.+)$', line)
            if match:
                level = len(match.group(1))
                title = match.group(2).strip()
                toc.append((i + 1, level, title))
        
        if not toc:
            console.print("[dim]No headings found[/dim]")
            return
        
        table = Table(title="📑 Table of Contents", box=box.ROUNDED)
        table.add_column("Line", style="dim", width=6)
        table.add_column("Title", style="cyan")
        
        for line_num, level, title in toc:
            indent = "  " * (level - 1)
            table.add_row(str(line_num), f"{indent}{title}")
        
        console.print(table)
    
    def show_help(self):
        """Show help message"""
        help_text = """
[bold cyan]╭─ MDX 快捷键 ─╮[/bold cyan]
│                    │
│ [yellow]翻页:[/yellow]          │
│   ↑/k 或 j    上一页          │
│   ↓/l 或 k   下一页          │
│   g           开头            │
│   G           结尾            │
│                    │
│ [yellow]导航:[/yellow]          │
│   t            目录            │
│   /            搜索            │
│   n            下一个搜索      │
│   p            上一个搜索      │
│   :N           跳转到第N行    │
│                    │
│ [yellow]其他:[/yellow]          │
│   e            执行代码块      │
│   h            帮助            │
│   q            退出            │
│ [cyan]╰───────────────────╯[/cyan]
        """
        console.print(help_text)
    
    def _execute_code_blocks(self):
        """Execute all code blocks"""
        console.print()
        console.print(Panel("[bold yellow]⚡ Executing Code Blocks[/bold yellow]", box=box.ROUNDED))
        
        for i, block in enumerate(self.code_blocks, 1):
            console.print(f"\n[cyan]--- Code Block {i}: {block.language} (line {block.line_number}) ---[/cyan]")
            
            syntax = Syntax(
                block.code, 
                block.language if block.language != "text" else "bash", 
                theme=self.theme,
                line_numbers=False
            )
            console.print(syntax)
            
            if block.language in ["bash", "sh", "shell", ""]:
                self._run_command(block.code)
            elif block.language == "python":
                self._run_python(block.code)
            else:
                console.print(f"[dim]⚠ Skipping {block.language} (not executable)[/dim]")
    
    def _run_command(self, cmd: str):
        """Run shell command"""
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=30
            )
            if result.stdout:
                console.print(f"[green]{result.stdout}[/green]")
            if result.stderr:
                console.print(f"[red]{result.stderr}[/red]")
            if not result.stdout and not result.stderr:
                console.print("[dim]✓ Command executed successfully[/dim]")
        except subprocess.TimeoutExpired:
            console.print("[red]⏱ Command timeout[/red]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
    
    def _run_python(self, code: str):
        """Run Python code"""
        try:
            result = subprocess.run(
                ["python3", "-c", code], capture_output=True, text=True, timeout=30
            )
            if result.stdout:
                console.print(f"[green]{result.stdout}[/green]")
            if result.stderr:
                console.print(f"[red]{result.stderr}[/red]")
            if not result.stdout and not result.stderr:
                console.print("[dim]✓ Code executed successfully[/dim]")
        except subprocess.TimeoutExpired:
            console.print("[red]⏱ Code timeout[/red]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
    
    def _get_key(self):
        """Get a single key press"""
        try:
            old_settings = termios.tcgetattr(sys.stdin)
            try:
                tty.setcbreak(sys.stdin.fileno())
                key = sys.stdin.read(1)
            finally:
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
            return key
        except:
            return ""
    
    def interactive(self):
        """Interactive mode with full navigation"""
        self.lines_per_page = console.height - 12
        search_matches = []
        current_search_idx = 0
        
        while True:
            self.render(self.current_page * self.lines_per_page)
            
            try:
                console.print()
                key = console.input("\n[cyan]>[/cyan] ")
                
                if not key:
                    continue
                    
                key = key.strip().lower()
                
                if key == 'q' or key == 'quit':
                    break
                elif key in ['k', '上', '\x1b[A'] or key == '' and False:  # Up - handled below
                    self.current_page = max(0, self.current_page - 1)
                elif key in ['j', '下', '\x1b[B']:  # Down
                    total_pages = (len(self.lines) + self.lines_per_page - 1) // self.lines_per_page
                    self.current_page = min(total_pages - 1, self.current_page + 1)
                elif key == 'g':
                    self.current_page = 0
                elif key == 'G':
                    total_pages = (len(self.lines) + self.lines_per_page - 1) // self.lines_per_page
                    self.current_page = total_pages - 1
                elif key == 't' or key == 'toc':
                    self.show_toc()
                    console.input("\n[dim]Press Enter to continue...[/dim]")
                elif key == 'h' or key == 'help':
                    self.show_help()
                    console.input("\n[dim]Press Enter to continue...[/dim]")
                elif key == '/':
                    search_term = console.input("[cyan]Search: [/cyan]")
                    if search_term:
                        search_matches = []
                        for i, line in enumerate(self.lines, 1):
                            if search_term.lower() in line.lower():
                                search_matches.append(i)
                        if search_matches:
                            console.print(f"[green]Found {len(search_matches)} matches[/green]")
                            current_search_idx = 0
                            self.current_page = (search_matches[0] - 1) // self.lines_per_page
                        else:
                            console.print(f"[red]No matches found[/red]")
                            console.input("\n[dim]Press Enter to continue...[/dim]")
                elif key == 'n' and search_matches:
                    current_search_idx = (current_search_idx + 1) % len(search_matches)
                    self.current_page = (search_matches[current_search_idx] - 1) // self.lines_per_page
                    console.print(f"[dim]Match {current_search_idx + 1}/{len(search_matches)}[/dim]")
                elif key == 'p' and search_matches:
                    current_search_idx = (current_search_idx - 1) % len(search_matches)
                    self.current_page = (search_matches[current_search_idx] - 1) // self.lines_per_page
                    console.print(f"[dim]Match {current_search_idx + 1}/{len(search_matches)}[/dim]")
                elif key == 'e':
                    self._execute_code_blocks()
                    console.input("\n[dim]Press Enter to continue...[/dim]")
                elif key.startswith(':') and key[1:].isdigit():
                    line_num = int(key[1:])
                    if 1 <= line_num <= len(self.lines):
                        self.current_page = (line_num - 1) // self.lines_per_page
                else:
                    pass
                    
            except (KeyboardInterrupt, EOFError):
                break
        
        console.print("[dim]Goodbye![/dim]")
    
    def _search(self, term: str):
        """Search for term in file"""
        if not term:
            return
        
        matches = []
        for i, line in enumerate(self.lines, 1):
            if term.lower() in line.lower():
                matches.append((i, line.strip()))
        
        if matches:
            console.print(f"\n[cyan]Found {len(matches)} matches:[/cyan]")
            for line_num, line in matches[:20]:
                console.print(f"[dim]{line_num:4d}:[/dim] {line}")
        else:
            console.print(f"\n[red]No matches found for '{term}'[/red]")
    
    def _show_line(self, line_num: int):
        """Show specific line with context"""
        start = max(0, line_num - 5)
        end = min(len(self.lines), line_num + 5)
        
        for i in range(start, end):
            prefix = ">>> " if i == line_num - 1 else "    "
            console.print(f"[dim]{i+1:4d}:[/dim] {prefix}{self.lines[i]}")


def main():
    import click
    
    @click.command()
    @click.argument('file', type=click.Path(exists=True))
    @click.option('--execute', '-e', is_flag=True, help='Execute code blocks')
    @click.option('--toc', '-t', is_flag=True, help='Show table of contents')
    @click.option('--line', '-l', type=int, help='Jump to specific line')
    @click.option('--theme', '-m', default='monokai', help='Syntax highlighting theme')
    @click.option('--interactive', '-i', is_flag=True, help='Interactive mode')
    @click.option('--search', '-s', type=str, help='Search in file')
    @click.option('--page', '-p', type=int, help='Go to specific page')
    @click.version_option(version='0.3.0', prog_name='mdx')
    def cli(file: str, execute: bool, toc: bool, line: int, theme: str, interactive: bool, search: str, page: int):
        """
        MDX - A beautiful Markdown viewer for terminal
        
        Example:
            mdx README.md
            mdx README.md --execute
            mdx README.md --toc
            mdx README.md -i
        """
        viewer = MDXViewer(file, execute=execute, theme=theme)
        
        if search:
            viewer._search(search)
        elif toc:
            viewer.show_toc()
        elif interactive:
            viewer.interactive()
        elif line:
            lines_per_page = console.height - 12
            viewer.current_page = (line - 1) // lines_per_page
            viewer.render(viewer.current_page * lines_per_page)
        elif page:
            viewer.render((page - 1) * (console.height - 12))
        else:
            viewer.render()
    
    cli()


if __name__ == '__main__':
    main()
