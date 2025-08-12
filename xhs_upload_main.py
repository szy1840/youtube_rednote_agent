#!/usr/bin/env python3
"""
Xiaohongshu Upload Test Script
专门用于测试小红书上传功能，读取已有的内容文件并上传
"""

import asyncio
import logging
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional
import re

from xiaohongshu_selenium import XiaohongshuSelenium

# Configure logging
def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )

class ContentParser:
    """解析内容文件的工具类"""
    
    @staticmethod
    def parse_content_file(file_path: Path) -> Optional[Dict[str, Any]]:
        """解析内容文件，提取标题、描述和视频路径"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 提取标题
            title_match = re.search(r'=== GENERATED TITLE ===\s*\n\s*(.+?)\s*\n', content, re.DOTALL)
            if not title_match:
                logging.error("❌ Could not find title in content file")
                return None
            title = title_match.group(1).strip()
            
            # 提取描述
            desc_match = re.search(r'=== GENERATED DESCRIPTION ===\s*\n\s*(.+?)\s*\n\s*=== INSTRUCTIONS ===', content, re.DOTALL)
            if not desc_match:
                logging.error("❌ Could not find description in content file")
                return None
            description = desc_match.group(1).strip()
            
            # 提取视频路径
            video_path_match = re.search(r'Output Video Path: (.+?)\s*\n', content)
            if not video_path_match:
                logging.error("❌ Could not find video path in content file")
                return None
            video_path = Path(video_path_match.group(1).strip())
            
            # 提取原始视频信息
            original_title_match = re.search(r'Original Video Title: (.+?)\s*\n', content)
            original_title = original_title_match.group(1).strip() if original_title_match else "Unknown"
            
            youtube_url_match = re.search(r'YouTube URL: (.+?)\s*\n', content)
            youtube_url = youtube_url_match.group(1).strip() if youtube_url_match else ""
            
            return {
                'title': title,
                'description': description,
                'video_path': video_path,
                'original_title': original_title,
                'youtube_url': youtube_url,
                'content_file': file_path
            }
            
        except Exception as e:
            logging.error(f"❌ Error parsing content file: {e}")
            return None

class XHSUploadTester:
    """小红书上传测试器"""
    
    def __init__(self):
        self.content_parser = ContentParser()
        self.uploader = XiaohongshuSelenium()
    
    def find_latest_content_file(self, processed_dir: Path = Path("processed_videos")) -> Optional[Path]:
        """找到最新的内容文件"""
        try:
            if not processed_dir.exists():
                logging.error(f"❌ Processed videos directory not found: {processed_dir}")
                return None
            
            # 查找所有.txt文件
            txt_files = list(processed_dir.glob("*.txt"))
            if not txt_files:
                logging.error(f"❌ No content files found in {processed_dir}")
                return None
            
            # 按修改时间排序，返回最新的
            latest_file = max(txt_files, key=lambda f: f.stat().st_mtime)
            logging.info(f"📁 Found latest content file: {latest_file.name}")
            return latest_file
            
        except Exception as e:
            logging.error(f"❌ Error finding content file: {e}")
            return None
    
    def validate_video_file(self, video_path: Path) -> bool:
        """验证视频文件是否存在"""
        if not video_path.exists():
            logging.error(f"❌ Video file not found: {video_path}")
            return False
        
        # 检查文件大小
        file_size_mb = video_path.stat().st_size / 1024 / 1024
        logging.info(f"📹 Video file size: {file_size_mb:.1f} MB")
        
        if file_size_mb < 1:
            logging.warning("⚠️ Video file seems too small (< 1MB)")
            return False
        
        return True
    
    async def test_upload(self, content_file_path: Optional[Path] = None, headless: bool = False) -> bool:
        """测试上传功能"""
        try:
            # 1. 找到内容文件
            if content_file_path is None:
                content_file_path = self.find_latest_content_file()
                if not content_file_path:
                    return False
            
            logging.info(f"📄 Using content file: {content_file_path.name}")
            
            # 2. 解析内容
            content_data = self.content_parser.parse_content_file(content_file_path)
            if not content_data:
                return False
            
            title = content_data['title']
            description = content_data['description']
            video_path = content_data['video_path']
            original_title = content_data['original_title']
            
            logging.info(f"🎬 Original video: {original_title}")
            logging.info(f"📝 Generated title: {title}")
            logging.info(f"📄 Description length: {len(description)} characters")
            logging.info(f"📹 Video path: {video_path}")
            
            # 3. 验证视频文件
            if not self.validate_video_file(video_path):
                return False
            
            # 4. 显示上传配置
            print("\n" + "="*60)
            print("🚀 XIAOHONGSHU UPLOAD TEST CONFIGURATION")
            print("="*60)
            print(f"📁 Content file: {content_file_path.name}")
            print(f"🎬 Video: {video_path.name}")
            print(f"📝 Title: {title}")
            print(f"📄 Description: {description[:100]}...")
            print(f"🌐 Headless mode: {'Yes' if headless else 'No'}")
            print("="*60)
            
            # 5. 确认上传
            if not headless:
                confirm = input("\n🤔 Do you want to proceed with the upload? (y/N): ")
                if confirm.lower() != 'y':
                    print("❌ Upload cancelled by user")
                    return False
            
            # 6. 执行上传
            logging.info("🚀 Starting Xiaohongshu upload process...")
            success = self.uploader.run_upload_process(video_path, title, description, headless=headless)
            
            if success:
                logging.info("✅ Upload completed successfully!")
                print("\n🎉 Upload test completed successfully!")
                print("💡 Check your Xiaohongshu account to see the published video")
            else:
                logging.error("❌ Upload failed")
                print("\n❌ Upload test failed")
                print("💡 Check the logs above for error details")
            
            return success
            
        except Exception as e:
            logging.error(f"❌ Upload test failed with error: {e}")
            return False

async def main():
    """主函数"""
    setup_logging()
    
    print("📱 XIAOHONGSHU UPLOAD TESTER")
    print("专门用于测试小红书上传功能")
    print("="*50)
    
    # 创建测试器
    tester = XHSUploadTester()
    
    # 检查命令行参数
    headless = "--headless" in sys.argv
    
    if "--help" in sys.argv or "-h" in sys.argv:
        print("\n使用方法:")
        print("  python xhs_upload_main.py                    # 使用最新内容文件，可见模式")
        print("  python xhs_upload_main.py --headless         # 使用最新内容文件，后台模式")
        print("  python xhs_upload_main.py <content_file>     # 使用指定内容文件")
        print("\n参数说明:")
        print("  --headless   在后台运行（不显示浏览器窗口）")
        print("  --help, -h   显示帮助信息")
        return
    
    # 检查是否有指定的内容文件
    content_file = None
    for arg in sys.argv[1:]:
        if not arg.startswith("--"):
            content_file = Path(arg)
            break
    
    # 执行上传测试
    success = await tester.test_upload(content_file, headless)
    
    if success:
        print("\n✅ Test completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Test failed!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
