# YouTube RedNote Agent - YouTube视频自动处理与小红书发布系统

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

一个智能的自动化系统，用于监控YouTube播放列表，下载视频，生成字幕，创建小红书内容并自动发布。

## 🚀 功能特性

### 核心功能
- **YouTube播放列表监控**: 自动检测新视频并下载
- **视频处理**: 使用VideoLingo进行视频转录和字幕生成
- **AI内容生成**: 基于视频内容自动生成小红书文案
- **自动发布**: 通过Chrome配置文件记录小红书账号，自动发布到小红书
- **邮件通知**: 处理状态和错误通知

### 技术特性
- **智能重试机制**: 失败自动重试，确保任务完成
- **定时任务**: 支持cron定时执行
- **详细日志**: 完整的处理日志和状态跟踪
- **配置管理**: 基于Pydantic的配置系统

## 📋 系统要求

- Python 3.8+
- Chrome浏览器
- VideoLingo (视频处理工具)
- Ollama (本地LLM服务)

## 🛠️ 核心技术栈

### 核心框架与库

- **Pydantic**: 数据验证和配置管理框架，用于配置文件管理、API响应验证和类型安全的数据处理。项目中使用Pydantic Settings进行配置管理，确保配置数据的类型安全和验证。

- **Selenium**: 完整的Web自动化框架，用于小红书自动登录、内容发布、表单填写和页面交互。
  - **WebDriver**: 定义与浏览器通信的标准接口，接口层。项目中使用ChromeDriver作为WebDriver的具体实现，通过多种方式（webdriver-manager自动下载、手动下载、系统安装）确保ChromeDriver的可用性。
  - **ChromeDriver**: 实际控制Chrome浏览器进行自动化操作，包括反检测处理（移除webdriver属性）和多账号配置文件管理。

- **yt-dlp**: 强大的视频下载工具，用于从YouTube下载视频文件。使用yt-dlp替代传统的youtube-dl，提供更好的下载稳定性和格式支持。

- **Google API - YouTube Data API v3**: YouTube数据访问服务，用于播放列表监控、视频信息获取和OAuth2认证管理。项目用于获取播放列表中的新视频信息。

> **Playwright**: 现代浏览器自动化框架，由微软开源。作用类似于Selenium，但更现代、更稳定，对反爬虫和抓取动态页面等场景有更好的支持。


### 外部服务与平台

- **VideoLingo**: 专业的视频转录和字幕生成工具，通过subprocess调用处理下载的视频，生成中英文字幕。项目使用VideoLingo进行视频的转录、翻译和字幕生成。
  - **Streamlit**: VideoLingo基于Streamlit快速构建Data Apps，通过Streamlit提供可视化的转录、字幕生成和进度监控界面，便于用户操作和查看处理结果。

- **Ollama**: 本地大语言模型服务，运行qwen2.5-coder:32b模型。项目中VideoLingo使用该服务进行字幕翻译。

- **YouTube Data API v3**: YouTube官方数据访问服务，通过OAuth2认证获取播放列表、视频元数据、频道信息。项目使用此API监控指定播放列表的新视频。

- **Gmail SMTP**: 邮件通知服务，用于处理状态通知、错误报告和任务完成提醒。项目集成Gmail SMTP服务发送处理状态邮件。

### 数据处理与存储

- **SRT**: 字幕文件格式解析库，用于解析VideoLingo生成的字幕文件，提取文本内容。项目处理SRT格式的字幕文件，提取中文文本用于内容生成。

- **OpenPyXL**: Excel文件读写处理库，用于处理VideoLingo的状态跟踪文件，读取处理进度。项目读取Excel格式的处理状态文件，监控视频处理进度。

- **Pathlib**: 跨平台路径管理库，用于文件路径处理、目录操作和路径验证。项目使用Pathlib进行跨平台的文件路径操作。

### 开发与部署工具

- **Cron**: 定时任务工具，用于定期执行视频处理任务。项目使用cron实现自动化定时执行。


## 🛠️ 安装步骤

### 1. 克隆项目
```bash
git clone <repository-url>
cd youtube_rednote_agent
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 配置环境

#### 3.1 复制配置文件模板
```bash
# 复制配置文件模板
cp config.example.py config.py
```

#### 3.2 编辑配置文件
编辑 `config.py` 文件，设置以下必要参数：

```python
# YouTube API设置
youtube_playlist_id: str = "YOUR_PLAYLIST_ID"

# OpenAI API (用于内容生成)
openai_api_key: str = "YOUR_OPENAI_API_KEY"

# 邮箱设置
smtp_user: str = "YOUR_GMAIL"
smtp_password: str = "YOUR_APP_PASSWORD"
user_email: str = "YOUR_EMAIL"

# 路径设置
videolingo_path: str = "/path/to/VideoLingo"
```

> **重要提醒**: 请确保复制 `config.example.py` 为 `config.py` 后再进行编辑，避免直接修改模板文件。配置文件包含敏感信息，请妥善保管。
> 
> **路径说明**: `download_folder_path` 已设置为相对路径 `"downloads/input"`，会自动指向项目根目录下的 `downloads/input` 文件夹，无需手动配置。

### 4. 配置OAuth2认证
1. 配置YouTube Data API v3，下载Google OAuth2客户端配置文件
2. 重命名为 `client_secret_*.json`
3. 首次运行时会引导完成OAuth2认证


## 🚀 使用方法

### 手动运行
```bash
python main.py
```

### 定时任务设置
```bash
# 编辑crontab
crontab -e

# 添加定时任务 (每小时执行一次)
0 * * * * /path/to/youtube_rednote_agent/cron_job.sh
```

## 📁 项目结构

```
youtube_rednote_agent/
├── main.py                    # 主程序入口
├── config.py                  # 配置管理
├── config.example.py          # 配置文件模板
├── youtube_helper.py          # YouTube API助手
├── video_processor.py         # 视频处理模块
├── xiaohongshu_selenium.py    # 小红书自动化
├── llm_client.py              # AI客户端
├── email_helper.py            # 邮件通知
├── xhs_account_manager.py     # 账号管理
├── post_xhs_video.py          # 视频发布脚本
├── xhs_upload_main.py         # 小红书上传主程序
├── monitor_running.py         # 系统监控脚本
├── requirements.txt           # 依赖列表
├── cron_job.sh               # 定时任务脚本
├── cron_job.example.sh       # cron任务脚本模板
├── .gitignore                # Git忽略文件
├── downloads/                # 下载目录
│   ├── input/               # 原始视频
│   └── processed/           # 处理后的视频
├── processed_videos/         # 处理记录目录
├── chrome_profiles/          # Chrome配置文件
│   ├── auto/                # 自动发布账号
│   └── manual/              # 手动账号
├── xiaohongshu_extension/    # 浏览器扩展
├── test_content_parser.py    # 内容解析测试
├── processed_videos.json     # 已处理视频记录
├── video_attempts.json       # 处理尝试记录
├── youtube_token.json        # YouTube认证令牌
├── client_secret_*.json      # OAuth2客户端配置
└── fill_content_error.png    # 错误截图示例
```

## 🔄 工作流程

1. **监控播放列表**: 定期检查YouTube播放列表中的新视频
2. **下载视频**: 使用yt-dlp下载视频到本地
3. **视频处理**: 使用VideoLingo进行转录和字幕生成
4. **内容生成**: 使用AI生成小红书文案和标签
5. **自动发布**: 通过Selenium自动发布到小红书
6. **状态通知**: 发送邮件通知处理结果

## ⚠️ 项目局限性

### 视频处理限制
- **翻译方向固定**: 目前仅支持英语到中文的翻译，源语言硬编码为英语（'en'），目标语言为中文。不支持其他语言对的翻译。
- **忽略已有字幕**: VideoLingo 会忽略视频中已有的字幕，对所有视频都进行语音识别和翻译。好处是不依赖视频原有的字幕质量。

### 平台兼容性
- **操作系统限制**: 当前主要针对macOS优化，包含macOS特定的路径配置（如`/Applications/Google Chrome.app`）和AppleScript自动化脚本。


### 自动化限制
- **小红书反检测**: 虽然实现了反检测机制，但平台可能会更新检测算法，需要持续维护。
- **账号管理**: 依赖Chrome配置文件管理多账号，需要手动预先登录账号。
- **扩展功能**: 浏览器扩展加载功能目前被禁用，需要手动加载。

### 处理能力限制
- **并发处理**: 当前设置为单线程处理（`max_concurrent_processing: int = 1`），不支持并行处理多个视频。

### 配置限制
- **硬编码路径**: 包含多个硬编码的路径配置，在不同环境下需要手动调整。
- **环境依赖**: 依赖特定的conda环境（videolingo），环境配置复杂。
- **权限要求**: 需要系统级权限进行进程管理和文件操作。



## 📊 监控和状态

### 状态文件
- `processed_videos.json`: 已处理视频记录
- `video_attempts.json`: 处理尝试记录
- `youtube_token.json`: YouTube认证令牌

### 监控脚本
```bash
# 检查系统状态
python monitor_running.py
```

## 🔒 安全注意事项

1. **API密钥保护**: 不要在代码中硬编码API密钥
2. **OAuth2令牌**: 定期刷新认证令牌
3. **Chrome配置文件**: 保护账号登录状态


## 📄 许可证

本项目采用MIT许可证 - 查看 [LICENSE](LICENSE) 文件了解详情



**注意**: 本项目仅供学习和研究使用，请遵守相关平台的使用条款和法律法规。
