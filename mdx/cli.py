#!/usr/bin/env python3
"""
MDX - A beautiful Markdown viewer for terminal with code execution support
"""

import click
import os
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple, Optional
import re

try:
    from rich.console import Console
    from rich.syntax import Syntax
    from rich.theme import Theme
    from rich.markdown import Markdown
    from rich.panel import Panel
    from rich.table import Table
    from rich import box
except ImportError:
    print("Error: rich library not found. Install with: pip install rich")
    sys.exit(1)

console = Console()

CUSTOM_THEME = Theme({
    "markdown.heading": "bold cyan",
    "markdown.heading1": "bold cyan",
    "markdown.heading2": "bold blue",
    "markdown.heading3": "bold green",
    "markdown.code": "dim white on black",
    "markdown.code_block": "dim white on black",
    "markdown.link": "blue underline",
    "markdown.paragraph": "white",
    "markdown.list": "white",
    "markdown.block_quote": "italic green",
})


class MDXParser:
    """Parse markdown and extract code blocks for execution"""
    
    def __init__(self, content: str):
        self.content = content
        self.code_blocks: List[Tuple[str, str, int]] = []  # (language, code, line_number)
        self._extract_code_blocks()
    
    def _extract_code_blocks(self):
        """Extract all code blocks with their language"""
        lines = self.content.split('\n')
        in_code_block = False
        current_lang = ""
        current_code = []
        start_line = 0
        
        for i, line in enumerate(lines):
            if line.strip().startswith('```'):
                if not in_code_block:
                    in_code_block = True
                    current_lang = line.strip()[3:].strip() or "text"
                    current_code = []
                    start_line = i + 1
                else:
                    in_code_block = False
                    self.code_blocks.append((current_lang, '\n'.join(current_code), start_line))
                    current_lang = ""
                    current_code = []
            elif in_code_block:
                current_code.append(line)
    
    def get_toc(self) -> List[Tuple[int, str, str]]:
        """Extract table of contents"""
        toc = []
        lines = self.content.split('\n')
        for i, line in enumerate(lines):
            match = re.match(r'^(#{1,6})\s+(.+)$', line)
            if match:
                level = len(match.group(1))
                title = match.group(2).strip()
                toc.append((i + 1, "  " * (level - 1) + title, "#" * level))
        return toc


class MDXViewer:
    """Main viewer class"""
    
    def __init__(self, filepath: str, execute: bool = False):
        self.filepath = Path(filepath)
        if not self.filepath.exists():
            console.print(f"[red]Error: File not found: {filepath}[/red]")
            sys.exit(1)
        
        self.execute = execute
        self.content = self.filepath.read_text()
        self.parser = MDXParser(self.content)
    
    def render(self):
        """Render the markdown file"""
        console.clear()
        
        # Print header
        console.print(Panel(
            f"[bold cyan]{self.filepath.name}[/bold cyan]",
            subtitle=f"📄 {len(self.content.split())} words",
            box=box.DOUBLE,
            style="cyan"
        ))
        console.print()
        
        # Render with rich
        syntax = Syntax(self.content, "markdown", theme="monokai", line_numbers=False)
        console.print(syntax)
        
        # Show code blocks summary
        if self.parser.code_blocks:
            console.print()
            console.print(f"[dim]Found {len(self.parser.code_blocks)} code blocks[/dim]")
            
            if self.execute:
                self._execute_code_blocks()
    
    def _execute_code_blocks(self):
        """Execute all code blocks"""
        console.print()
        console.print(Panel("[bold yellow]⚡ Executing Code Blocks[/bold yellow]", box=box.ROUNDED))
        
        for i, (lang, code, line_num) in enumerate(self.parser.code_blocks, 1):
            console.print(f"\n[cyan]--- Code Block {i}: {lang} (line {line_num}) ---[/cyan]")
            
            # Show code
            syntax = Syntax(code, lang if lang != "text" else "bash", theme="monokai")
            console.print(syntax)
            
            # Execute
            if lang in ["bash", "sh", "shell"]:
                self._run_command(code)
            elif lang == "python":
                self._run_python(code)
            else:
                console.print(f"[dim]⚠ Skipping {lang} (not executable)[/dim]")
    
    def _run_command(self, cmd: str):
        """Run shell command"""
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=30
            )
            if result.stdout:
                console.print(f"[green]$ {result.stdout}[/green]")
            if result.stderr:
                console.print(f"[red]{result.stderr}[/red]")
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
        except subprocess.TimeoutExpired:
            console.print("[red]⏱ Code timeout[/red]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
    
    def show_toc(self):
        """Show table of contents"""
        toc = self.parser.get_toc()
        
        if not toc:
            console.print("[dim]No headings found[/dim]")
            return
        
        table = Table(title="📑 Table of Contents", box=box.ROUNDED)
        table.add_column("Line", style="dim", width=6)
        table.add_column("Title", style="cyan")
        
        for line, title, _ in toc:
            table.add_row(str(line), title)
        
        console.print(table)
        console.print(f"\n[dim]Jump to line: mdx {self.filepath} --line N[/dim]")


@click.command()
@click.argument('file', type=click.Path(exists=True))
@click.option('--execute', '-e', is_flag=True, help='Execute code blocks')
@click.option('--toc', '-t', is_flag=True, help='Show table of contents')
@click.option('--line', '-l', type=int, help='Jump to specific line')
@click.option('--theme', '-m', default='monokai', help='Syntax highlighting theme')
@click.version_option(version='0.1.0', prog_name='mdx')
def main(file: str, execute: bool, toc: bool, line: int, theme: str):
    """
    MDX - A beautiful Markdown viewer for terminal
    
    Example:
        mdx README.md
        mdx README.md --execute
        mdx README.md --toc
    """
    viewer = MDXViewer(file, execute=execute)
    
    if toc:
        viewer.show_toc()
    else:
        viewer.render()


if __name__ == '__main__':
    main()
