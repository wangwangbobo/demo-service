#!/usr/bin/env python3
"""
知识库 HTML 生成器

将 Markdown 内容或文件转换为美观的 HTML 页面，支持：
- 代码高亮（保留 Python 缩进和换行）
- 自动目录生成
- 中文文件名
- 浅色/暗色主题
- 批量生成多个文件
"""

import argparse
import os
import re
import html
from pathlib import Path
from typing import Optional, List, Tuple
import json


def escape_html(text: str) -> str:
    """转义 HTML 特殊字符"""
    return html.escape(text)


def slugify(text: str) -> str:
    """生成 URL 友好的 ID"""
    # 移除 HTML 标签
    text = re.sub(r'<[^>]+>', '', text)
    # 转换为小写，替换空格为连字符
    slug = text.strip().lower()
    slug = re.sub(r'[^\w\u4e00-\u9fff\-]', '-', slug)
    slug = re.sub(r'-+', '-', slug)
    return slug.strip('-')


def parse_markdown_headings(content: str) -> List[Tuple[int, str, str]]:
    """
    解析 Markdown 中的标题，返回 (级别, 标题文本, ID) 列表
    """
    headings = []
    lines = content.split('\n')
    in_code_block = False
    
    for line in lines:
        # 检测代码块
        if line.strip().startswith('```'):
            in_code_block = not in_code_block
            continue
        
        if in_code_block:
            continue
        
        # 匹配标题
        match = re.match(r'^(#{1,6})\s+(.+)$', line)
        if match:
            level = len(match.group(1))
            title = match.group(2).strip()
            heading_id = slugify(title)
            headings.append((level, title, heading_id))
    
    return headings


def generate_toc_html(headings: List[Tuple[int, str, str]]) -> str:
    """
    根据标题列表生成目录 HTML
    """
    if not headings:
        return '<ul><li>暂无目录</li></ul>'
    
    toc_html = []
    current_level = 0
    
    for level, title, heading_id in headings:
        # 调整嵌套层级
        while current_level < level:
            toc_html.append('<ul>')
            current_level += 1
        while current_level > level:
            toc_html.append('</ul>')
            current_level -= 1
        
        toc_html.append(f'<li><a href="#{heading_id}">{escape_html(title)}</a></li>')
    
    # 关闭所有未关闭的标签
    while current_level > 0:
        toc_html.append('</ul>')
        current_level -= 1
    
    return '\n'.join(toc_html)


def convert_code_blocks(content: str) -> str:
    """
    转换 Markdown 代码块为 HTML，保留格式
    """
    def replace_code_block(match):
        lang = match.group(1) or 'text'
        code = match.group(2)
        # 保留原始格式，只转义 HTML
        escaped_code = escape_html(code)
        return f'<pre><code class="language-{lang}">{escaped_code}</code></pre>'
    
    # 匹配 ``` 代码块
    pattern = r'```(\w*)\n(.*?)```'
    content = re.sub(pattern, replace_code_block, content, flags=re.DOTALL)
    
    # 匹配行内代码
    content = re.sub(r'`([^`\n]+)`', r'<code>\1</code>', content)
    
    return content


def convert_markdown_to_html(content: str) -> str:
    """
    将 Markdown 转换为 HTML
    """
    # 先处理代码块（避免被其他规则影响）
    code_blocks = []
    def save_code_block(match):
        idx = len(code_blocks)
        code_blocks.append(match.group(0))
        # 使用不会被 Markdown 规则干扰的占位符
        return f'CODEPLACEHOLDER{idx}ENDCODEPLACEHOLDER'
    
    content = re.sub(r'```\w*\n.*?```', save_code_block, content, flags=re.DOTALL)
    
    # 标题
    def heading_replace(match):
        level = len(match.group(1))
        title = match.group(2).strip()
        heading_id = slugify(title)
        return f'<h{level} id="{heading_id}">{title}</h{level}>'
    
    content = re.sub(r'^(#{1,6})\s+(.+)$', heading_replace, content, flags=re.MULTILINE)
    
    # 粗体和斜体
    content = re.sub(r'\*\*\*(.+?)\*\*\*', r'<strong><em>\1</em></strong>', content)
    content = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', content)
    content = re.sub(r'\*(.+?)\*', r'<em>\1</em>', content)
    content = re.sub(r'___(.+?)___', r'<strong><em>\1</em></strong>', content)
    content = re.sub(r'__(.+?)__', r'<strong>\1</strong>', content)
    content = re.sub(r'_(.+?)_', r'<em>\1</em>', content)
    
    # 链接和图片
    content = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', r'<figure><img src="\2" alt="\1"><figcaption>\1</figcaption></figure>', content)
    content = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', content)
    
    # 引用块
    def blockquote_replace(match):
        text = match.group(0)
        lines = text.split('\n')
        content_lines = [re.sub(r'^>\s?', '', line) for line in lines]
        return f'<blockquote><p>{" ".join(content_lines)}</p></blockquote>'
    
    content = re.sub(r'(?:^>.*\n?)+', blockquote_replace, content, flags=re.MULTILINE)
    
    # 无序列表
    def ul_replace(match):
        text = match.group(0)
        items = re.findall(r'^[\-\*\+]\s+(.+)$', text, flags=re.MULTILINE)
        list_html = '<ul>\n'
        for item in items:
            list_html += f'<li>{item}</li>\n'
        list_html += '</ul>'
        return list_html
    
    content = re.sub(r'(?:^[\-\*\+]\s+.+\n?)+', ul_replace, content, flags=re.MULTILINE)
    
    # 有序列表
    def ol_replace(match):
        text = match.group(0)
        items = re.findall(r'^\d+\.\s+(.+)$', text, flags=re.MULTILINE)
        list_html = '<ol>\n'
        for item in items:
            list_html += f'<li>{item}</li>\n'
        list_html += '</ol>'
        return list_html
    
    content = re.sub(r'(?:^\d+\.\s+.+\n?)+', ol_replace, content, flags=re.MULTILINE)
    
    # 水平线
    content = re.sub(r'^[\-\*_]{3,}\s*$', '<hr>', content, flags=re.MULTILINE)
    
    # 表格
    def table_replace(match):
        text = match.group(0)
        lines = [l.strip() for l in text.strip().split('\n') if l.strip()]
        if len(lines) < 2:
            return text
        
        html_parts = ['<table>']
        
        # 表头
        header_cells = [c.strip() for c in lines[0].strip('|').split('|')]
        html_parts.append('<thead><tr>')
        for cell in header_cells:
            html_parts.append(f'<th>{cell}</th>')
        html_parts.append('</tr></thead>')
        
        # 跳过分隔行（第二行），处理数据行
        html_parts.append('<tbody>')
        for line in lines[2:]:
            cells = [c.strip() for c in line.strip('|').split('|')]
            html_parts.append('<tr>')
            for cell in cells:
                html_parts.append(f'<td>{cell}</td>')
            html_parts.append('</tr>')
        html_parts.append('</tbody></table>')
        
        return '\n'.join(html_parts)
    
    # 匹配 Markdown 表格
    content = re.sub(r'(?:^\|.+\|\n)+', table_replace, content, flags=re.MULTILINE)
    
    # 段落（处理剩余的非空行）
    lines = content.split('\n')
    result_lines = []
    in_paragraph = False
    
    for line in lines:
        stripped = line.strip()
        
        # 跳过已处理的 HTML 元素
        if stripped.startswith('<') and not stripped.startswith('CODEPLACEHOLDER'):
            if in_paragraph:
                result_lines.append('</p>')
                in_paragraph = False
            result_lines.append(line)
        elif stripped == '':
            if in_paragraph:
                result_lines.append('</p>')
                in_paragraph = False
            result_lines.append('')
        elif stripped.startswith('CODEPLACEHOLDER'):
            if in_paragraph:
                result_lines.append('</p>')
                in_paragraph = False
            result_lines.append(line)
        else:
            if not in_paragraph:
                result_lines.append('<p>')
                in_paragraph = True
            result_lines.append(line)
    
    if in_paragraph:
        result_lines.append('</p>')
    
    content = '\n'.join(result_lines)
    
    # 恢复代码块
    for idx, code_block in enumerate(code_blocks):
        # 转换代码块
        match = re.match(r'```(\w*)\n(.*?)```', code_block, flags=re.DOTALL)
        if match:
            lang = match.group(1) or 'text'
            code = match.group(2)
            escaped_code = escape_html(code)
            html_code = f'<pre><code class="language-{lang}">{escaped_code}</code></pre>'
            content = content.replace(f'CODEPLACEHOLDER{idx}ENDCODEPLACEHOLDER', html_code)
    
    return content


def load_template(template_path: Optional[str] = None) -> str:
    """
    加载 HTML 模板
    """
    if template_path and os.path.exists(template_path):
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    # 默认使用同目录下的模板
    default_template = Path(__file__).parent.parent / 'templates' / 'base_template.html'
    if default_template.exists():
        with open(default_template, 'r', encoding='utf-8') as f:
            return f.read()
    
    raise FileNotFoundError("未找到 HTML 模板文件")


def generate_breadcrumb(path_parts: List[str]) -> str:
    """
    生成面包屑导航
    """
    if not path_parts:
        return ''
    
    breadcrumb_html = ['<nav class="breadcrumb">']
    breadcrumb_html.append('<a href="index.html">首页</a>')
    
    for i, part in enumerate(path_parts[:-1]):
        breadcrumb_html.append('<span class="breadcrumb-separator">/</span>')
        # 计算相对路径
        rel_path = '../' * (len(path_parts) - i - 1) + 'index.html'
        breadcrumb_html.append(f'<a href="{rel_path}">{part}</a>')
    
    if len(path_parts) > 0:
        breadcrumb_html.append('<span class="breadcrumb-separator">/</span>')
        breadcrumb_html.append(f'<span>{path_parts[-1]}</span>')
    
    breadcrumb_html.append('</nav>')
    return '\n'.join(breadcrumb_html)


def generate_html(
    title: str,
    content: str,
    output_path: str,
    theme: str = 'light',
    generate_toc: bool = True,
    template_path: Optional[str] = None,
    breadcrumb_parts: Optional[List[str]] = None
) -> str:
    """
    生成单个 HTML 文件
    
    Args:
        title: 页面标题
        content: Markdown 内容
        output_path: 输出文件路径
        theme: 主题 (light/dark)
        generate_toc: 是否生成目录
        template_path: 自定义模板路径
        breadcrumb_parts: 面包屑路径部分
    
    Returns:
        生成的 HTML 文件路径
    """
    # 加载模板
    template = load_template(template_path)
    
    # 解析标题并生成目录
    headings = parse_markdown_headings(content)
    toc_html = generate_toc_html(headings) if generate_toc else ''
    
    # 转换 Markdown 为 HTML
    content_html = convert_markdown_to_html(content)
    
    # 生成面包屑
    breadcrumb_html = generate_breadcrumb(breadcrumb_parts) if breadcrumb_parts else ''
    
    # 填充模板
    html_content = template.replace('{{TITLE}}', escape_html(title))
    html_content = html_content.replace('{{THEME}}', theme)
    html_content = html_content.replace('{{TOC}}', toc_html)
    html_content = html_content.replace('{{CONTENT}}', content_html)
    html_content = html_content.replace('{{BREADCRUMB}}', breadcrumb_html)
    
    # 确保输出目录存在
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # 写入文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    return output_path


def generate_index_html(
    title: str,
    items: List[dict],
    output_path: str,
    theme: str = 'light',
    template_path: Optional[str] = None,
    breadcrumb_parts: Optional[List[str]] = None
) -> str:
    """
    生成索引/导航页面
    
    Args:
        title: 页面标题
        items: 条目列表，每个条目包含 {name, path, is_dir, description}
        output_path: 输出文件路径
        theme: 主题
        template_path: 自定义模板路径
        breadcrumb_parts: 面包屑路径部分
    
    Returns:
        生成的 HTML 文件路径
    """
    # 构建 Markdown 内容
    content_lines = [f'# {title}', '']
    
    # 分离目录和文件
    dirs = [item for item in items if item.get('is_dir')]
    files = [item for item in items if not item.get('is_dir')]
    
    if dirs:
        content_lines.append('## 📁 子目录')
        content_lines.append('')
        for item in dirs:
            desc = f" - {item.get('description', '')}" if item.get('description') else ''
            content_lines.append(f"- [{item['name']}/]({item['path']}/index.html){desc}")
        content_lines.append('')
    
    if files:
        content_lines.append('## 📄 文档')
        content_lines.append('')
        for item in files:
            desc = f" - {item.get('description', '')}" if item.get('description') else ''
            content_lines.append(f"- [{item['name']}]({item['path']}){desc}")
        content_lines.append('')
    
    content = '\n'.join(content_lines)
    
    return generate_html(
        title=title,
        content=content,
        output_path=output_path,
        theme=theme,
        generate_toc=False,
        template_path=template_path,
        breadcrumb_parts=breadcrumb_parts
    )


def main():
    parser = argparse.ArgumentParser(description='知识库 HTML 生成器')
    parser.add_argument('--title', '-t', required=True, help='页面标题')
    parser.add_argument('--content', '-c', required=True, help='Markdown 内容或文件路径')
    parser.add_argument('--output', '-o', required=True, help='输出 HTML 文件路径')
    parser.add_argument('--theme', default='light', choices=['light', 'dark'], help='主题风格')
    parser.add_argument('--toc', type=lambda x: x.lower() == 'true', default=True, help='是否生成目录')
    parser.add_argument('--template', help='自定义模板路径')
    parser.add_argument('--breadcrumb', help='面包屑路径（JSON 数组格式）')
    
    args = parser.parse_args()
    
    # 读取内容
    if os.path.isfile(args.content):
        with open(args.content, 'r', encoding='utf-8') as f:
            content = f.read()
    else:
        # 命令行传入的字符串，将字面量 \n 转换为真正的换行符
        content = args.content.replace('\\n', '\n')
    
    # 解析面包屑
    breadcrumb_parts = None
    if args.breadcrumb:
        try:
            breadcrumb_parts = json.loads(args.breadcrumb)
        except json.JSONDecodeError:
            breadcrumb_parts = args.breadcrumb.split('/')
    
    # 生成 HTML
    output = generate_html(
        title=args.title,
        content=content,
        output_path=args.output,
        theme=args.theme,
        generate_toc=args.toc,
        template_path=args.template,
        breadcrumb_parts=breadcrumb_parts
    )
    
    print(f"✅ 已生成: {output}")


if __name__ == '__main__':
    main()
