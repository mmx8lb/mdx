#!/usr/bin/env python3
"""
Test script to verify ESC key handling fix
"""

import curses
import time

def test_esc_key(stdscr):
    """Test ESC key handling"""
    stdscr.clear()
    stdscr.addstr(0, 0, "Testing ESC key handling...")
    stdscr.addstr(2, 0, "Press / to start search, then press ESC to cancel")
    stdscr.addstr(4, 0, "Expected: ESC should cancel search without displaying escape sequence")
    stdscr.refresh()
    
    # Simulate the search input process
    def get_search_input():
        curses.echo()
        curses.curs_set(1)
        
        try:
            width = curses.COLS
        except:
            width = 80
        
        prompt = "/"
        input_text = ""
        
        while True:
            # Clear the bottom line and display prompt
            try:
                stdscr.move(curses.LINES - 1, 0)
                stdscr.clrtoeol()
                stdscr.addstr(curses.LINES - 1, 0, prompt + input_text)
                stdscr.refresh()
            except:
                pass
            
            # Get key press
            try:
                key = stdscr.get_wch()
            except:
                # Fallback to getch() if get_wch() fails
                key = stdscr.getch()
            
            if isinstance(key, int):
                if key == curses.KEY_BACKSPACE or key == 127:
                    # Backspace
                    input_text = input_text[:-1]
                elif key == curses.KEY_ENTER or key == 10 or key == 13:
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
                # Handle string input (including escape sequences)
                if key == '\x1b':  # ESC character as string
                    # Cancel search
                    input_text = ""
                    break
                # Check if it's a Unicode character (e.g., Chinese)
                input_text += key
        
        # Restore settings
        curses.noecho()
        curses.curs_set(0)
        
        return input_text
    
    # Wait for user to press /
    while True:
        key = stdscr.getch()
        if key == ord('/'):
            result = get_search_input()
            stdscr.clear()
            stdscr.addstr(0, 0, f"Search input result: '{result}'")
            stdscr.addstr(2, 0, "If ESC was pressed, result should be empty string")
            stdscr.addstr(4, 0, "Press q to quit")
            stdscr.refresh()
            # Wait for q to quit
            while True:
                key = stdscr.getch()
                if key == ord('q'):
                    return
        elif key == ord('q'):
            return

if __name__ == "__main__":
    curses.wrapper(test_esc_key)
