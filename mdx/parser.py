"""Markdown parser module"""

import re
from typing import List, Tuple, Dict, Any


class MarkdownParser:
    """Markdown parser class"""
    
    def __init__(self, content: str):
        self.content = content
        self.lines = content.split('\n')
    
    def parse(self) -> List[Tuple[str, Any]]:
        """Parse markdown content into structured data"""
        result = []
        in_code = False
        code_lang = ""
        code_lines = []
        in_table = False
        table_lines = []
        
        try:
            for line in self.lines:
                try:
                    stripped = line.strip()
                    
                    # Code block handling
                    if stripped.startswith('```'):
                        if not in_code:
                            in_code = True
                            code_lang = stripped[3:].strip() or "text"
                            code_lines = []
                        else:
                            in_code = False
                            result.append(('code_block', (code_lang, code_lines)))
                        continue
                    
                    if in_code:
                        code_lines.append(line)
                        continue
                    
                    # Table handling
                    if stripped.startswith('|') and '|' in stripped:
                        if not in_table:
                            in_table = True
                            table_lines = []
                        table_lines.append(line)
                        continue
                    elif in_table:
                        in_table = False
                        result.append(('table', table_lines))
                        table_lines = []
                    
                    # Header
                    if stripped.startswith('#'):
                        level = len(stripped) - len(stripped.lstrip('#'))
                        if level <= 6:
                            title = stripped.lstrip('#').strip()
                            result.append(('header', (level, title)))
                        continue
                    
                    # Horizontal rule
                    if stripped in ['---', '***', '___']:
                        result.append(('hr', None))
                        continue
                    
                    # List item
                    if stripped.startswith(('- ', '* ', '+ ')):
                        content = stripped[2:]
                        result.append(('list_item', ('unordered', content)))
                        continue
                    
                    # Numbered list
                    m = re.match(r'^\d+\.\s+(.*)', stripped)
                    if m:
                        result.append(('list_item', ('ordered', m.group(1))))
                        continue
                    
                    # Blockquote
                    if stripped.startswith('>'):
                        content = stripped[1:].strip()
                        result.append(('blockquote', content))
                        continue
                    
                    # Bold and italic
                    if '**' in line or '*' in line:
                        result.append(('text', line))
                        continue
                    
                    # Regular text
                    result.append(('text', line))
                except Exception as e:
                    # Handle line-level parsing errors
                    result.append(('text', line))  # Fallback to plain text
        except Exception as e:
            # Handle major parsing errors
            result = [('text', f"Error parsing markdown: {str(e)}")]
        
        # Handle any remaining table
        if in_table and table_lines:
            try:
                result.append(('table', table_lines))
            except:
                # Fallback if table parsing fails
                for line in table_lines:
                    result.append(('text', line))
        
        return result
    
    def parse_table(self, table_lines: List[str]) -> Dict[str, Any]:
        """Parse table lines into structured data"""
        if not table_lines:
            return {}
        
        # Parse header
        header = table_lines[0].strip().split('|')
        header = [h.strip() for h in header if h.strip()]
        num_columns = len(header)
        
        # Parse alignment
        alignment = []
        if len(table_lines) > 1:
            align_line = table_lines[1].strip().split('|')
            for i, cell in enumerate(align_line):
                if i == 0 or i == len(align_line) - 1:
                    continue
                cell = cell.strip()
                if cell.startswith(':') and cell.endswith(':'):
                    alignment.append('center')
                elif cell.startswith(':'):
                    alignment.append('left')
                elif cell.endswith(':'):
                    alignment.append('right')
                else:
                    alignment.append('left')
        
        # Parse rows
        rows = []
        # Start from index 2 if there's an alignment line and data rows
        # Skip processing if there are no data rows
        if len(table_lines) > 2:
            for line in table_lines[2:]:
                cells = line.strip().split('|')
                cells = [c.strip() for c in cells if c.strip()]
                # Ensure each row has the same number of columns as header
                while len(cells) < num_columns:
                    cells.append('')
                if len(cells) > num_columns:
                    cells = cells[:num_columns]
                if cells:
                    rows.append(cells)
        
        return {
            'header': header,
            'alignment': alignment,
            'rows': rows
        }
