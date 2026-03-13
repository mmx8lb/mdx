# MDX - Markdown Viewer for Terminal

<p align="center">
  <img src="https://img.shields.io/pypi/v/mdx-viewer" alt="PyPI">
  <img src="https://img.shields.io/pypi/l/mdx-viewer" alt="License">
  <img src="https://img.shields.io/pypi/pyversions/mdx-viewer" alt="Python">
</p>

A beautiful Markdown viewer for terminal with code execution support.

## Features

- 🎨 Beautiful syntax highlighting with multiple themes
- 📑 Table of contents navigation
- ⚡ Execute code blocks directly (bash, python)
- 🔍 Search within documents (supports Chinese)
- 📖 Multiple rendering modes
- 🛠️ Development mode for debugging

## Installation

```bash
pip install mdx-viewer
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

# Enable development mode
mdx README.md --dev
```

## Options

| Option | Description |
|--------|-------------|
| `-e, --execute` | Execute code blocks |
| `-t, --toc` | Show table of contents |
| `-l, --line` | Jump to specific line |
| `-m, --theme` | Syntax highlighting theme |
| `-d, --dev` | Enable development mode |

## Keyboard Shortcuts

- `j`/`k` or arrow keys: Scroll up/down
- `g`: Go to top
- `G`: Go to bottom
- `space`/`f`: Page down
- `b`: Page up
- `/`: Search
- `n`/`N`: Next/previous search result
- `t`: Show table of contents
- `M`: Switch theme
- `q`: Quit

## Search Functionality

- Press `/` to enter search mode
- Type your search term (supports Chinese)
- Press Enter to search
- Press `n` to find next result
- Press `N` to find previous result
- Press ESC to cancel search

## Development Mode

Use `--dev` flag to enable development mode, which shows debug information in a floating window:

```bash
mdx --dev filename.md
```

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

# Debug search functionality
mdx docs/linux-0.11-filesystem-analysis.md --dev
```

## License

MIT License
