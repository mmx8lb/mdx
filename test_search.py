#!/usr/bin/env python3
"""
Test script to verify search functionality
"""

import curses
import time
from mdx.parser import MarkdownParser

class TestSearch:
    """Test search functionality"""
    
    def __init__(self, content):
        self.parser = MarkdownParser(content)
        self.parsed_content = self.parser.parse()
        self.search_term = ""
        self.search_results = []
        self.current_result_index = -1
    
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
            scroll = self.search_results[0]
            return scroll
        return -1

def test_search_functionality():
    """Test search functionality"""
    # Test content with Chinese characters
    test_content = """# 测试文档

这是一个测试文档，用于测试搜索功能。

## 中文测试

这是一个中文段落，包含一些关键词：层、文件系统、inode。

### 代码测试

```python
def hello():
    print("Hello, world!")
```

### 表格测试

| 列1 | 列2 |
|-----|-----|
| 中文 | English |
| 层 | layer |
| inode | inode |
"""
    
    print("Testing search functionality...")
    print("=" * 50)
    
    # Create test instance
    test_search = TestSearch(test_content)
    
    # Test cases
    test_cases = [
        "测试",
        "层",
        "inode",
        "Hello",
        "表格",
        "English"
    ]
    
    for term in test_cases:
        print(f"\nSearching for: '{term}'")
        scroll = test_search.search(term)
        print(f"Results found: {len(test_search.search_results)}")
        print(f"Scroll position: {scroll}")
        print(f"Results: {test_search.search_results}")
    
    print("\n" + "=" * 50)
    print("Test completed!")

if __name__ == "__main__":
    test_search_functionality()
