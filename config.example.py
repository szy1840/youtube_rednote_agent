import pydantic_settings
import pydantic
import os
from pathlib import Path


class Settings(pydantic_settings.BaseSettings):
    # Video processing settings
    download_folder_path: str = "downloads/input"
    processed_folder_name: str = "processed"
    supported_video_formats: list[str] = [".mp4", ".webm", ".mkv", ".avi"]
    video_quality: str = "medium"  # yt-dlp quality setting
    
    # YouTube API settings (using OAuth2 authentication)
    youtube_playlist_id: str = "YOUR_YOUTUBE_PLAYLIST_ID"  # 需要替换为实际的YouTube播放列表ID
    
    
    # ChatGPT for summarization (fallback if needed)
    openai_api_key: str = "YOUR_OPENAI_API_KEY"  # 需要替换为实际的OpenAI API密钥
    chatgpt_model: str = "gpt-4o"
    chatgpt_max_tokens: int = 1000
    chatgpt_timeout: int = 60  # seconds

    # Email credentials (same as screenshot processor)
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = "your_email@gmail.com"  # 需要替换为实际的Gmail地址
    smtp_password: pydantic.SecretStr = "YOUR_GMAIL_APP_PASSWORD"  # 需要替换为Gmail应用密码
    user_email: str = "your_email@gmail.com"  # 需要替换为实际的Email地址

    # Xiaohongshu posting settings (temporarily disabled for testing)
    xhs_auto_post: bool = True
    
    # Chrome Profile settings
    chrome_profiles_dir: str = "chrome_profiles"
    
    # Xiaohongshu account settings (using relative paths)
    xhs_accounts: dict[str, dict] = {
        "auto": {
            "name": "Auto-Posting Account",
            "chrome_profile": "chrome_profiles/auto",
            "enabled": True,
            "description": "Account for automated posting from YouTube videos"
        },
        "manual": {
            "name": "Manual Account", 
            "chrome_profile": "chrome_profiles/manual",
            "enabled": True,
            "description": "Account for manual posting and personal use"
        }
    }
    
    # Auto-posting account (always uses the 'auto' account - never changes)
    xhs_default_account: str = "auto"
    
    # Processing settings
    max_concurrent_processing: int = 1  # Process videos sequentially
    max_retries: int = 3  # Same retry logic as screenshot processor
    
    # Python executable path (updated for macOS maker environment)
    python_executable: str = "/path/to/your/python"  # 更新为当前系统的Python路径
    
    # VideoLingo settings
    videolingo_path: str = "/path/to/VideoLingo"  # VideoLingo 安装路径
    videolingo_port: int = 8501  # VideoLingo Web UI 端口（Streamlit 默认端口）
    
    # Excel file path for VideoLingo
    videolingo_excel_path: str = "/path/to/VideoLingo/batch/tasks_setting.xlsx"
    
    # Test video path
    test_video_path: str = "/path/to/test_video.mp4"
    
    # Extension path
    xiaohongshu_extension_path: str = "xiaohongshu_extension"
    
    # Cron job settings
    cron_log_path: str = "/path/to/cron_log.txt"
    project_root_path: str = "/path/to/project/root"
    
    @property
    def processed_folder_path(self) -> str:
        """Get the full path to the processed folder"""
        # Normalize path separators for cross-platform compatibility
        expanded_path = os.path.normpath(self.download_folder_path)
        return os.path.join(expanded_path, self.processed_folder_name)
    
    @property
    def download_folder_path_normalized(self) -> str:
        """Get normalized download folder path"""
        return os.path.normpath(self.download_folder_path)
    
    @property
    def auto_chrome_profile_path(self) -> str:
        """Get auto Chrome profile path"""
        return str(Path(self.chrome_profiles_dir) / "auto")
    
    @property
    def manual_chrome_profile_path(self) -> str:
        """Get manual Chrome profile path"""
        return str(Path(self.chrome_profiles_dir) / "manual")
    
    def get_chrome_profile_path(self, profile_type: str = "auto") -> str:
        """Get Chrome profile path by type"""
        if profile_type == "auto":
            return self.auto_chrome_profile_path
        elif profile_type == "manual":
            return self.manual_chrome_profile_path
        else:
            raise ValueError(f"Unknown profile type: {profile_type}")
    
    def setup_chrome_profiles(self) -> bool:
        """Setup Chrome profile directories"""
        try:
            auto_path = Path(self.auto_chrome_profile_path)
            manual_path = Path(self.manual_chrome_profile_path)
            
            auto_path.mkdir(parents=True, exist_ok=True)
            manual_path.mkdir(parents=True, exist_ok=True)
            
            return True
        except Exception as e:
            print(f"❌ Failed to setup Chrome profiles: {e}")
            return False

settings = Settings()
