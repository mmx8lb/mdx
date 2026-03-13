# MDX 数据结构说明

本文档详细说明MDX项目中使用的数据结构，包括文档存储、内容类型、表格解析和搜索相关的数据结构。

## 1. 主要文档存储结构

MDX使用**列表**作为主要的文档存储结构，列表中的每个元素代表文档的一个部分。

### 结构定义
```python
parsed_content: List[Tuple[str, Any]]
```

### 示例
```python
[
    ('header', (1, 'Introduction')),
    ('text', 'This is a paragraph'),
    ('code_block', ('python', ['def hello():', '    print("Hello world")'])),
    ('list_item', ('unordered', 'First item')),
    ('table', ['| Header 1 | Header 2 |', '| -------- | -------- |', '| Row 1    | Data 1   |'])
]
```

## 2. 内容类型结构

列表中的每个元素是一个元组 `(item_type, content)`，其中 `item_type` 表示内容类型，`content` 是具体内容。

### 2.1 标题 (header)
```python
('header', (level: int, title: str))
```
- `level`: 标题级别，1-6
- `title`: 标题文本

### 2.2 文本 (text)
```python
('text', content: str)
```
- `content`: 文本内容

### 2.3 代码块 (code_block)
```python
('code_block', (language: str, lines: List[str]))
```
- `language`: 代码语言
- `lines`: 代码行列表

### 2.4 列表项 (list_item)
```python
('list_item', (list_type: str, content: str))
```
- `list_type`: 列表类型，'unordered' 或 'ordered'
- `content`: 列表项内容

### 2.5 引用 (blockquote)
```python
('blockquote', content: str)
```
- `content`: 引用内容

### 2.6 表格 (table)
```python
('table', lines: List[str])
```
- `lines`: 表格行列表

### 2.7 水平分隔线 (hr)
```python
('hr', None)
```

## 3. 表格解析结构

表格被解析为字典结构，包含表头、对齐方式和数据行。

### 结构定义
```python
table_data: Dict[str, Any]
```

### 示例
```python
{
    'header': ['Header 1', 'Header 2'],
    'alignment': ['left', 'center'],
    'rows': [
        ['Row 1', 'Data 1'],
        ['Row 2', 'Data 2']
    ]
}
```

## 4. 搜索相关数据结构

### 4.1 搜索状态
```python
search_term: str  # 搜索词
search_results: List[int]  # 搜索结果的索引列表
current_result_index: int  # 当前结果的索引
```

### 4.2 目录相关数据结构
```python
toc_items: List[Tuple[int, str, int]]  # (级别, 标题, 索引)
current_toc_index: int  # 当前目录项的索引
```

## 5. 渲染器缓存结构

使用LRU缓存来优化渲染性能。

### 结构定义
```python
cache: Cache  # 缓存对象
```

### 缓存键格式
```python
cache_key = f"{item_type}:{content}:{width}"
```

### 缓存值
```python
cached_item: List[str]  # 渲染后的行列表
```

## 6. 主题结构

主题定义了不同元素的颜色。

### 结构定义
```python
theme: Dict[str, Any]
```

### 示例
```python
{
    'header': {
        1: (curses.COLOR_RED, -1),
        2: (curses.COLOR_GREEN, -1),
        # ...
    },
    'list': (curses.COLOR_YELLOW, -1),
    'blockquote': (curses.COLOR_BLUE, -1),
    'code': (curses.COLOR_CYAN, -1),
    'table': (curses.COLOR_MAGENTA, -1),
    'hr': (curses.COLOR_WHITE, -1)
}
```

## 7. 终端信息结构

### 结构定义
```python
size: os.terminal_size
```

### 示例
```python
os.terminal_size(columns=80, lines=24)
```

## 8. 代码渲染器结构

```python
code_renderer: CodeRenderer  # 代码渲染器对象
table_renderer: TableRenderer  # 表格渲染器对象
```

## 9. 总结

MDX使用了以下数据结构组合：

| 结构类型 | 用途 | 示例 |
|---------|------|------|
| 列表 | 存储文档内容顺序 | `[('text', 'content'), ('header', (1, 'Title'))]` |
| 元组 | 存储内容类型和数据 | `('code_block', ('python', ['print("hello")']))` |
| 字典 | 存储表格数据和主题 | `{'header': ['Col1'], 'rows': [['Data1']]}` |

这种混合数据结构设计既保持了文档的顺序性，又能灵活存储不同类型的内容，为MDX的渲染和搜索功能提供了良好的基础。