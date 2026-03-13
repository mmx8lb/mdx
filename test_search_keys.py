#!/usr/bin/env python3
"""
Test script to verify search functionality key handling
"""

import curses
import time

class TestSearch:
    """Test search functionality"""
    
    def __init__(self):
        self.search_term = ""
        self.search_results = []
        self.current_result_index = -1
    
    def _get_search_input(self, stdscr):
        """Get search input from user"""
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
    
    def search(self, term):
        """Search for term (simulated)"""
        if not term:
            self.search_term = ""
            self.search_results = []
            self.current_result_index = -1
            return
        
        self.search_term = term
        # Simulate search results
        self.search_results = [5, 12, 18, 25, 30]
        self.current_result_index = 0
        
        return self.search_results
    
    def find_next(self):
        """Find next search result"""
        if not self.search_results:
            return -1
        
        self.current_result_index = (self.current_result_index + 1) % len(self.search_results)
        return self.search_results[self.current_result_index]
    
    def find_previous(self):
        """Find previous search result"""
        if not self.search_results:
            return -1
        
        self.current_result_index = (self.current_result_index - 1) % len(self.search_results)
        return self.search_results[self.current_result_index]

def test_search_keys(stdscr):
    """Test search key handling"""
    test_search = TestSearch()
    
    stdscr.clear()
    stdscr.addstr(0, 0, "Testing search functionality key handling...")
    stdscr.addstr(2, 0, "Press / to start search")
    stdscr.addstr(3, 0, "Press n to go to next result")
    stdscr.addstr(4, 0, "Press N to go to previous result")
    stdscr.addstr(5, 0, "Press ESC to cancel search")
    stdscr.addstr(7, 0, "Current state:")
    stdscr.addstr(8, 0, f"Search term: {test_search.search_term}")
    stdscr.addstr(9, 0, f"Results: {test_search.search_results}")
    stdscr.addstr(10, 0, f"Current index: {test_search.current_result_index}")
    stdscr.addstr(12, 0, "Press q to quit")
    stdscr.refresh()
    
    while True:
        key = stdscr.getch()
        
        if key == ord('q'):
            break
        elif key == ord('/'):
            # Start search
            search_term = test_search._get_search_input(stdscr)
            if search_term:
                results = test_search.search(search_term)
                stdscr.addstr(14, 0, f"Search for '{search_term}' found {len(results)} results")
            else:
                stdscr.addstr(14, 0, "Search cancelled")
        elif key == ord('n'):
            # Next result
            result = test_search.find_next()
            if result != -1:
                stdscr.addstr(14, 0, f"Next result: {result}")
            else:
                stdscr.addstr(14, 0, "No search results")
        elif key == ord('N'):
            # Previous result
            result = test_search.find_previous()
            if result != -1:
                stdscr.addstr(14, 0, f"Previous result: {result}")
            else:
                stdscr.addstr(14, 0, "No search results")
        elif key == 27:  # ESC
            # Clear search results
            test_search.search_term = ""
            test_search.search_results = []
            test_search.current_result_index = -1
            stdscr.addstr(14, 0, "Search cleared")
        
        # Update state display
        stdscr.addstr(8, 0, f"Search term: {test_search.search_term}")
        stdscr.addstr(9, 0, f"Results: {test_search.search_results}")
        stdscr.addstr(10, 0, f"Current index: {test_search.current_result_index}")
        stdscr.refresh()

if __name__ == "__main__":
    curses.wrapper(test_search_keys)
