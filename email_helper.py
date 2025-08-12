import asyncio
import smtplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from config import settings

class EmailHelper:
    def send_video_notification(self, chinese_title: str, chinese_description: str,
                               video_path: Optional[str] = None,
                               original_video_title: str = "",
                               youtube_url: str = "") -> Optional[str]:
        """Send enhanced notification for processed YouTube videos with Chinese content"""
        logging.info(f"[Email] Sending video notification to {settings.user_email}")
        logging.info(f"[Email] Chinese Title: {chinese_title}")
        logging.debug(f"[Email] Chinese Description preview: {chinese_description[:100]}...")
        
        # Create multipart message
        msg = MIMEMultipart('related')
        msg["Subject"] = 'YouTube视频处理完成: ' + chinese_title
        msg["From"] = settings.smtp_user
        msg["To"] = settings.user_email
        msg["Message-ID"] = email.utils.make_msgid()
        message_id = msg["Message-ID"]
        
        logging.debug(f"[Email] Generated Message-ID: {message_id}")

        # Create HTML content
        html_body = self._create_html_email_body(chinese_title, chinese_description, 
                                                original_video_title, youtube_url, video_path)
        
        # Attach HTML content
        html_part = MIMEText(html_body, 'html', 'utf-8')
        msg.attach(html_part)
        
        # Note: We don't attach the video file due to size limitations
        # Instead, we include the local path in the email
        if video_path and Path(video_path).exists():
            logging.info(f"[Email] Video location: {video_path}")
        
        try:
            with smtplib.SMTP(settings.smtp_server, settings.smtp_port) as server:
                logging.debug(f"[Email] Connecting to SMTP server {settings.smtp_server}:{settings.smtp_port}")
                server.starttls()
                server.login(settings.smtp_user, settings.smtp_password.get_secret_value())
                server.send_message(msg)
                logging.info(f"[Email] Successfully sent video notification with Message-ID: {message_id}")
                return message_id
        except Exception as e:
            logging.error(f"[Email] Failed to send video email: {e}")
            return None

    def _create_html_email_body(self, chinese_title: str, chinese_description: str, 
                               original_video_title: str, youtube_url: str,
                               video_path: Optional[str]) -> str:
        """Create HTML email body for video notifications"""
        
        # Format timestamp
        timestamp = datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")
        
        # Determine if video exists locally
        has_video = video_path and Path(video_path).exists()
        video_info = f"<p>🎬 <strong>本地视频:</strong> {Path(video_path).name}</p>" if has_video else ""
        
        # Prepare Chinese description with HTML line breaks
        chinese_description_html = chinese_description.replace('\n', '<br>')
        
        # YouTube URL link
        youtube_link = f'<p>🔗 <strong>原始链接:</strong> <a href="{youtube_url}" target="_blank">{youtube_url}</a></p>' if youtube_url else ""
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>{chinese_title}</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background: linear-gradient(135deg, #ff4757 0%, #ff3838 100%);
                    color: white;
                    padding: 20px;
                    border-radius: 10px 10px 0 0;
                    text-align: center;
                }}
                .content {{
                    background: #f8f9fa;
                    padding: 25px;
                    border-radius: 0 0 10px 10px;
                    border: 1px solid #e9ecef;
                }}
                .chinese-title {{
                    font-size: 24px;
                    font-weight: bold;
                    margin: 0 0 10px 0;
                }}
                .timestamp {{
                    font-size: 14px;
                    opacity: 0.9;
                    margin: 0;
                }}
                .chinese-description {{
                    background: white;
                    padding: 20px;
                    border-radius: 8px;
                    border-left: 4px solid #ff4757;
                    margin: 20px 0;
                    font-size: 16px;
                    line-height: 1.8;
                }}
                .meta-info {{
                    background: #e3f2fd;
                    padding: 15px;
                    border-radius: 8px;
                    margin: 20px 0;
                    font-size: 14px;
                }}
                .meta-info p {{
                    margin: 5px 0;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 30px;
                    padding: 20px;
                    background: #f1f3f4;
                    border-radius: 8px;
                    font-size: 14px;
                    color: #666;
                }}
                .success-badge {{
                    display: inline-block;
                    background: #4caf50;
                    color: white;
                    padding: 4px 12px;
                    border-radius: 20px;
                    font-size: 12px;
                    font-weight: bold;
                    margin-bottom: 10px;
                }}
                .youtube-badge {{
                    display: inline-block;
                    background: #ff4757;
                    color: white;
                    padding: 4px 12px;
                    border-radius: 20px;
                    font-size: 12px;
                    font-weight: bold;
                    margin-left: 10px;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <div class="success-badge">✅ 处理完成</div>
                <span class="youtube-badge">📺 YouTube</span>
                <h1 class="chinese-title">{chinese_title}</h1>
                <p class="timestamp">处理时间: {timestamp}</p>
            </div>
            
            <div class="content">
                <div class="chinese-description">
                    {chinese_description_html}
                </div>
                
                <div class="meta-info">
                    <p>📹 <strong>原视频标题:</strong> {original_video_title}</p>
                    {youtube_link}
                    {video_info}
                    <p>🚀 <strong>状态:</strong> 已自动发布到小红书</p>
                    <p>🎯 <strong>语言:</strong> 英文→中文 (AI翻译)</p>
                </div>
            </div>
            
            <div class="footer">
                <p>🤖 <strong>YouTube 视频处理系统</strong></p>
                <p>此邮件由自动化系统发送，包含从 YouTube 视频中提取并翻译的中文内容。</p>
            </div>
        </body>
        </html>
        """
        
        return html_body

    def send_error_notification(self, error_message: str, video_info: Optional[dict] = None,
                                original_video_title: str = "") -> Optional[str]:
        """Send error notification for failed video processing"""
        logging.info(f"[Email] Sending error notification to {settings.user_email}")
        
        subject = f"❌ YouTube视频处理失败 - {original_video_title}"
        
        # Create multipart message
        msg = MIMEMultipart('related')
        msg["Subject"] = subject
        msg["From"] = settings.smtp_user
        msg["To"] = settings.user_email
        msg["Message-ID"] = email.utils.make_msgid()
        message_id = msg["Message-ID"]

        # Create HTML content for error
        html_body = self._create_error_email_body(error_message, original_video_title, video_info)
        
        # Attach HTML content
        html_part = MIMEText(html_body, 'html', 'utf-8')
        msg.attach(html_part)
        
        try:
            with smtplib.SMTP(settings.smtp_server, settings.smtp_port) as server:
                server.starttls()
                server.login(settings.smtp_user, settings.smtp_password.get_secret_value())
                server.send_message(msg)
                logging.info(f"[Email] Successfully sent error notification with Message-ID: {message_id}")
                return message_id
        except Exception as e:
            logging.error(f"[Email] Failed to send error email: {e}")
            return None

    def _create_error_email_body(self, error_message: str, original_video_title: str, 
                               video_info: Optional[dict]) -> str:
        """Create HTML email body for error notifications"""
        
        timestamp = datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")
        
        # Extract video info if available
        youtube_url = ""
        if video_info:
            youtube_url = video_info.get('url', '')
        
        youtube_link = f'<p>🔗 <strong>视频链接:</strong> <a href="{youtube_url}" target="_blank">{youtube_url}</a></p>' if youtube_url else ""
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>YouTube视频处理失败</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
                    color: white;
                    padding: 20px;
                    border-radius: 10px 10px 0 0;
                    text-align: center;
                }}
                .content {{
                    background: #f8f9fa;
                    padding: 25px;
                    border-radius: 0 0 10px 10px;
                    border: 1px solid #e9ecef;
                }}
                .error-badge {{
                    display: inline-block;
                    background: #dc3545;
                    color: white;
                    padding: 4px 12px;
                    border-radius: 20px;
                    font-size: 12px;
                    font-weight: bold;
                    margin-bottom: 10px;
                }}
                .youtube-badge {{
                    display: inline-block;
                    background: #ff4757;
                    color: white;
                    padding: 4px 12px;
                    border-radius: 20px;
                    font-size: 12px;
                    font-weight: bold;
                    margin-left: 10px;
                }}
                .error-message {{
                    background: #fff5f5;
                    padding: 20px;
                    border-radius: 8px;
                    border-left: 4px solid #dc3545;
                    margin: 20px 0;
                    font-size: 14px;
                    color: #721c24;
                }}
                .meta-info {{
                    background: #fff3cd;
                    padding: 15px;
                    border-radius: 8px;
                    margin: 20px 0;
                    font-size: 14px;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 30px;
                    padding: 20px;
                    background: #f1f3f4;
                    border-radius: 8px;
                    font-size: 14px;
                    color: #666;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <div class="error-badge">❌ 处理失败</div>
                <span class="youtube-badge">📺 YouTube</span>
                <h1>视频处理失败</h1>
                <p>处理时间: {timestamp}</p>
            </div>
            
            <div class="content">
                <div class="error-message">
                    <strong>错误详情:</strong><br>
                    {error_message}
                </div>
                
                <div class="meta-info">
                    <p>📹 <strong>视频标题:</strong> {original_video_title}</p>
                    {youtube_link}
                    <p>🔧 <strong>建议:</strong> 请检查网络连接、API配置和VideoLingo设置，然后重新尝试处理。</p>
                </div>
            </div>
            
            <div class="footer">
                <p>🤖 <strong>YouTube 视频处理系统</strong></p>
                <p>系统将继续监控新的视频。</p>
            </div>
        </body>
        </html>
        """
        
        return html_body

async def main():
    # Example Usage
    helper = EmailHelper()
    
    # Test video notification
    chinese_title = "🚀 AI革命：GPT-5改变世界的10种方式"
    chinese_description = "本视频深入探讨了即将到来的GPT-5如何在教育、医疗、创作等领域带来革命性变化。从提高工作效率到推动科学发现，AI正在重塑我们的未来。"
    video_path = r"C:\Users\xiaowu\tmp\processed\ai_revolution_20250121_143022.mp4"
    original_title = "GPT-5: 10 Ways AI Will Change Everything"
    youtube_url = "https://youtube.com/watch?v=example123"
    
    message_id = helper.send_video_notification(chinese_title, chinese_description, 
                                              video_path, original_title, youtube_url)
    if message_id:
        print(f"Video notification sent with Message-ID: {message_id}")

if __name__ == "__main__":
    asyncio.run(main())
