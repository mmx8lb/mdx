#!/usr/bin/env python3
"""Test script for search display functionality"""

import curses
from mdx.cli import MDXViewer


def test_search_display(stdscr):
    """Test search display functionality"""
    # Create a test document with Chinese characters
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
    
    # Test search with Chinese term
    search_term = "搜索"
    print(f"Testing search with term: '{search_term}'")
    viewer.search(search_term)
    print(f"Search results: {viewer.search_results}")
    print(f"Current result index: {viewer.current_result_index}")
    print(f"Scroll position: {viewer.scroll}")
    print(f"Search term: '{viewer.search_term}'")
    
    # Test search with English term
    search_term = "Markdown"
    print(f"\nTesting search with term: '{search_term}'")
    viewer.search(search_term)
    print(f"Search results: {viewer.search_results}")
    print(f"Current result index: {viewer.current_result_index}")
    print(f"Scroll position: {viewer.scroll}")
    print(f"Search term: '{viewer.search_term}'")
    
    # Test search with another Chinese term
    search_term = "中文"
    print(f"\nTesting search with term: '{search_term}'")
    viewer.search(search_term)
    print(f"Search results: {viewer.search_results}")
    print(f"Current result index: {viewer.current_result_index}")
    print(f"Scroll position: {viewer.scroll}")
    print(f"Search term: '{viewer.search_term}'")
    
    # Clean up
    import os
    if os.path.exists("test_search.md"):
        os.remove("test_search.md")


if __name__ == "__main__":
    # Run without curses wrapper since we're not doing interactive input
    test_search_display(None)
