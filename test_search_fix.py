#!/usr/bin/env python3
"""Test script for search functionality fix"""

import curses
import time
from mdx.cli import MDXViewer


def test_search_input(stdscr):
    """Test search input functionality"""
    curses.curs_set(1)
    curses.echo()
    
    # Create a simple test document with Chinese characters
    test_content = """
# MDX - Markdown Viewer

这是一个测试文档，用于测试搜索功能。

## 功能特点
- 支持 Markdown 语法解析
- 支持中文显示
- 支持搜索功能

## 搜索测试
请搜索以下关键词：
- 搜索
- 功能
- Markdown
- 中文
"""
    
    # Write test content to a temporary file
    with open("test_search.md", "w", encoding="utf-8") as f:
        f.write(test_content)
    
    # Initialize MDXViewer
    viewer = MDXViewer("test_search.md")
    
    # Test search input method directly
    stdscr.clear()
    stdscr.addstr(0, 0, "测试搜索输入功能，请输入中文关键词...")
    stdscr.addstr(1, 0, "按 / 开始搜索，输入 '搜索' 后按 Enter")
    stdscr.addstr(2, 0, "按 q 退出测试")
    stdscr.refresh()
    
    # Wait for user to press /
    while True:
        key = stdscr.getch()
        if key == ord('/'):
            # Test search input
            search_term = viewer._get_search_input(stdscr)
            stdscr.addstr(4, 0, f"搜索词: '{search_term}'")
            stdscr.refresh()
            time.sleep(2)
        elif key == ord('q'):
            break
    
    # Clean up
    import os
    if os.path.exists("test_search.md"):
        os.remove("test_search.md")


if __name__ == "__main__":
    curses.wrapper(test_search_input)
