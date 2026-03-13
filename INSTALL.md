# MDX 安装指南

本指南将帮助您安装和使用 MDX - 一个终端 Markdown 查看器。

## 系统要求

- Python 3.8 或更高版本
- 支持终端的操作系统（Linux, macOS, Windows）

## 安装方法

### 方法一：使用 pip 安装

```bash
# 从 PyPI 安装
pip install mdx-viewer

# 或者从本地安装（开发模式）
cd /path/to/mdx
pip install -e .
```

### 方法二：从源码安装

1. 克隆仓库

```bash
git clone https://github.com/mmx8lb/mdx.git
cd mdx
```

2. 安装依赖

```bash
pip install -r requirements.txt
```

3. 安装 MDX

```bash
pip install .
```

## 依赖项

MDX 依赖以下 Python 包：

- `click>=8.0.0` - 命令行参数处理
- `wcwidth>=0.2.5` - 字符宽度计算（支持中文）
- `pygments>=2.14.0` - 语法高亮
- `markdown>=3.4.0` - Markdown 解析

## 使用方法

### 基本使用

```bash
# 查看 Markdown 文件
mdx README.md

# 显示目录
mdx README.md --toc

# 执行代码块
mdx README.md --execute

# 跳转到指定行
mdx README.md --line 100

# 使用不同主题
mdx README.md --theme dracula
```

### 快捷键

- `q` - 退出
- `j`/`↓` - 向下滚动
- `k`/`↑` - 向上滚动
- `g` - 滚动到顶部
- `G` - 滚动到底部
- `Space`/`f` - 向下翻页
- `b` - 向上翻页
- `/` - 搜索（待实现）
- `n` - 下一个搜索结果（待实现）
- `N` - 上一个搜索结果（待实现）

## 主题

MDX 支持以下主题：

- `monokai` (默认)
- `dracula`
- `github-dark`
- `nord`
- `solarized-dark`

## 故障排除

### 问题：缺少依赖项

**解决方案**：安装缺少的依赖项

```bash
pip install wcwidth pygments markdown
```

### 问题：终端显示乱码

**解决方案**：确保终端支持 UTF-8 编码，并且使用支持 Unicode 的字体。

### 问题：表格渲染不正确

**解决方案**：确保终端宽度足够，或者使用较小的字体。

### 问题：代码块显示不完整

**解决方案**：确保终端宽度足够，或者使用较小的字体。

## 开发

### 运行测试

```bash
pytest
```

### 构建包

```bash
python -m build
```

### 发布到 PyPI

```bash
twine upload dist/*
```

## 许可证

MDX 使用 MIT 许可证，详见 LICENSE 文件。