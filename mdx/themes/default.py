"""Default theme definition"""

DEFAULT_THEME = {
    'header': {
        1: (2, -1),  # Cyan
        2: (4, -1),  # Blue
        3: (1, -1),  # Green
        4: (3, -1),  # Yellow
        5: (5, -1),  # Red
        6: (6, -1)   # Magenta
    },
    'list': (6, -1),  # Magenta
    'blockquote': (1, -1),  # Green
    'code': (3, -1),  # Yellow
    'table': (2, -1),  # Cyan
    'hr': (7, -1)  # White
}

# Available themes
AVAILABLE_THEMES = {
    'monokai': DEFAULT_THEME,
    'dracula': {
        'header': {
            1: (5, -1),  # Red
            2: (4, -1),  # Blue
            3: (1, -1),  # Green
            4: (3, -1),  # Yellow
            5: (6, -1),  # Magenta
            6: (2, -1)   # Cyan
        },
        'list': (6, -1),  # Magenta
        'blockquote': (1, -1),  # Green
        'code': (3, -1),  # Yellow
        'table': (4, -1),  # Blue
        'hr': (7, -1)  # White
    },
    'github-dark': {
        'header': {
            1: (4, -1),  # Blue
            2: (4, -1),  # Blue
            3: (4, -1),  # Blue
            4: (4, -1),  # Blue
            5: (4, -1),  # Blue
            6: (4, -1)   # Blue
        },
        'list': (6, -1),  # Magenta
        'blockquote': (7, -1),  # White
        'code': (3, -1),  # Yellow
        'table': (7, -1),  # White
        'hr': (7, -1)  # White
    },
    'nord': {
        'header': {
            1: (4, -1),  # Blue
            2: (6, -1),  # Magenta
            3: (1, -1),  # Green
            4: (3, -1),  # Yellow
            5: (5, -1),  # Red
            6: (2, -1)   # Cyan
        },
        'list': (6, -1),  # Magenta
        'blockquote': (1, -1),  # Green
        'code': (3, -1),  # Yellow
        'table': (4, -1),  # Blue
        'hr': (7, -1)  # White
    },
    'solarized-dark': {
        'header': {
            1: (4, -1),  # Blue
            2: (6, -1),  # Magenta
            3: (1, -1),  # Green
            4: (3, -1),  # Yellow
            5: (5, -1),  # Red
            6: (2, -1)   # Cyan
        },
        'list': (6, -1),  # Magenta
        'blockquote': (1, -1),  # Green
        'code': (3, -1),  # Yellow
        'table': (4, -1),  # Blue
        'hr': (7, -1)  # White
    }
}