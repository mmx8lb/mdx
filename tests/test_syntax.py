#!/usr/bin/env python3
"""Test syntax highlighting"""

from mdx.renderers.syntax_highlight import SyntaxHighlighter

# Test Python code
python_code = "def hello_world():\n    print(\"Hello, world!\")\n    return 42"

# Test Bash code
bash_code = "echo \"Hello, bash!\"\nls -la"

# Create syntax highlighter
highlighter = SyntaxHighlighter(theme='monokai')

# Test Python syntax highlighting
print("Testing Python syntax highlighting:")
print(f"Original code:\n{python_code}")
highlighted_python = highlighter.highlight(python_code, 'python')
print(f"Highlighted code:\n{repr(highlighted_python)}")
print()

# Test Bash syntax highlighting
print("Testing Bash syntax highlighting:")
print(f"Original code:\n{bash_code}")
highlighted_bash = highlighter.highlight(bash_code, 'bash')
print(f"Highlighted code:\n{repr(highlighted_bash)}")
