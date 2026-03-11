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
        
        # Print header
        word_count = len(self.content.split())
        console.print(Panel(
            f"[bold cyan]{self.filepath.name}[/bold cyan]",
            subtitle=f"📄 {word_count} words | {len(self.code_blocks)} code blocks | {len(self.lines)} lines",
            box=box.DOUBLE,
            style="cyan"
        ))
        console.print()
        
        # Render markdown content
        self._render_content(start_line)
        
        # Show navigation hint
        console.print()
        console.print("[dim]↑↓: 翻页 | t: 目录 | /: 搜索 | q: 退出[/dim]")
        
        if self.execute and self.code_blocks:
            self._execute_code_blocks()
    
    def _render_content(self, start_line: int = 0):
        """Render markdown content with proper styling"""
        # Remove code blocks for cleaner display
        content = self._remove_code_blocks(self.content)
        
        # Use rich's Markdown parser
        md = Markdown(content, code_theme=self.theme)
        
        # Render with padding
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
    
    def _execute_code_blocks(self):
        """Execute all code blocks"""
        console.print()
        console.print(Panel("[bold yellow]⚡ Executing Code Blocks[/bold yellow]", box=box.ROUNDED))
        
        for i, block in enumerate(self.code_blocks, 1):
            console.print(f"\n[cyan]--- Code Block {i}: {block.language} (line {block.line_number}) ---[/cyan]")
            
            # Show code with syntax highlighting
            syntax = Syntax(
                block.code, 
                block.language if block.language != "text" else "bash", 
                theme=self.theme,
                line_numbers=False
            )
            console.print(syntax)
            
            # Execute
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
    
    def interactive(self):
        """Interactive mode with navigation"""
        current_line = 0
        lines_per_page = console.height - 10
        
        while True:
            self.render(current_line)
            
            try:
                key = console.input("\n[cyan]>[/cyan] ")
                key = key.strip().lower()
                
                if key == 'q' or key == 'quit':
                    break
                elif key == 'up' or key == 'k':
                    current_line = max(0, current_line - lines_per_page)
                elif key == 'down' or key == 'j':
                    current_line = min(len(self.lines), current_line + lines_per_page)
                elif key == 't' or key == 'toc':
                    self.show_toc()
                    console.input("\n[dim]Press Enter to continue...[/dim]")
                elif key == '/':
                    search_term = console.input("[cyan]Search: [/cyan]")
                    self._search(search_term)
                elif key.isdigit():
                    line_num = int(key)
                    if 1 <= line_num <= len(self.lines):
                        self._show_line(line_num)
                else:
                    # Try to parse as line number or command
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
    @click.version_option(version='0.2.0', prog_name='mdx')
    def cli(file: str, execute: bool, toc: bool, line: int, theme: str, interactive: bool, search: str):
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
            viewer._show_line(line)
        else:
            viewer.render()
    
    cli()


if __name__ == '__main__':
    main()
