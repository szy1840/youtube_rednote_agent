#!/bin/bash

# YouTube RedNote Agent 一键安装脚本 (macOS专用)
# 自动检测已安装的依赖，只安装缺失的组件

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查命令是否存在
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 检查Python包是否已安装
python_package_exists() {
    python3 -c "import $1" >/dev/null 2>&1
}

# 检查Homebrew是否已安装
check_homebrew() {
    if command_exists brew; then
        log_success "✅ Homebrew已安装"
        return 0
    else
        log_warning "❌ Homebrew未安装"
        return 1
    fi
}

# 安装Homebrew
install_homebrew() {
    if ! check_homebrew; then
        log_info "正在安装Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        
        # 添加Homebrew到PATH
        if [[ -f "/opt/homebrew/bin/brew" ]]; then
            echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
            eval "$(/opt/homebrew/bin/brew shellenv)"
        elif [[ -f "/usr/local/bin/brew" ]]; then
            echo 'eval "$(/usr/local/bin/brew shellenv)"' >> ~/.zprofile
            eval "$(/usr/local/bin/brew shellenv)"
        fi
        
        log_success "Homebrew安装完成"
    fi
}

# 检查并安装Python依赖
check_python_dependencies() {
    log_info "检查Python依赖..."
    
    # 检查Python版本
    if command_exists python3; then
        python_version=$(python3 --version)
        log_success "✅ Python已安装: $python_version"
    else
        log_error "❌ Python3未安装"
        return 1
    fi
    
    # 检查pip
    if command_exists pip3; then
        log_success "✅ pip3已安装"
    else
        log_warning "❌ pip3未安装，正在安装..."
        python3 -m ensurepip --upgrade
    fi
    
    # 升级pip
    log_info "升级pip..."
    python3 -m pip install --upgrade pip
    
    # 检查requirements.txt中的主要依赖
    local missing_packages=()
    local required_packages=(
        "pydantic"
        "pydantic_settings" 
        "requests"
        "httpx"
        "openai"
        "yt_dlp"
        "selenium"
        "webdriver_manager"
        "asyncio_mqtt"
        "email_validator"
        "json_repair"
        "google_api_python_client"
        "google_auth_oauthlib"
        "google_auth_httplib2"
        "openpyxl"
        "srt"
        "pypandoc"
    )
    
    for package in "${required_packages[@]}"; do
        if python_package_exists "$package"; then
            log_success "✅ $package 已安装"
        else
            log_warning "❌ $package 未安装"
            missing_packages+=("$package")
        fi
    done
    
    # 安装缺失的包
    if [[ ${#missing_packages[@]} -gt 0 ]]; then
        log_info "安装缺失的Python包..."
        if [[ -f "requirements.txt" ]]; then
            python3 -m pip install -r requirements.txt
        else
            # 安装基础依赖
            python3 -m pip install pydantic>=2.0.0 pydantic-settings>=2.0.0 requests>=2.28.0 httpx>=0.24.0 openai>=1.0.0 yt-dlp>=2023.7.6 selenium>=4.15.0 webdriver-manager>=4.0.0 asyncio-mqtt>=0.11.1 email-validator>=2.0.0 json-repair>=0.7.0 google-api-python-client>=2.0.0 google-auth-oauthlib>=1.0.0 google-auth-httplib2>=0.2.0 openpyxl>=3.0.0 srt>=3.0.0 pypandoc
        fi
        log_success "Python依赖安装完成"
    else
        log_success "所有Python依赖已安装"
    fi
}

# 检查并安装Pandoc
check_pandoc() {
    if command_exists pandoc; then
        pandoc_version=$(pandoc --version | head -n 1)
        log_success "✅ Pandoc已安装: $pandoc_version"
    else
        log_warning "❌ Pandoc未安装，正在安装..."
        if check_homebrew; then
            brew install pandoc
            log_success "Pandoc安装完成"
        else
            log_error "无法安装Pandoc，请手动安装: https://pandoc.org/installing.html"
            return 1
        fi
    fi
}

# 检查并安装Ollama
check_ollama() {
    if command_exists ollama; then
        ollama_version=$(ollama --version)
        log_success "✅ Ollama已安装: $ollama_version"
    else
        log_warning "❌ Ollama未安装，正在安装..."
        curl -fsSL https://ollama.ai/install.sh | sh
        log_success "Ollama安装完成"
    fi
    
    # 检查Ollama服务是否运行
    if pgrep -x "ollama" > /dev/null; then
        log_success "✅ Ollama服务正在运行"
    else
        log_info "启动Ollama服务..."
        ollama serve &
        sleep 3
        
        if pgrep -x "ollama" > /dev/null; then
            log_success "✅ Ollama服务启动成功"
        else
            log_warning "⚠️ Ollama服务启动失败，请手动运行: ollama serve"
        fi
    fi
    
    # 检查常用模型
    log_info "检查Ollama模型..."
    local common_models=("qwen2.5:3b")
    for model in "${common_models[@]}"; do
        if ollama list | grep -q "$model"; then
            log_success "✅ 模型 $model 已下载"
        else
            log_info "下载模型 $model..."
            ollama pull "$model" || log_warning "无法下载模型 $model"
        fi
    done
}

# 检查并安装VideoLingo
check_videolingo() {
    log_info "检查VideoLingo..."
    
    # 检查VideoLingo是否已安装
    if command_exists videolingo; then
        videolingo_version=$(videolingo --version 2>/dev/null || echo "已安装")
        log_success "✅ VideoLingo已安装: $videolingo_version"
        return 0
    fi
    
    # 检查conda环境
    if command_exists conda; then
        log_info "检测到conda，尝试在conda环境中安装VideoLingo..."
        
        # 检查是否存在videolingo环境
        if conda env list | grep -q "videolingo"; then
            log_success "✅ 找到videolingo conda环境"
            
            # 激活环境并检查VideoLingo
            if conda run -n videolingo videolingo --help >/dev/null 2>&1; then
                log_success "✅ VideoLingo在conda环境中可用"
                return 0
            else
                log_info "在videolingo环境中安装VideoLingo..."
                conda run -n videolingo pip install videolingo
                log_success "✅ VideoLingo在conda环境中安装完成"
                return 0
            fi
        else
            log_info "创建videolingo conda环境..."
            conda create -n videolingo python=3.9 -y
            conda run -n videolingo pip install videolingo
            log_success "✅ VideoLingo conda环境创建并安装完成"
            return 0
        fi
    fi
    
    # 如果没有conda，尝试直接安装
    log_warning "❌ VideoLingo未安装，正在尝试直接安装..."
    if python3 -m pip install videolingo; then
        log_success "✅ VideoLingo安装完成"
    else
        log_error "❌ VideoLingo安装失败"
        log_info "请手动安装VideoLingo:"
        echo "   方法1: pip install videolingo"
        echo "   方法2: conda create -n videolingo python=3.9 && conda activate videolingo && pip install videolingo"
        return 1
    fi
}

# 检查并安装Chrome
check_chrome() {
    if command_exists google-chrome; then
        chrome_version=$(google-chrome --version)
        log_success "✅ Chrome已安装: $chrome_version"
    elif [[ -d "/Applications/Google Chrome.app" ]]; then
        log_success "✅ Chrome已安装 (应用程序)"
    else
        log_warning "❌ Chrome未安装，正在安装..."
        if check_homebrew; then
            brew install --cask google-chrome
            log_success "Chrome安装完成"
        else
            log_error "无法安装Chrome，请手动安装"
            return 1
        fi
    fi
}

# 检查并创建项目目录
check_project_directories() {
    log_info "检查项目目录结构..."
    
    local directories=(
        "downloads/input"
        "downloads/processed"
        "processed_videos"
        "chrome_profiles/auto"
        "chrome_profiles/manual"
        "xiaohongshu_extension"
    )
    
    for directory in "${directories[@]}"; do
        if [[ -d "$directory" ]]; then
            log_success "✅ 目录 $directory 已存在"
        else
            log_info "创建目录 $directory..."
            mkdir -p "$directory"
            log_success "✅ 目录 $directory 创建完成"
        fi
    done
}

# 检查并设置环境变量
check_environment() {
    log_info "检查环境变量..."
    
    local project_dir=$(pwd)
    local shell_config=""
    
    # 检测使用的shell配置文件
    if [[ -f ~/.zshrc ]]; then
        shell_config=~/.zshrc
    elif [[ -f ~/.bash_profile ]]; then
        shell_config=~/.bash_profile
    elif [[ -f ~/.bashrc ]]; then
        shell_config=~/.bashrc
    fi
    
    if [[ -n "$shell_config" ]]; then
        if grep -q "YOUTUBE_REDNOTE_PATH" "$shell_config"; then
            log_success "✅ 环境变量已配置"
        else
            log_info "配置环境变量..."
            echo "" >> "$shell_config"
            echo "# YouTube RedNote Agent" >> "$shell_config"
            echo "export YOUTUBE_REDNOTE_PATH=\"$project_dir\"" >> "$shell_config"
            echo "export PATH=\"\$PATH:$project_dir\"" >> "$shell_config"
            log_success "✅ 环境变量配置完成"
        fi
    else
        log_warning "⚠️ 无法找到shell配置文件"
    fi
}

# 验证安装
verify_installation() {
    log_info "验证安装..."
    
    local all_good=true
    
    # 验证Python依赖
    log_info "验证Python依赖..."
    local test_packages=("pydantic" "requests" "yt_dlp" "selenium")
    for package in "${test_packages[@]}"; do
        if python_package_exists "$package"; then
            log_success "✅ $package 验证成功"
        else
            log_error "❌ $package 验证失败"
            all_good=false
        fi
    done
    
    # 验证工具
    log_info "验证工具安装..."
    local tools=(
        ["pandoc"]="Pandoc"
        ["ollama"]="Ollama"
        ["videolingo"]="VideoLingo"
        ["google-chrome"]="Chrome"
    )
    
    for cmd in "${!tools[@]}"; do
        if command_exists "$cmd"; then
            log_success "✅ ${tools[$cmd]} 验证成功"
        else
            log_warning "⚠️ ${tools[$cmd]} 验证失败"
            all_good=false
        fi
    done
    
    # 验证目录
    log_info "验证项目目录..."
    local required_dirs=("downloads/input" "chrome_profiles/auto")
    for dir in "${required_dirs[@]}"; do
        if [[ -d "$dir" ]]; then
            log_success "✅ 目录 $dir 验证成功"
        else
            log_error "❌ 目录 $dir 验证失败"
            all_good=false
        fi
    done
    
    if $all_good; then
        log_success "🎉 所有依赖验证成功！"
    else
        log_warning "⚠️ 部分依赖验证失败，请检查上述错误"
    fi
}

# 显示使用说明
show_usage() {
    log_success "安装检查完成！"
    echo ""
    echo "🎉 YouTube RedNote Agent 依赖检查完成！"
    echo ""
    echo "�� 下一步操作："
    echo "1. 配置 config.py 文件中的API密钥和设置"
    echo "2. 运行测试: python3 test_main_integration.py"
    echo "3. 启动主程序: python3 main.py"
    echo ""
    echo "�� 常用命令："
    echo "- 启动Ollama服务: ollama serve"
    echo "- 下载模型: ollama pull <model_name>"
    echo "- 运行模型: ollama run <model_name>"
    echo "- 查看已安装模型: ollama list"
    echo "- 启动VideoLingo: videolingo"
    echo "- 使用VideoLingo conda环境: conda activate videolingo"
    echo ""
    echo "📚 更多信息请查看 README.md"
    echo ""
    echo "�� 提示：如果遇到权限问题，请确保脚本有执行权限："
    echo "   chmod +x install_dependencies_macos.sh"
}

# 主函数
main() {
    echo "🚀 YouTube RedNote Agent 依赖检查脚本 (macOS)"
    echo "=========================================="
    echo ""
    
    # 检查操作系统
    if [[ "$OSTYPE" != "darwin"* ]]; then
        log_error "此脚本仅支持macOS系统"
        exit 1
    fi
    
    log_info "检测到macOS系统"
    
    # 检查并安装依赖
    install_homebrew
    check_python_dependencies
    check_pandoc
    check_ollama
    check_videolingo
    check_chrome
    check_project_directories
    check_environment
    
    # 验证安装
    verify_installation
    
    # 显示使用说明
    show_usage
}

# 运行主函数
main "$@"


