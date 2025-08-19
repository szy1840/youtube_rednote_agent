import asyncio
import json
import logging
import httpx
from openai import AsyncOpenAI
from pydantic import BaseModel, validator
from typing import Optional
import re

from config import settings

class VideoSummaryContent(BaseModel):
    """Content generated from video subtitles for Xiaohongshu posting"""
    title: str
    description: str
    confidence: float
    is_uncertain: bool = False
    error_message: Optional[str] = None
    
    @validator('title')
    def validate_title_length(cls, v):
        if len(v) > 20:
            logging.warning(f"⚠️  Title exceeds 20 characters ({len(v)}): {v}")
        return v
    
    @validator('description')
    def validate_description_length(cls, v):
        if len(v) < 100:
            logging.warning(f"⚠️  Description too short ({len(v)} < 100): {v}")
        elif len(v) > 800:
            logging.warning(f"⚠️  Description too long ({len(v)} > 800): {v}")
        return v

class LLMClient:
    """LLM client for Xiaohongshu content generation using OpenAI only
    
    VideoLingo handles local LLM processing for video subtitle generation.
    This client focuses on generating Chinese titles and descriptions for Xiaohongshu posting.
    """
    
    def __init__(self):
        # OpenAI client for Xiaohongshu content generation
        self.openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
    
    async def generate_xiaohongshu_content(self, chinese_subtitle_text: str, 
                                          video_title: str = "", 
                                          video_url: str = "") -> VideoSummaryContent:
        """
        Generate Xiaohongshu title and description from VideoLingo's Chinese subtitle text
        Uses OpenAI to create engaging content for Xiaohongshu posting
        """
        logging.info(f"🔍 Starting Xiaohongshu content generation with OpenAI")
        logging.info(f"📝 Chinese subtitle text length: {len(chinese_subtitle_text)} characters")
        logging.info(f"🎬 Video title: {video_title}")
        
        try:
            # Use OpenAI for Xiaohongshu content generation
            result = await self._generate_xiaohongshu_content_with_openai(chinese_subtitle_text, video_title, video_url)
            logging.info("✅ Successfully generated Xiaohongshu content with OpenAI")
            return result
            
        except Exception as e:
            error_msg = str(e)
            logging.error(f"❌ OpenAI content generation failed: {error_msg}")
            
            return VideoSummaryContent(
                title="视频处理失败",
                description=f"抱歉，视频内容总结失败。错误：{error_msg}",
                confidence=0.0,
                is_uncertain=True,
                error_message=error_msg
            )
    

    
    async def _generate_xiaohongshu_content_with_openai(self, chinese_text: str, video_title: str, video_url: str) -> VideoSummaryContent:
        """Generate Xiaohongshu content from Chinese subtitle text"""
        
        
        prompt = f"""你是资深小红书自媒体编辑，也精通创业、商业、科技、AI。请基于以下视频的字幕内容，创作小红书内容。

原视频标题：{video_title}
视频链接：{video_url}

中文字幕内容：
{chinese_text[:6000]}  # Limit to prevent token overflow

任务要求：
1. **中文标题**：创作一个吸引眼球的中文标题（20字以内），要有情感共鸣和话题性
2. **中文描述**：基于视频内容创作小红书风格的描述：
   - 语调生动有趣，符合小红书用户喜好
   - 适当添加emoji表情
   - 要有话题感和互动性
   - 突出重点内容和亮点
   - 描述长度控制在100-600字之间
   - 在生成的文案后，添加一段内容：评论区扣【666】，领取我的独家硬核笔记文档和高能思维导图
   - 最后可以适当添加相关引流话题标签

请用以下JSON格式回复：
{{
  "title": "吸引人的中文标题",
  "description": "详细的中文描述内容",
  "confidence": 0.95
}}"""

        try:
            logging.info(f"🤖 Sending request to OpenAI ChatGPT...")
            logging.info(f"📋 Model: {settings.chatgpt_model}")
            
            response = await self.openai_client.chat.completions.create(
                model=settings.chatgpt_model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=settings.chatgpt_max_tokens,
                timeout=settings.chatgpt_timeout,
                temperature=0.7
            )
            
            content = response.choices[0].message.content
            logging.info(f"📨 OpenAI response received ({len(content)} characters)")
            logging.debug(f"📨 Full OpenAI response: {content}")
            
            return self._parse_llm_response(content)
            
        except Exception as e:
            logging.error(f"❌ OpenAI request failed: {e}")
            raise
    

    
    def _parse_llm_response(self, content: str) -> VideoSummaryContent:
        """Parse LLM response and extract title and description"""
        
        try:
            # First, try direct JSON parsing
            try:
                parsed_content = json.loads(content)
                logging.info(f"✅ Direct JSON parsing successful")
                
            except json.JSONDecodeError:
                # If direct parsing fails, try to extract JSON from markdown code blocks or text
                logging.info(f"🔄 Direct JSON parsing failed, attempting to extract JSON from response...")
                
                # Look for JSON within ```json code blocks
                json_match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                    logging.info(f"🔍 Found JSON in markdown code block")
                else:
                    # Look for any JSON-like structure in the text
                    json_match = re.search(r'\{[^{}]*"title"[^{}]*"description"[^{}]*\}', content, re.DOTALL)
                    if json_match:
                        json_str = json_match.group(0)
                        logging.info(f"🔍 Found JSON-like structure in text")
                    else:
                        # Last resort: look for any object with curly braces
                        json_match = re.search(r'\{.*\}', content, re.DOTALL)
                        if json_match:
                            json_str = json_match.group(0)
                            logging.info(f"🔍 Found generic JSON structure")
                        else:
                            raise json.JSONDecodeError("No JSON found in response", content, 0)
                
                # Clean the JSON string by removing invalid control characters
                json_str = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', json_str)
                parsed_content = json.loads(json_str)
                logging.info(f"✅ Successfully parsed extracted JSON")
            
            # Create result from parsed content
            result = VideoSummaryContent(
                title=parsed_content.get("title", ""),
                description=parsed_content.get("description", ""),
                confidence=parsed_content.get("confidence", 0.8),
                is_uncertain=parsed_content.get("confidence", 0.8) < 0.7
            )
            
            logging.info(f"🎯 Extracted title: {result.title} ({len(result.title)} chars)")
            logging.info(f"🎯 Extracted description: {result.description} ({len(result.description)} chars)")
            logging.info(f"🎯 Confidence: {result.confidence}")
            
            return result
            
        except (json.JSONDecodeError, KeyError) as e:
            logging.error(f"❌ JSON parsing failed: {e}")
            logging.error(f"❌ Unable to parse LLM response. Raw content: {content}")
            
            return VideoSummaryContent(
                title="内容解析失败",
                description="抱歉，无法解析AI返回的内容格式。请检查模型响应。",
                confidence=0.0,
                is_uncertain=True,
                error_message=f"JSON parsing failed: {e}"
            )
    
    async def test_ollama_connection(self) -> bool:
        """
        Test Ollama connection for VideoLingo integration verification
        Note: This client uses OpenAI only. This test is for VideoLingo compatibility.
        """
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                # Test basic connection
                response = await client.get("http://localhost:11434/api/tags")
                response.raise_for_status()
                
                data = response.json()
                models = [model.get("name", "") for model in data.get("models", [])]
                
                if "qwen2.5-coder:32b" in models:
                    logging.info(f"✅ Ollama connection successful. Model 'qwen2.5-coder:32b' is available")
                    return True
                else:
                    logging.warning(f"⚠️ Ollama connected but model 'qwen2.5-coder:32b' not found")
                    logging.info(f"Available models: {models}")
                    return False
                    
        except Exception as e:
            logging.error(f"❌ Ollama connection failed: {e}")
            return False


async def main():
    """Test the LLM client functionality"""
    client = LLMClient()
    
    # Test video summarization
    sample_subtitle = """
    Welcome to today's video about artificial intelligence and its impact on the future of work.
    In this video, we'll explore how AI is transforming various industries and what it means for workers.
    First, let's talk about automation. AI-powered robots are now capable of performing complex tasks
    that were once thought to be exclusively human. This includes everything from manufacturing to
    customer service. However, this doesn't necessarily mean that humans will become obsolete.
    Instead, we're seeing a shift towards human-AI collaboration, where humans focus on creative
    and strategic tasks while AI handles routine operations.
    """
    
    result = await client.generate_xiaohongshu_content(
        sample_subtitle, 
        "AI and the Future of Work", 
        "https://youtube.com/watch?v=example123"
    )
    
    print(f"Title: {result.title}")
    print(f"Description: {result.description}")
    print(f"Confidence: {result.confidence}")

if __name__ == "__main__":
    asyncio.run(main())