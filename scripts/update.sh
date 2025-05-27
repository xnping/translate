#!/bin/bash

# =============================================================================
# 翻译API项目更新脚本
# 用于更新已部署的项目
# =============================================================================

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# 项目配置
PROJECT_NAME="translation-api"
PROJECT_DIR="$HOME/$PROJECT_NAME"

print_message() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查项目是否存在
check_project() {
    if [ ! -d "$PROJECT_DIR" ]; then
        print_error "项目目录不存在: $PROJECT_DIR"
        print_message "请先运行 ./deploy.sh 进行初始部署"
        exit 1
    fi
}

# 备份当前版本
backup_current() {
    print_message "备份当前版本..."
    
    cd "$PROJECT_DIR"
    
    # 创建备份目录
    BACKUP_DIR="backup_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    # 备份关键文件
    cp -r static "$BACKUP_DIR/" 2>/dev/null || true
    cp main.py "$BACKUP_DIR/" 2>/dev/null || true
    cp .env "$BACKUP_DIR/" 2>/dev/null || true
    cp requirements.txt "$BACKUP_DIR/" 2>/dev/null || true
    
    print_message "备份完成: $BACKUP_DIR"
}

# 更新代码
update_code() {
    print_message "更新项目代码..."
    
    cd "$PROJECT_DIR"
    
    # 如果是git仓库
    if [ -d ".git" ]; then
        git pull
    else
        print_warning "不是git仓库，请手动上传新文件"
        read -p "文件已更新完成，按回车继续..."
    fi
}

# 更新依赖
update_dependencies() {
    print_message "更新Python依赖..."
    
    cd "$PROJECT_DIR"
    
    # 激活虚拟环境
    source venv/bin/activate
    
    # 更新依赖
    pip install --upgrade pip
    pip install -r requirements.txt
    
    print_message "依赖更新完成"
}

# 重启服务
restart_service() {
    print_message "重启服务..."
    
    # 重启应用服务
    sudo systemctl restart $PROJECT_NAME
    
    # 重启Nginx
    sudo systemctl restart nginx
    
    # 检查服务状态
    sleep 3
    if sudo systemctl is-active --quiet $PROJECT_NAME; then
        print_message "服务重启成功"
    else
        print_error "服务重启失败"
        sudo systemctl status $PROJECT_NAME
        exit 1
    fi
}

# 检查更新状态
check_update() {
    print_message "检查更新状态..."
    
    # 测试API
    if curl -s http://localhost:9000/health > /dev/null; then
        print_message "API健康检查通过"
    else
        print_error "API健康检查失败"
        exit 1
    fi
    
    print_message "更新完成！"
}

# 主函数
main() {
    echo "========================================"
    echo "    翻译API项目更新脚本"
    echo "========================================"
    echo
    
    check_project
    backup_current
    update_code
    update_dependencies
    restart_service
    check_update
    
    print_message "项目更新完成！"
}

# 运行主函数
main "$@"
