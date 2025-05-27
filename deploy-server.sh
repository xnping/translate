#!/bin/bash
# 服务器端一键部署脚本
# 在服务器 45.204.6.32 上运行此脚本

set -e

# 配置
PROJECT_DIR="/home/translation-api"
JENKINS_URL="http://你的Jenkins服务器IP:8080"
JOB_NAME="api"

echo "🚀 开始部署翻译API..."

# 创建项目目录
echo "📁 创建项目目录..."
mkdir -p $PROJECT_DIR
cd $PROJECT_DIR

# 停止现有服务
echo "⏹️ 停止现有服务..."
pkill -f "python.*main.py" || true

# 备份现有版本
if [ -d "app" ]; then
    echo "📦 备份现有版本..."
    mv app app.backup.$(date +%Y%m%d-%H%M%S) || true
    mv main.py main.py.backup.$(date +%Y%m%d-%H%M%S) || true
    mv requirements.txt requirements.txt.backup.$(date +%Y%m%d-%H%M%S) || true
fi

# 下载最新构建包（手动方式）
echo "📥 请手动下载最新的构建包..."
echo "1. 访问: $JENKINS_URL/job/$JOB_NAME/lastSuccessfulBuild/"
echo "2. 点击 'Build Artifacts'"
echo "3. 下载 translation-api-*.tar.gz 文件"
echo "4. 上传到服务器的 $PROJECT_DIR 目录"
echo ""
echo "或者如果您已经有构建包，请将其放在当前目录中"
echo ""

# 等待用户上传文件
echo "⏳ 等待构建包上传..."
while true; do
    if ls translation-api-*.tar.gz 1> /dev/null 2>&1; then
        echo "✅ 发现构建包文件"
        break
    fi
    echo "等待构建包文件 (translation-api-*.tar.gz)..."
    sleep 5
done

# 解压构建包
echo "📦 解压构建包..."
PACKAGE_FILE=$(ls translation-api-*.tar.gz | head -1)
tar -xzf $PACKAGE_FILE
echo "✅ 解压完成"

# 安装依赖
echo "🐍 设置Python环境..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
echo "✅ 依赖安装完成"

# 检查配置文件
if [ ! -f ".env" ]; then
    echo "⚙️ 创建配置文件..."
    cat > .env << 'EOF'
# 应用配置
APP_NAME=翻译API服务
VERSION=2.0.0
DEBUG=false
HOST=0.0.0.0
PORT=9000

# Redis配置
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0

# API配置
API_TIMEOUT=30
MAX_TEXT_LENGTH=5000
CACHE_TTL=3600
EOF
    echo "✅ 配置文件已创建"
fi

# 启动服务
echo "🚀 启动服务..."
nohup python main.py > app.log 2>&1 &
sleep 3

# 检查服务状态
if pgrep -f "python.*main.py" > /dev/null; then
    echo "✅ 服务启动成功！"
    echo ""
    echo "📊 服务信息:"
    echo "• 进程ID: $(pgrep -f 'python.*main.py')"
    echo "• 日志文件: $PROJECT_DIR/app.log"
    echo "• 访问地址: http://45.204.6.32:9000"
    echo "• API文档: http://45.204.6.32:9000/docs"
    echo ""
    echo "📋 管理命令:"
    echo "• 查看日志: tail -f $PROJECT_DIR/app.log"
    echo "• 停止服务: pkill -f 'python.*main.py'"
    echo "• 重启服务: $0"
else
    echo "❌ 服务启动失败！"
    echo "查看日志: tail -f app.log"
    exit 1
fi

# 清理
echo "🧹 清理临时文件..."
rm -f $PACKAGE_FILE

echo "🎉 部署完成！"
