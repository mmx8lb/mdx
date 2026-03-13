#!/usr/bin/env python3
"""Test script for search input functionality"""

from mdx.utils.terminal import get_display_width


def test_display_width():
    """Test display width calculation for Chinese characters"""
    test_cases = [
        ("搜索", 4),  # 2 Chinese characters should be 4 width
        ("功能", 4),  # 2 Chinese characters should be 4 width
        ("Markdown", 8),  # 8 ASCII characters should be 8 width
        ("中文", 4),  # 2 Chinese characters should be 4 width
        ("测试测试", 8),  # 4 Chinese characters should be 8 width
    ]
    
    print("Testing display width calculation...")
    for text, expected in test_cases:
        result = get_display_width(text)
        status = "✓" if result == expected else "✗"
        print(f"{status} '{text}' -> {result} (expected: {expected})")


def test_input_handling():
    """Test input handling logic"""
    print("\nTesting input handling logic...")
    
    # Test cases for input handling
    test_inputs = [
        "搜索",
        "功能",
        "Markdown",
        "中文",
        "测试搜索功能",
    ]
    
    for input_text in test_inputs:
        display_width = get_display_width(input_text)
        print(f"Input: '{input_text}' -> Display width: {display_width}")


if __name__ == "__main__":
    test_display_width()
    test_input_handling()
