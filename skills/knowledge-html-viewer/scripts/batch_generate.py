#!/usr/bin/env python3
"""
批量生成知识库 HTML 文件夹结构

根据配置文件或目录结构，批量生成带嵌套文件夹的 HTML 知识库。
"""

import os
import json
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Any
from generate_html import generate_html, generate_index_html


def scan_markdown_files(source_dir: str) -> Dict[str, Any]:
    """
    扫描目录中的 Markdown 文件，构建目录结构
    
    Args:
        source_dir: 源目录路径
    
    Returns:
        目录结构字典
    """
    structure = {
        'name': os.path.basename(source_dir),
        'path': '',
        'items': []
    }
    
    for item in sorted(os.listdir(source_dir)):
        item_path = os.path.join(source_dir, item)
        
        if os.path.isdir(item_path):
            # 递归扫描子目录
            sub_structure = scan_markdown_files(item_path)
            sub_structure['is_dir'] = True
            structure['items'].append(sub_structure)
        elif item.endswith('.md'):
            # Markdown 文件
            name = os.path.splitext(item)[0]
            structure['items'].append({
                'name': name,
                'source_file': item_path,
                'is_dir': False
            })
    
    return structure


def generate_from_structure(
    structure: Dict[str, Any],
    output_dir: str,
    theme: str = 'light',
    template_path: Optional[str] = None,
    breadcrumb_parts: Optional[List[str]] = None
) -> List[str]:
    """
    根据结构配置生成 HTML 文件
    
    Args:
        structure: 目录结构字典
        output_dir: 输出目录
        theme: 主题
        template_path: 模板路径
        breadcrumb_parts: 当前面包屑路径
    
    Returns:
        生成的文件列表
    """
    generated_files = []
    breadcrumb_parts = breadcrumb_parts or []
    
    os.makedirs(output_dir, exist_ok=True)
    
    # 准备索引页的条目
    index_items = []
    
    for item in structure.get('items', []):
        item_name = item.get('name', 'Untitled')
        
        if item.get('is_dir'):
            # 处理子目录
            sub_output_dir = os.path.join(output_dir, item_name)
            sub_breadcrumb = breadcrumb_parts + [item_name]
            
            sub_files = generate_from_structure(
                structure=item,
                output_dir=sub_output_dir,
                theme=theme,
                template_path=template_path,
                breadcrumb_parts=sub_breadcrumb
            )
            generated_files.extend(sub_files)
            
            index_items.append({
                'name': item_name,
                'path': item_name,
                'is_dir': True,
                'description': item.get('description', '')
            })
        else:
            # 处理文件
            source_file = item.get('source_file')
            content = item.get('content', '')
            
            if source_file and os.path.exists(source_file):
                with open(source_file, 'r', encoding='utf-8') as f:
                    content = f.read()
            
            if content:
                output_file = os.path.join(output_dir, f"{item_name}.html")
                item_breadcrumb = breadcrumb_parts + [item_name]
                
                generate_html(
                    title=item_name,
                    content=content,
                    output_path=output_file,
                    theme=theme,
                    generate_toc=True,
                    template_path=template_path,
                    breadcrumb_parts=item_breadcrumb
                )
                generated_files.append(output_file)
                
                index_items.append({
                    'name': item_name,
                    'path': f"{item_name}.html",
                    'is_dir': False,
                    'description': item.get('description', '')
                })
    
    # 生成索引页
    if index_items:
        index_path = os.path.join(output_dir, 'index.html')
        index_title = structure.get('name', '知识库')
        
        generate_index_html(
            title=index_title,
            items=index_items,
            output_path=index_path,
            theme=theme,
            template_path=template_path,
            breadcrumb_parts=breadcrumb_parts
        )
        generated_files.append(index_path)
    
    return generated_files


def generate_from_config(config_path: str, output_dir: str, theme: str = 'light') -> List[str]:
    """
    从配置文件生成 HTML
    
    配置文件格式 (JSON):
    {
        "name": "知识库名称",
        "items": [
            {
                "name": "章节名称",
                "is_dir": true,
                "items": [...]
            },
            {
                "name": "文档名称",
                "source_file": "path/to/file.md",
                "description": "文档描述"
            },
            {
                "name": "直接内容",
                "content": "# Markdown 内容\\n\\n正文..."
            }
        ]
    }
    """
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    template_path = config.get('template_path')
    
    return generate_from_structure(
        structure=config,
        output_dir=output_dir,
        theme=theme,
        template_path=template_path
    )


def generate_from_markdown_dir(source_dir: str, output_dir: str, theme: str = 'light') -> List[str]:
    """
    扫描 Markdown 目录并生成 HTML
    """
    structure = scan_markdown_files(source_dir)
    
    return generate_from_structure(
        structure=structure,
        output_dir=output_dir,
        theme=theme
    )


def main():
    parser = argparse.ArgumentParser(description='批量生成知识库 HTML')
    parser.add_argument('--source', '-s', help='源 Markdown 目录路径')
    parser.add_argument('--config', '-c', help='配置文件路径 (JSON)')
    parser.add_argument('--output', '-o', required=True, help='输出目录路径')
    parser.add_argument('--theme', default='light', choices=['light', 'dark'], help='主题风格')
    
    args = parser.parse_args()
    
    if args.config:
        files = generate_from_config(args.config, args.output, args.theme)
    elif args.source:
        files = generate_from_markdown_dir(args.source, args.output, args.theme)
    else:
        parser.error('必须指定 --source 或 --config 参数')
    
    print(f"✅ 生成完成！共 {len(files)} 个文件")
    for f in files:
        print(f"   - {f}")


if __name__ == '__main__':
    main()
