#!/usr/bin/env python3
"""
Test script for content parser functionality
"""

import sys
from pathlib import Path

# Add current directory to path to import from xhs_upload_main
sys.path.append('.')

from xhs_upload_main import ContentParser

def test_content_parser():
    """测试内容解析功能"""
    print("🧪 Testing Content Parser...")
    
    # 查找内容文件
    processed_dir = Path("processed_videos")
    if not processed_dir.exists():
        print("❌ Processed videos directory not found")
        return False
    
    txt_files = list(processed_dir.glob("*.txt"))
    if not txt_files:
        print("❌ No content files found")
        return False
    
    # 使用最新的文件
    latest_file = max(txt_files, key=lambda f: f.stat().st_mtime)
    print(f"📁 Testing with file: {latest_file.name}")
    
    # 解析内容
    parser = ContentParser()
    content_data = parser.parse_content_file(latest_file)
    
    if not content_data:
        print("❌ Failed to parse content file")
        return False
    
    # 显示解析结果
    print("\n✅ Content parsed successfully!")
    print("="*50)
    print(f"📝 Title: {content_data['title']}")
    print(f"📄 Description length: {len(content_data['description'])} characters")
    print(f"📹 Video path: {content_data['video_path']}")
    print(f"🎬 Original title: {content_data['original_title']}")
    print(f"🔗 YouTube URL: {content_data['youtube_url']}")
    print("="*50)
    
    # 检查视频文件是否存在
    video_path = content_data['video_path']
    if video_path.exists():
        file_size_mb = video_path.stat().st_size / 1024 / 1024
        print(f"✅ Video file exists: {file_size_mb:.1f} MB")
    else:
        print(f"❌ Video file not found: {video_path}")
    
    return True

if __name__ == "__main__":
    success = test_content_parser()
    sys.exit(0 if success else 1)
