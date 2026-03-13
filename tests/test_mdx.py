#!/usr/bin/env python3
"""
Tests for MDX - Markdown Viewer for Terminal
"""

import unittest
from pathlib import Path
from mdx.parser import MarkdownParser
from mdx.renderer import TerminalRenderer

class TestMarkdownParser(unittest.TestCase):
    """Test markdown parser functionality"""
    
    def test_basic_parsing(self):
        """Test basic markdown parsing"""
        content = """# Header 1

## Header 2

- List item 1
- List item 2

> Blockquote

```python
print("Hello World")
```

| Header 1 | Header 2 |
|----------|----------|
| Cell 1   | Cell 2   |
"""
        parser = MarkdownParser(content)
        parsed = parser.parse()
        
        # Check that we have the expected number of items
        self.assertGreater(len(parsed), 0)
        
        # Check that we have different types of items
        item_types = [item[0] for item in parsed]
        self.assertIn('header', item_types)
        self.assertIn('list_item', item_types)
        self.assertIn('blockquote', item_types)
        self.assertIn('code_block', item_types)
        self.assertIn('table', item_types)
    
    def test_table_parsing(self):
        """Test table parsing"""
        content = """
| Header 1 | Header 2 |
|----------|----------|
| Cell 1   | Cell 2   |
| Cell 3   | Cell 4   |
"""
        parser = MarkdownParser(content)
        parsed = parser.parse()
        
        # Find the table item
        table_items = [item for item in parsed if item[0] == 'table']
        self.assertEqual(len(table_items), 1)

class TestTerminalRenderer(unittest.TestCase):
    """Test terminal renderer functionality"""
    
    def test_initialization(self):
        """Test renderer initialization"""
        renderer = TerminalRenderer()
        self.assertIsNotNone(renderer)
    
    def test_theme_selection(self):
        """Test theme selection"""
        renderer = TerminalRenderer(theme='dracula')
        self.assertIsNotNone(renderer)
        
        # Test with invalid theme (should fallback to monokai)
        renderer = TerminalRenderer(theme='invalid_theme')
        self.assertIsNotNone(renderer)

if __name__ == '__main__':
    unittest.main()
