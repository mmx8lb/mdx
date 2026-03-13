#!/usr/bin/env python3
"""
MDX - A beautiful Markdown viewer for terminal
"""

import click
import curses
from pathlib import Path
from .parser import MarkdownParser
from .renderer import TerminalRenderer
from . import __version__


class MDXViewer:
    """Main MDX viewer class"""
    
    def __init__(self, filepath: str, toc=False, execute=False, line=None, theme='monokai', dev_mode=False):
        self.filepath = Path(filepath)
        # Read file with UTF-8 encoding to handle Chinese characters correctly
        self.content = self.filepath.read_text(encoding='utf-8')
        self.parser = MarkdownParser(self.content)
        self.parsed_content = self.parser.parse()
        self.renderer = TerminalRenderer(theme=theme)
        self.scroll = 0
        self.toc = toc
        self.execute = execute
        self.line = line
        self.theme = theme
        # Search related attributes
        self.search_term = ""
        self.search_results = []
        self.current_result_index = -1
        # Table of contents related attributes
        self.toc_items = []
        self.current_toc_index = -1
        # Development mode
        self.dev_mode = dev_mode
    
    def run(self):
        """Run the viewer"""
        # Handle line jump if specified
        if self.line is not None:
            # Calculate scroll position based on line number
            # Get actual terminal height for dynamic calculation
            import shutil
            try:
                height = shutil.get_terminal_size().lines
                content_height = max(10, height - 5)  # Reserve space for header and status
            except:
                content_height = 20  # Fallback to reasonable default
            # Calculate scroll position (assuming each line in parsed content is one line on screen)
            # This is a simple approximation, actual implementation may need to consider wrapped lines
            self.scroll = max(0, self.line - content_height // 2 - 1)
        
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
                        self.renderer.render(stdscr, self.parsed_content, self.scroll, self.search_term, self.search_results, self.current_result_index, self.dev_mode)
                        last_scroll = self.scroll
                    elif key in [ord('k'), ord('K'), curses.KEY_UP]:
                        self.scroll_up()
                        # Force render on key press
                        self.renderer.render(stdscr, self.parsed_content, self.scroll, self.search_term, self.search_results, self.current_result_index, self.dev_mode)
                        last_scroll = self.scroll
                    elif key in [ord('g')]:
                        self.scroll_to_top()
                        # Force render on key press
                        self.renderer.render(stdscr, self.parsed_content, self.scroll, self.search_term, self.search_results, self.current_result_index, self.dev_mode)
                        last_scroll = self.scroll
                    elif key in [ord('G')]:
                        self.scroll_to_bottom()
                        # Force render on key press
                        self.renderer.render(stdscr, self.parsed_content, self.scroll, self.search_term, self.search_results, self.current_result_index, self.dev_mode)
                        last_scroll = self.scroll
                    elif key in [ord(' '), ord('f')]:
                        # Page down with smooth scrolling
                        self.scroll_page_down()
                        # Force render after scrolling
                        self.renderer.render(stdscr, self.parsed_content, self.scroll, self.search_term, self.search_results, self.current_result_index, self.dev_mode)
                        last_scroll = self.scroll
                    elif key in [ord('b')]:
                        # Page up with smooth scrolling
                        self.scroll_page_up()
                        # Force render after scrolling
                        self.renderer.render(stdscr, self.parsed_content, self.scroll, self.search_term, self.search_results, self.current_result_index, self.dev_mode)
                        last_scroll = self.scroll
                    elif key in [ord('/')]:
                        # Start search
                        search_term = self._get_search_input(stdscr)
                        # Always call search, even if search_term is empty (to clear search state)
                        self.search(search_term)
                        # Force render after search
                        self.renderer.render(stdscr, self.parsed_content, self.scroll, self.search_term, self.search_results, self.current_result_index, self.dev_mode)
                        last_scroll = self.scroll
                    elif key in [ord('n')]:
                        # Next search result
                        self.find_next()
                        # Force render after navigation
                        self.renderer.render(stdscr, self.parsed_content, self.scroll, self.search_term, self.search_results, self.current_result_index, self.dev_mode)
                        last_scroll = self.scroll
                    elif key in [ord('N')]:
                        # Previous search result
                        self.find_previous()
                        # Force render after navigation
                        self.renderer.render(stdscr, self.parsed_content, self.scroll, self.search_term, self.search_results, self.current_result_index, self.dev_mode)
                        last_scroll = self.scroll
                    elif key in [ord('t')]:
                        # Show table of contents
                        self.navigate_toc(stdscr)
                        last_scroll = self.scroll
                    elif key in [ord('M')]:
                        # Switch theme
                        self.switch_theme(stdscr)
                        last_scroll = self.scroll
                    elif key == 27:  # ESC
                        # Clear search results and exit search mode
                        if self.search_term:
                            self.search_term = ""
                            self.search_results = []
                            self.current_result_index = -1
                            # Force render after clearing search
                            self.renderer.render(stdscr, self.parsed_content, self.scroll, self.search_term, self.search_results, self.current_result_index, self.dev_mode)
                            last_scroll = self.scroll
                    
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
    
    def smooth_scroll_to(self, target_scroll):
        """Smooth scroll to target position"""
        import time
        current_scroll = self.scroll
        step = 1 if target_scroll > current_scroll else -1
        
        while current_scroll != target_scroll:
            current_scroll += step
            # Ensure we don't overshoot
            if step > 0 and current_scroll > target_scroll:
                current_scroll = target_scroll
            elif step < 0 and current_scroll < target_scroll:
                current_scroll = target_scroll
            
            self.scroll = current_scroll
            # Small delay for smooth effect
            time.sleep(0.01)
    
    def scroll_page_down(self):
        """Scroll down by one page"""
        # Get actual terminal height for dynamic calculation
        import shutil
        try:
            height = shutil.get_terminal_size().lines
            content_height = max(10, height - 5)  # Reserve space for header and status
        except:
            content_height = 20  # Fallback to reasonable default
        max_scroll = max(0, len(self.parsed_content) - content_height)
        target_scroll = min(max_scroll, self.scroll + content_height)
        self.smooth_scroll_to(target_scroll)
    
    def scroll_page_up(self):
        """Scroll up by one page"""
        # Get actual terminal height for dynamic calculation
        import shutil
        try:
            height = shutil.get_terminal_size().lines
            content_height = max(10, height - 5)  # Reserve space for header and status
        except:
            content_height = 20  # Fallback to reasonable default
        target_scroll = max(0, self.scroll - content_height)
        self.smooth_scroll_to(target_scroll)
    
    def _get_search_input(self, stdscr):
        """Get search input from user"""
        # Save current curses settings
        try:
            # Get current echo state
            import curses
            old_echo = curses.echo()
            # Disable echo for manual input handling
            curses.noecho()
        except:
            old_echo = False
        
        # Save current cursor state and show cursor
        try:
            old_curs_set = curses.curs_set(1)
        except:
            old_curs_set = 0
        
        # Get terminal size
        try:
            height, width = curses.LINES, curses.COLS
        except:
            height, width = 24, 80
        
        # Import display width function
        from .utils.terminal import get_display_width
        
        # Display search prompt with help
        prompt = "/"  # Search prompt
        help_text = " [Enter:搜索, ESC:取消] "  # Keyboard help
        input_text = ""
        
        try:
            while True:
                # Clear the bottom line and display prompt
                try:
                    # Clear the entire line
                    stdscr.move(height - 1, 0)
                    stdscr.clrtoeol()
                    
                    # Use reverse video for search prompt to make it more visible
                    stdscr.addstr(height - 1, 0, prompt, curses.A_REVERSE)
                    
                    # Display input text
                    if input_text:
                        stdscr.addstr(height - 1, 1, input_text)
                    
                    # Add help text after input
                    help_pos = 1 + get_display_width(input_text)
                    if help_pos < width - len(help_text):
                        stdscr.addstr(height - 1, help_pos, help_text, curses.A_DIM)
                    
                    # Move cursor to the end of input text
                    cursor_pos = 1 + get_display_width(input_text)
                    if cursor_pos < width:
                        stdscr.move(height - 1, cursor_pos)
                    else:
                        stdscr.move(height - 1, width - 1)
                    
                    stdscr.refresh()
                except Exception:
                    pass
                
                # Get key press
                try:
                    key = stdscr.get_wch()
                except Exception:
                    # Fallback to getch() if get_wch() fails
                    try:
                        key = stdscr.getch()
                    except Exception:
                        # If both fail, just continue to next iteration
                        continue
                
                # Handle key input
                if isinstance(key, int):
                    if key == curses.KEY_BACKSPACE or key == 127:
                        # Backspace
                        input_text = input_text[:-1]
                    elif key in [curses.KEY_ENTER, 10, 13]:
                        # Enter
                        break
                    elif key == 27:  # ESC
                        # Cancel search
                        input_text = ""
                        break
                    elif 32 <= key <= 126:
                        # Printable ASCII character
                        input_text += chr(key)
                else:
                    # Handle string input (including Unicode characters like Chinese)
                    if key == '\x1b':  # ESC character as string
                        # Cancel search
                        input_text = ""
                        break
                    # Add the character to input
                    input_text += key
        finally:
            # Restore original curses settings
            curses.curs_set(old_curs_set)
            if old_echo:
                curses.echo()
        
        # Clean up search term by removing any quotes and whitespace
        input_text = input_text.replace("'", "").replace('"', "").strip('\n\r\t ')
        
        return input_text
    
    def search(self, term):
        """Search for term in parsed content"""
        if not term:
            self.search_term = ""
            self.search_results = []
            self.current_result_index = -1
            return
        
        self.search_term = term
        self.search_results = []
        self.current_result_index = -1
        
        # Search through parsed content
        for idx, (item_type, content) in enumerate(self.parsed_content):
            if item_type == 'text':
                # For Chinese and other Unicode characters, use exact match
                # For ASCII characters, use case-insensitive match
                if term in content or (term.isascii() and term.lower() in content.lower()):
                    self.search_results.append(idx)
            elif item_type == 'header':
                level, title = content
                if term in title or (term.isascii() and term.lower() in title.lower()):
                    self.search_results.append(idx)
            elif item_type == 'list_item':
                list_type, item_content = content
                if term in item_content or (term.isascii() and term.lower() in item_content.lower()):
                    self.search_results.append(idx)
            elif item_type == 'blockquote':
                if term in content or (term.isascii() and term.lower() in content.lower()):
                    self.search_results.append(idx)
            elif item_type == 'code_block':
                lang, lines = content
                # Search in code lines
                for line in lines:
                    if term in line or (term.isascii() and term.lower() in line.lower()):
                        self.search_results.append(idx)
                        break  # Only add once per code block
            elif item_type == 'table':
                # Search in table lines
                for line in content:
                    if term in line or (term.isascii() and term.lower() in line.lower()):
                        self.search_results.append(idx)
                        break  # Only add once per table
        
        # Go to first result if any
        if self.search_results:
            self.current_result_index = 0
            self.scroll = self.search_results[0]
    
    def find_next(self):
        """Find next search result"""
        if not self.search_results:
            return
        
        self.current_result_index = (self.current_result_index + 1) % len(self.search_results)
        self.scroll = self.search_results[self.current_result_index]
    
    def find_previous(self):
        """Find previous search result"""
        if not self.search_results:
            return
        
        self.current_result_index = (self.current_result_index - 1) % len(self.search_results)
        self.scroll = self.search_results[self.current_result_index]
    
    def build_toc(self):
        """Build table of contents from parsed content"""
        self.toc_items = []
        
        for idx, (item_type, content) in enumerate(self.parsed_content):
            if item_type == 'header':
                level, title = content
                self.toc_items.append((level, title, idx))
        
        if self.toc_items:
            self.current_toc_index = 0
    
    def display_toc(self, stdscr):
        """Display table of contents"""
        if not self.toc_items:
            return
        
        # Get terminal size
        try:
            height, width = curses.LINES, curses.COLS
        except:
            height, width = 24, 80
        
        # Calculate TOC window size
        toc_width = min(50, width - 4)  # Leave more margin
        toc_height = min(15, height - 4)  # Fixed window height with scroll support
        
        # Create TOC window
        try:
            # Create window
            toc_win = curses.newwin(toc_height, toc_width, 2, 2)  # Move window inwards
            
            # Set the window to receive input
            toc_win.keypad(True)
            
            # Hide cursor
            curses.curs_set(0)
            
            # Initial draw
            toc_win.clear()
            
            # Create a simple ASCII border
            # Top border
            try:
                top_border = "+" + "-" * (toc_width - 2) + "+"
                toc_win.addstr(0, 0, top_border)
            except:
                pass
            
            # Bottom border
            try:
                bottom_border = "+" + "-" * (toc_width - 2) + "+"
                toc_win.addstr(toc_height - 1, 0, bottom_border)
            except:
                pass
            
            # Left and right borders
            try:
                for i in range(1, toc_height - 1):
                    toc_win.addstr(i, 0, "|")
                    toc_win.addstr(i, toc_width - 1, "|")
            except:
                pass
            
            # Title
            try:
                toc_win.addstr(0, 2, " Table of Contents ", curses.A_BOLD)
            except:
                pass
            
            # Store previous selected index
            prev_index = -1
            # Track scroll position
            scroll_position = 0
            
            # Calculate visible items count
            visible_items = toc_height - 2
            
            # Handle TOC navigation
            while True:
                # Only redraw if selection has changed or scroll position has changed
                if self.current_toc_index != prev_index:
                    # Adjust scroll position to keep selected item visible
                    if self.current_toc_index < scroll_position:
                        scroll_position = self.current_toc_index
                    elif self.current_toc_index >= scroll_position + visible_items:
                        scroll_position = self.current_toc_index - visible_items + 1
                    
                    # Clear only the content area (inside the borders)
                    try:
                        for i in range(1, toc_height - 1):
                            # Clear from column 1 to toc_width - 2 (inside the right border)
                            toc_win.move(i, 1)
                            toc_win.clrtoeol()
                            # Restore right border
                            toc_win.addstr(i, toc_width - 1, "|")
                    except:
                        pass
                    
                    # Display TOC items with scroll support
                    try:
                        for i in range(scroll_position, min(scroll_position + visible_items, len(self.toc_items))):
                            # Calculate display line (relative to window)
                            display_line = i - scroll_position + 1
                            if display_line < 1 or display_line >= toc_height - 1:
                                continue
                            
                            level, title, idx = self.toc_items[i]
                            indent = (level - 1) * 2
                            # Calculate available width for title
                            max_title_width = toc_width - 3 - indent
                            if max_title_width > 0:
                                # Truncate title if it's too long
                                truncated_title = title[:max_title_width]
                                if i == self.current_toc_index:
                                    # Highlight current item
                                    toc_win.addstr(display_line, 2 + indent, truncated_title, curses.A_REVERSE)
                                else:
                                    toc_win.addstr(display_line, 2 + indent, truncated_title)
                    except:
                        pass
                    
                    # Refresh the window
                    try:
                        toc_win.refresh()
                    except:
                        pass
                    
                    # Update previous index
                    prev_index = self.current_toc_index
                
                # Get key press from the TOC window
                try:
                    key = toc_win.getch()
                except Exception as e:
                    print(f"Error getting key: {str(e)}")
                    break
                
                try:
                    if key == ord('q') or key == 27:  # ESC
                        break
                    elif key == ord('j') or key == curses.KEY_DOWN:
                        # Move down
                        if self.current_toc_index < len(self.toc_items) - 1:
                            self.current_toc_index += 1
                    elif key == ord('k') or key == curses.KEY_UP:
                        # Move up
                        if self.current_toc_index > 0:
                            self.current_toc_index -= 1
                    elif key == ord(' ') or key == 10 or key == 13:  # Space, Enter
                        # Select current item
                        _, _, idx = self.toc_items[self.current_toc_index]
                        self.scroll = idx
                        break
                except Exception as e:
                    print(f"Error processing key: {str(e)}")
                    break
        except Exception as e:
            # Print error for debugging
            print(f"Error in display_toc: {str(e)}")
            pass
        finally:
            # Restore cursor
            try:
                curses.curs_set(1)
            except:
                pass
    
    def navigate_toc(self, stdscr):
        """Navigate table of contents"""
        if not self.toc_items:
            self.build_toc()
        
        self.display_toc(stdscr)
        # Force render after navigation to immediately show the selected section
        self.renderer.render(stdscr, self.parsed_content, self.scroll, self.search_term, self.search_results, self.current_result_index)
    
    def switch_theme(self, stdscr):
        """Switch theme"""
        from .themes.default import AVAILABLE_THEMES
        
        # Get terminal size
        try:
            height, width = curses.LINES, curses.COLS
        except:
            height, width = 24, 80
        
        # Calculate theme window size
        theme_width = min(40, width - 2)
        theme_height = min(len(AVAILABLE_THEMES) + 2, height - 2)
        
        # Create theme window
        try:
            theme_win = curses.newwin(theme_height, theme_width, 1, 1)
            theme_win.box()
            theme_win.addstr(0, 2, " Select Theme ", curses.A_BOLD)
            
            # Get list of available themes
            themes = list(AVAILABLE_THEMES.keys())
            current_theme_index = themes.index(self.theme) if self.theme in themes else 0
            
            # Display theme options
            for i, theme in enumerate(themes):
                if i >= theme_height - 2:
                    break
                if i == current_theme_index:
                    # Highlight current theme
                    theme_win.addstr(i + 1, 2, theme, curses.A_REVERSE)
                else:
                    theme_win.addstr(i + 1, 2, theme)
            
            theme_win.refresh()
            
            # Handle theme selection
            while True:
                key = stdscr.getch()
                if key == ord('q') or key == 27:  # ESC
                    break
                elif key in [ord('j'), curses.KEY_DOWN]:
                    # Move down
                    current_theme_index = (current_theme_index + 1) % len(themes)
                    # Redraw theme window
                    theme_win.clear()
                    theme_win.box()
                    theme_win.addstr(0, 2, " Select Theme ", curses.A_BOLD)
                    for i, theme in enumerate(themes):
                        if i >= theme_height - 2:
                            break
                        if i == current_theme_index:
                            theme_win.addstr(i + 1, 2, theme, curses.A_REVERSE)
                        else:
                            theme_win.addstr(i + 1, 2, theme)
                    theme_win.refresh()
                elif key in [ord('k'), curses.KEY_UP]:
                    # Move up
                    current_theme_index = (current_theme_index - 1) % len(themes)
                    # Redraw theme window
                    theme_win.clear()
                    theme_win.box()
                    theme_win.addstr(0, 2, " Select Theme ", curses.A_BOLD)
                    for i, theme in enumerate(themes):
                        if i >= theme_height - 2:
                            break
                        if i == current_theme_index:
                            theme_win.addstr(i + 1, 2, theme, curses.A_REVERSE)
                        else:
                            theme_win.addstr(i + 1, 2, theme)
                    theme_win.refresh()
                elif key in [ord(' '), ord('enter'), 10, 13]:
                    # Select theme
                    selected_theme = themes[current_theme_index]
                    self.theme = selected_theme
                    # Update renderer theme
                    self.renderer = TerminalRenderer(theme=selected_theme)
                    break
        except:
            pass
        
        # Force render after theme change
        self.renderer.render(stdscr, self.parsed_content, self.scroll, self.search_term, self.search_results, self.current_result_index)
    
    def execute_code(self, lang, code):
        """Execute code block based on language"""
        if not self.execute:
            return "Code execution is disabled. Use --execute flag to enable."
        
        import subprocess
        import sys
        
        if lang == 'bash' or lang == 'sh':
            try:
                result = subprocess.run(
                    code, 
                    shell=True, 
                    capture_output=True, 
                    text=True,
                    timeout=10  # Add timeout to prevent hanging
                )
                output = result.stdout
                if result.stderr:
                    output += f"\nstderr:\n{result.stderr}"
                return output
            except Exception as e:
                return f"Error executing bash code: {str(e)}"
        elif lang == 'python' or lang == 'py':
            try:
                # Create a temporary script
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                    f.write(code)
                    temp_file = f.name
                
                # Run the script
                result = subprocess.run(
                    [sys.executable, temp_file], 
                    capture_output=True, 
                    text=True,
                    timeout=10  # Add timeout to prevent hanging
                )
                
                # Clean up
                import os
                os.unlink(temp_file)
                
                output = result.stdout
                if result.stderr:
                    output += f"\nstderr:\n{result.stderr}"
                return output
            except Exception as e:
                return f"Error executing python code: {str(e)}"
        else:
            return f"Code execution not supported for {lang} language"


def main():
    """Main entry point"""
    @click.command()
    @click.argument('file', type=click.Path(exists=True))
    @click.version_option(version=__version__, prog_name='mdx')
    @click.option('--toc', '-t', is_flag=True, help='Show table of contents')
    @click.option('--execute', '-e', is_flag=True, help='Execute code blocks')
    @click.option('--line', '-l', type=int, help='Jump to specific line')
    @click.option('--theme', '-m', type=str, default='monokai', help='Syntax highlighting theme')
    @click.option('--dev', '-d', is_flag=True, help='Enable development mode with debug information')
    def cli(file, toc, execute, line, theme, dev):
        """MDX - Markdown Viewer for Terminal
        
        View Markdown files in the terminal with beautiful formatting.
        """
        viewer = MDXViewer(file, toc=toc, execute=execute, line=line, theme=theme, dev_mode=dev)
        viewer.run()
    
    cli()


if __name__ == '__main__':
    main()
