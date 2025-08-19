"""
使用pypandoc的Markdown转DOCX工具
将Markdown格式的学习笔记转换为Word文档格式
支持完整的Markdown语法和样式
"""

import os
import logging
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any
import pypandoc

class PandocConverter:
    """使用pypandoc的Markdown转DOCX转换器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._check_pandoc_installation()
    
    def _check_pandoc_installation(self):
        """检查pandoc是否正确安装"""
        try:
            # 检查pandoc版本
            result = subprocess.run(['pandoc', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                version_line = result.stdout.split('\n')[0]
                self.logger.info(f"✅ Pandoc已安装: {version_line}")
            else:
                self.logger.warning("⚠️ Pandoc可能未正确安装")
        except Exception as e:
            self.logger.error(f"❌ 检查pandoc安装失败: {e}")
    
    def convert_markdown_to_docx(self, 
                                markdown_file_path: str, 
                                output_path: str = None,
                                reference_doc: str = None) -> str:
        """
        将Markdown文件转换为DOCX文件
        
        Args:
            markdown_file_path: Markdown文件路径
            output_path: 输出DOCX文件路径（可选）
            reference_doc: 参考文档路径（用于样式设置）
            
        Returns:
            str: 生成的DOCX文件路径
        """
        try:
            # 检查输入文件是否存在
            if not Path(markdown_file_path).exists():
                raise FileNotFoundError(f"Markdown文件不存在: {markdown_file_path}")
            
            # 确定输出路径
            if output_path is None:
                markdown_path = Path(markdown_file_path)
                output_path = str(markdown_path.parent / f"{markdown_path.stem}.docx")
            
            # 准备转换参数
            extra_args = []
            
            # 如果有参考文档，添加样式设置
            if reference_doc and Path(reference_doc).exists():
                extra_args.extend(['--reference-doc', reference_doc])
                self.logger.info(f"使用参考文档样式: {reference_doc}")
            
            # 添加其他格式设置
            extra_args.extend([
                '--from', 'markdown',
                '--to', 'docx',
                '--output', output_path,
                '--standalone',
                '--toc',  # 添加目录
                '--number-sections',  # 添加章节编号
                '--highlight-style', 'tango'  # 代码高亮样式
            ])
            
            self.logger.info(f"开始转换: {markdown_file_path} -> {output_path}")
            
            # 使用pypandoc进行转换
            pypandoc.convert_file(
                source_file=markdown_file_path,
                to='docx',
                outputfile=output_path,
                extra_args=extra_args
            )
            
            # 检查输出文件是否生成
            if Path(output_path).exists():
                file_size = Path(output_path).stat().st_size
                self.logger.info(f"✅ 转换成功: {output_path} ({file_size} bytes)")
                return output_path
            else:
                raise FileNotFoundError(f"转换失败，输出文件未生成: {output_path}")
                
        except Exception as e:
            self.logger.error(f"❌ Markdown转DOCX失败: {e}")
            raise
    
    def convert_markdown_string_to_docx(self, 
                                       markdown_content: str, 
                                       output_path: str,
                                       reference_doc: str = None) -> str:
        """
        将Markdown字符串转换为DOCX文件
        
        Args:
            markdown_content: Markdown内容字符串
            output_path: 输出DOCX文件路径
            reference_doc: 参考文档路径（用于样式设置）
            
        Returns:
            str: 生成的DOCX文件路径
        """
        try:
            # 准备转换参数
            extra_args = []
            
            # 如果有参考文档，添加样式设置
            if reference_doc and Path(reference_doc).exists():
                extra_args.extend(['--reference-doc', reference_doc])
                self.logger.info(f"使用参考文档样式: {reference_doc}")
            
            # 添加其他格式设置
            extra_args.extend([
                '--from', 'markdown',
                '--to', 'docx',
                '--standalone',
                '--toc',  # 添加目录
                '--number-sections',  # 添加章节编号
                '--highlight-style', 'tango'  # 代码高亮样式
            ])
            
            self.logger.info(f"开始转换Markdown字符串 -> {output_path}")
            
            # 使用pypandoc进行转换
            pypandoc.convert_text(
                source=markdown_content,
                format='markdown',
                to='docx',
                outputfile=output_path,
                extra_args=extra_args
            )
            
            # 检查输出文件是否生成
            if Path(output_path).exists():
                file_size = Path(output_path).stat().st_size
                self.logger.info(f"✅ 转换成功: {output_path} ({file_size} bytes)")
                return output_path
            else:
                raise FileNotFoundError(f"转换失败，输出文件未生成: {output_path}")
                
        except Exception as e:
            self.logger.error(f"❌ Markdown字符串转DOCX失败: {e}")
            raise
    
    def create_reference_doc(self, output_path: str = "reference.docx") -> str:
        """
        创建一个参考文档，用于设置DOCX样式
        
        Args:
            output_path: 输出参考文档路径
            
        Returns:
            str: 生成的参考文档路径
        """
        try:
            # 创建一个简单的Markdown内容作为模板
            template_content = """# 标题1

## 标题2

### 标题3

这是一个段落，包含**粗体文本**和*斜体文本*。

> 这是一个引用块。

- 无序列表项1
- 无序列表项2
- 无序列表项3

1. 有序列表项1
2. 有序列表项2
3. 有序列表项3

```python
def hello_world():
    print("Hello, World!")
```

| 表格标题1 | 表格标题2 |
|-----------|-----------|
| 内容1     | 内容2     |
| 内容3     | 内容4     |
"""
            
            # 转换为DOCX作为参考文档
            pypandoc.convert_text(
                source=template_content,
                format='markdown',
                to='docx',
                outputfile=output_path,
                extra_args=[
                    '--standalone',
                    '--toc',
                    '--number-sections'
                ]
            )
            
            if Path(output_path).exists():
                self.logger.info(f"✅ 参考文档创建成功: {output_path}")
                return output_path
            else:
                raise FileNotFoundError(f"参考文档创建失败: {output_path}")
                
        except Exception as e:
            self.logger.error(f"❌ 创建参考文档失败: {e}")
            raise
    
    def get_supported_formats(self) -> Dict[str, Any]:
        """
        获取pandoc支持的格式列表
        
        Returns:
            Dict: 支持的输入和输出格式
        """
        try:
            result = subprocess.run(['pandoc', '--list-input-formats'], 
                                  capture_output=True, text=True, timeout=10)
            input_formats = result.stdout.strip().split('\n') if result.returncode == 0 else []
            
            result = subprocess.run(['pandoc', '--list-output-formats'], 
                                  capture_output=True, text=True, timeout=10)
            output_formats = result.stdout.strip().split('\n') if result.returncode == 0 else []
            
            return {
                'input_formats': input_formats,
                'output_formats': output_formats
            }
            
        except Exception as e:
            self.logger.error(f"❌ 获取支持格式失败: {e}")
            return {'input_formats': [], 'output_formats': []}
    
    def convert_to_other_formats(self, 
                                markdown_file_path: str, 
                                output_format: str,
                                output_path: str = None) -> str:
        """
        将Markdown转换为其他格式
        
        Args:
            markdown_file_path: Markdown文件路径
            output_format: 输出格式（如pdf, html, epub等）
            output_path: 输出文件路径（可选）
            
        Returns:
            str: 生成的输出文件路径
        """
        try:
            # 检查输入文件是否存在
            if not Path(markdown_file_path).exists():
                raise FileNotFoundError(f"Markdown文件不存在: {markdown_file_path}")
            
            # 确定输出路径
            if output_path is None:
                markdown_path = Path(markdown_file_path)
                output_path = str(markdown_path.parent / f"{markdown_path.stem}.{output_format}")
            
            self.logger.info(f"开始转换: {markdown_file_path} -> {output_path}")
            
            # 使用pypandoc进行转换
            pypandoc.convert_file(
                source_file=markdown_file_path,
                to=output_format,
                outputfile=output_path,
                extra_args=['--standalone']
            )
            
            # 检查输出文件是否生成
            if Path(output_path).exists():
                file_size = Path(output_path).stat().st_size
                self.logger.info(f"✅ 转换成功: {output_path} ({file_size} bytes)")
                return output_path
            else:
                raise FileNotFoundError(f"转换失败，输出文件未生成: {output_path}")
                
        except Exception as e:
            self.logger.error(f"❌ 转换为{output_format}失败: {e}")
            raise


def main():
    """测试函数"""
    import logging
    
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # 创建转换器
    converter = PandocConverter()
    
    # 测试Markdown内容
    test_markdown = """# 测试文档

## 章节1

这是一个测试文档，用于验证pypandoc转换功能。

### 列表测试

- **粗体项目1**：这是第一个列表项
- **粗体项目2**：这是第二个列表项
- **粗体项目3**：这是第三个列表项

### 引用测试

> 这是一个引用块，用于测试引用格式的转换效果。
> 引用通常用于突出重要的信息或观点。

### 代码块测试

```python
def hello_world():
    print("Hello, World!")
    return "Success"
```

## 章节2：问答格式

*Q：什么是pypandoc？*  
*A：pypandoc是pandoc的Python包装器，用于文档格式转换。*

*Q：为什么要使用pypandoc？*  
*A：pypandoc提供了强大的文档转换能力，支持多种格式。*

## 总结

这个测试文档包含了各种Markdown格式元素，用于验证转换器的功能是否正常。
"""
    
    try:
        # 创建测试目录
        test_dir = Path("test_pandoc")
        test_dir.mkdir(exist_ok=True)
        
        # 保存测试Markdown文件
        markdown_file = test_dir / "test_document.md"
        with open(markdown_file, "w", encoding="utf-8") as f:
            f.write(test_markdown)
        
        logging.info(f"📄 测试Markdown文件已保存: {markdown_file}")
        
        # 转换为DOCX
        docx_file = converter.convert_markdown_to_docx(str(markdown_file))
        
        logging.info(f"✅ 转换成功: {docx_file}")
        
        # 测试字符串转换
        docx_file2 = converter.convert_markdown_string_to_docx(
            test_markdown, 
            str(test_dir / "test_document2.docx")
        )
        
        logging.info(f"✅ 字符串转换成功: {docx_file2}")
        
        # 显示支持的格式
        formats = converter.get_supported_formats()
        logging.info(f"📋 支持的输入格式数量: {len(formats['input_formats'])}")
        logging.info(f"📋 支持的输出格式数量: {len(formats['output_formats'])}")
        
    except Exception as e:
        logging.error(f"❌ 测试失败: {e}")


if __name__ == "__main__":
    main()
