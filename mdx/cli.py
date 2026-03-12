#!/usr/bin/env python3
"""
MDX - A beautiful Markdown viewer for terminal
"""

import click
import curses
from pathlib import Path
from .parser import MarkdownParser
from .renderer import TerminalRenderer


class MDXViewer:
    """Main MDX viewer class"""
    
    def __init__(self, filepath: str):
        self.filepath = Path(filepath)
        self.content = self.filepath.read_text()
        self.parser = MarkdownParser(self.content)
        self.parsed_content = self.parser.parse()
        self.renderer = TerminalRenderer()
        self.scroll = 0
    
    def run(self):
        """Run the viewer"""
        def run_curses(stdscr):
            self._run_interactive(stdscr)
        
        curses.wrapper(run_curses)
    
    def _run_interactive(self, stdscr):
        """Run interactive mode with curses"""
        import time
        
        try:
            stdscr.nodelay(True)
            last_scroll = -1
            last_screen_size = (0, 0)
            
            # Initial render
            self.renderer.render(stdscr, self.parsed_content, self.scroll)
            last_scroll = self.scroll
            
            while True:
                try:
                    # Get key press
                    key = stdscr.getch()
                    
                    # Handle keys (less-style)
                    if key == ord('q'):
                        break
                    elif key in [ord('j'), ord('J'), curses.KEY_DOWN]:
                        self.scroll_down()
                        # Force render on key press
                        self.renderer.render(stdscr, self.parsed_content, self.scroll)
                        last_scroll = self.scroll
                    elif key in [ord('k'), ord('K'), curses.KEY_UP]:
                        self.scroll_up()
                        # Force render on key press
                        self.renderer.render(stdscr, self.parsed_content, self.scroll)
                        last_scroll = self.scroll
                    elif key in [ord('g')]:
                        self.scroll_to_top()
                        # Force render on key press
                        self.renderer.render(stdscr, self.parsed_content, self.scroll)
                        last_scroll = self.scroll
                    elif key in [ord('G')]:
                        self.scroll_to_bottom()
                        # Force render on key press
                        self.renderer.render(stdscr, self.parsed_content, self.scroll)
                        last_scroll = self.scroll
                    elif key in [ord(' '), ord('f')]:
                        self.scroll_down(10)
                        # Force render on key press
                        self.renderer.render(stdscr, self.parsed_content, self.scroll)
                        last_scroll = self.scroll
                    elif key in [ord('b')]:
                        self.scroll_up(10)
                        # Force render on key press
                        self.renderer.render(stdscr, self.parsed_content, self.scroll)
                        last_scroll = self.scroll
                    elif key in [ord('/')]:
                        # Simple search (to be implemented)
                        pass
                    elif key in [ord('n')]:
                        # Next search result (to be implemented)
                        pass
                    elif key in [ord('N')]:
                        # Previous search result (to be implemented)
                        pass
                    
                    # Small delay to reduce CPU usage but maintain responsiveness
                    time.sleep(0.005)
                    
                except KeyboardInterrupt:
                    # Handle Ctrl+C gracefully
                    break
                except Exception as e:
                    # Display error
                    try:
                        stdscr.clear()
                        stdscr.addstr(0, 0, f"Error: {str(e)}", curses.A_REVERSE | curses.A_BOLD)
                        stdscr.addstr(2, 0, "Press q to exit", curses.A_DIM)
                        stdscr.refresh()
                        time.sleep(2)
                    except:
                        pass
                    break
        except KeyboardInterrupt:
            # Handle Ctrl+C at the outer level
            pass
        except Exception as e:
            # Display overall error
            try:
                stdscr.clear()
                stdscr.addstr(0, 0, f"Fatal error: {str(e)}", curses.A_REVERSE | curses.A_BOLD)
                stdscr.addstr(2, 0, "Press any key to exit", curses.A_DIM)
                stdscr.refresh()
                stdscr.getch()  # Wait for user input
            except:
                pass
    
    def scroll_down(self, n: int = 1):
        """Scroll down by n lines"""
        # Get actual terminal height for dynamic calculation
        import shutil
        try:
            height = shutil.get_terminal_size().lines
            content_height = max(10, height - 5)  # Reserve space for header and status
        except:
            content_height = 20  # Fallback to reasonable default
        max_scroll = max(0, len(self.parsed_content) - content_height)
        self.scroll = min(max_scroll, self.scroll + n)
    
    def scroll_up(self, n: int = 1):
        """Scroll up by n lines"""
        self.scroll = max(0, self.scroll - n)
    
    def scroll_to_top(self):
        """Scroll to top"""
        self.scroll = 0
    
    def scroll_to_bottom(self):
        """Scroll to bottom"""
        # Get actual terminal height for dynamic calculation
        import shutil
        try:
            height = shutil.get_terminal_size().lines
            content_height = max(10, height - 5)  # Reserve space for header and status
        except:
            content_height = 20  # Fallback to reasonable default
        self.scroll = max(0, len(self.parsed_content) - content_height)


def main():
    """Main entry point"""
    @click.command()
    @click.argument('file', type=click.Path(exists=True))
    @click.version_option(version='1.0.0', prog_name='mdx')
    def cli(file):
        """MDX - Markdown Viewer for Terminal
        
        View Markdown files in the terminal with beautiful formatting.
        """
        viewer = MDXViewer(file)
        viewer.run()
    
    cli()


if __name__ == '__main__':
    main()
