# MDX - Markdown Viewer for Terminal

<p align="center">
  <img src="https://img.shields.io/pypi/v/mdx" alt="PyPI">
  <img src="https://img.shields.io/pypi/l/mdx" alt="License">
  <img src="https://img.shields.io/pypi/pyversions/mdx" alt="Python">
</p>

A beautiful Markdown viewer for terminal with code execution support.

## Features

- 🎨 Beautiful syntax highlighting with multiple themes
- 📑 Table of contents navigation
- ⚡ Execute code blocks directly (bash, python)
- 🔍 Search within documents
- 📖 Multiple rendering modes

## Installation

```bash
pip install mdx
```

## Usage

```bash
# View a markdown file
mdx README.md

# Show table of contents
mdx README.md --toc

# Execute code blocks
mdx README.md --execute

# Jump to specific line
mdx README.md --line 100

# Use different theme
mdx README.md --theme dracula
```

## Options

| Option | Description |
|--------|-------------|
| `-e, --execute` | Execute code blocks |
| `-t, --toc` | Show table of contents |
| `-l, --line` | Jump to specific line |
| `-m, --theme` | Syntax highlighting theme |

## Themes

Available syntax highlighting themes:
- monokai (default)
- dracula
- github-dark
- nord
- solarized-dark

## Example

```bash
# Read documentation
mdx docs/linux-0.11-filesystem-analysis.md --toc

# Execute tutorial code blocks
mdx docs/tutorial.md --execute
```

## License

MIT License
