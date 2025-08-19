"""
LLM生成笔记工具
负责将商业访谈字幕转换为高质量的Markdown学习笔记
专门针对人物访谈、商业分享、创业经验等内容
"""

import openai
import logging
from typing import Dict, List, Optional
import json
import re
from pathlib import Path
from config import settings

class NoteGenerator:
    """笔记生成器"""
    
    def __init__(self, api_key: str = None):
        """
        初始化笔记生成器
        
        Args:
            api_key: OpenAI API密钥
        """
        self.api_key = api_key or settings.openai_api_key
        if self.api_key:
            openai.api_key = self.api_key
        self.logger = logging.getLogger(__name__)
    
    def generate_learning_notes(self, 
                               transcription: Dict, 
                               video_title: str = "",
                               output_format: str = "markdown") -> Dict:
        """
        基于商业访谈字幕生成学习笔记
        
        Args:
            transcription: 音频转录结果
            video_title: 视频标题
            output_format: 输出格式 ("markdown" 或 "json")
            
        Returns:
            Dict: 学习笔记
        """
        try:
            # 1. 预处理字幕内容
            processed_content = self._preprocess_subtitle_content(transcription)
            
            # 2. 生成学习笔记
            notes = self._generate_notes_from_subtitle(processed_content, video_title)
            
            # 3. 根据格式输出
            if output_format == "markdown":
                markdown_content = self._convert_to_markdown(notes)
                return {
                    "markdown": markdown_content,
                    "json": notes,
                    "metadata": {
                        "title": video_title,
                        "duration": transcription.get("duration", 0),
                        "segments_count": len(transcription.get("segments", [])),
                        "total_text_length": len(processed_content["full_text"])
                    }
                }
            else:
                return notes
                
        except Exception as e:
            self.logger.error(f"学习笔记生成失败: {e}")
            raise
    
    def _preprocess_subtitle_content(self, transcription: Dict) -> Dict:
        """预处理字幕内容"""
        try:
            # 提取完整文本
            full_text = transcription.get("full_text", "")
            segments = transcription.get("segments", [])
            
            # 按时间轴组织内容
            timeline_content = []
            for segment in segments:
                timeline_content.append({
                    "timestamp": segment.get("start", 0),
                    "text": segment.get("text", ""),
                    "confidence": segment.get("confidence", 0)
                })
            
            return {
                "full_text": full_text,
                "timeline_content": timeline_content,
                "original_segments": segments
            }
            
        except Exception as e:
            self.logger.error(f"字幕内容预处理失败: {e}")
            raise
    
    def _generate_notes_from_subtitle(self, processed_content: Dict, title: str) -> Dict:
        """从字幕生成学习笔记"""
        try:
            # 构建增强的prompt
            prompt = self._build_enhanced_prompt(processed_content, title)
            
            # 调用GPT生成笔记
            response = self._call_gpt_for_notes(prompt, title)
            
            # 解析响应
            notes = self._parse_notes_response(response)
            
            return notes
            
        except Exception as e:
            self.logger.error(f"笔记生成失败: {e}")
            raise
    
    def _build_enhanced_prompt(self, processed_content: Dict, title: str) -> str:
        """构建增强的prompt"""
        
        prompt = f"""
你是一位专业的商业分析师和创业导师，并了解AI科技。请基于以下视频的转文字字幕内容，帮助读者生成一份高质量的Markdown格式学习笔记。

视频标题：{title}

字幕内容：
{processed_content['full_text']}

请按照以下要求生成学习笔记：
1. 使用Markdown格式
2. 在讲述具体案例之前，提供相关背景信息，帮助读者建立认知框架
3. 使用引用格式(>)适当加入相关知识、观点来帮助理解和深化内容
4. 用斜体格式模拟笔记作者的思考、提问并模拟导师的回答
   - 格式：*Q：问题内容*  
   - 格式：*A：回答内容*
   - 问题和回答都要有深度、有启发性、有针对性，避免模板化

5. 由于字幕信息有限，请在合适程度帮助学习者进行知识完善和扩展

6. 根据视频标题生成笔记的主标题，格式为：`# {title}`


请为视频观看者生成一份结构清晰、内容丰富的Markdown学习笔记。
"""
        
        return prompt
    
    def _call_gpt_for_notes(self, prompt: str, video_title: str = "商业访谈笔记") -> str:
        """调用GPT生成笔记"""
        try:
            # 使用新版本的OpenAI API
            client = openai.OpenAI(api_key=self.api_key)
            
            response = client.chat.completions.create(
                model=settings.chatgpt_model,
                messages=[
                    {"role": "system", "content": "你是一位专业的商业分析师和创业导师，擅长将商业访谈视频的字幕内容转化为通俗易懂、高质量的学习笔记。请使用简单明了的语言，避免过于学术化的、晦涩难懂的和自己编造的词汇。重点关注商业洞察、战略思维、领导力等实用内容。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=4000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            self.logger.error(f"GPT调用失败: {e}")
            raise
    
    def _parse_notes_response(self, response: str) -> Dict:
        """解析GPT响应"""
        try:
            return {
                "content": response,
                "sections": self._extract_sections(response),
                "keywords": self._extract_keywords(response),
                "backgrounds": self._extract_background_info(response)
            }
        except Exception as e:
            self.logger.error(f"响应解析失败: {e}")
            return {"content": response, "sections": [], "keywords": [], "backgrounds": []}
    
    def _extract_sections(self, content: str) -> List[str]:
        """提取章节标题"""
        sections = []
        lines = content.split('\n')
        for line in lines:
            if line.strip().startswith('#'):
                sections.append(line.strip())
        return sections
    
    def _extract_keywords(self, content: str) -> List[str]:
        """提取关键词（加粗内容）"""
        keywords = re.findall(r'\*\*(.*?)\*\*', content)
        return list(set(keywords))
    
    def _extract_background_info(self, content: str) -> List[str]:
        """提取背景信息建议"""
        backgrounds = re.findall(r'\[(.*?)\] - "(.*?)"', content)
        return [f"{title}: {keyword}" for title, keyword in backgrounds]
    
    def _convert_to_markdown(self, notes: Dict) -> str:
        """转换为Markdown格式"""
        return notes.get("content", "")
    
    def save_notes_to_file(self, notes: Dict, output_path: str, video_title: str = "", filename: str = None):
        """保存笔记到文件"""
        try:
            output_dir = Path(output_path)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # 使用视频标题作为文件名，如果没有提供则使用默认名称
            if filename is None:
                if video_title:
                    # 清理文件名中的特殊字符
                    safe_title = re.sub(r'[<>:"/\\|?*]', '_', video_title)
                    filename = f"{safe_title}_学习笔记.md"
                else:
                    filename = "learning_notes.md"
            
            # 保存Markdown文件
            markdown_path = output_dir / filename
            with open(markdown_path, "w", encoding="utf-8") as f:
                # 优先使用markdown字段，如果没有则使用json.content，最后使用content
                markdown_content = notes.get("markdown") or notes.get("json", {}).get("content") or notes.get("content", "")
                f.write(markdown_content)
            
            # 保存JSON文件（包含元数据）
            json_path = output_dir / f"{Path(filename).stem}.json"
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(notes, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"笔记已保存到: {markdown_path}")
            return str(markdown_path)
            
        except Exception as e:
            self.logger.error(f"笔记保存失败: {e}")
            raise
    
    def generate_notes_from_text(self, text: str, video_title: str = "", output_path: str = "notes") -> str:
        """
        从文本内容生成学习笔记的便捷方法
        
        Args:
            text: 文本内容
            video_title: 视频标题
            output_path: 输出路径
            
        Returns:
            str: 保存的文件路径
        """
        try:
            # 构造转录数据格式
            transcription = {
                "full_text": text,
                "segments": [{"start": 0, "text": text, "confidence": 1.0}],
                "duration": 0
            }
            
            # 生成笔记
            notes = self.generate_learning_notes(transcription, video_title, "markdown")
            
            # 保存到文件
            return self.save_notes_to_file(notes, output_path, video_title)
            
        except Exception as e:
            self.logger.error(f"从文本生成笔记失败: {e}")
            raise
