#!/bin/bash

# =============================================================================
# 翻译API项目管理脚本
# 提供启动、停止、重启、状态查看等功能
# =============================================================================

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
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

print_title() {
    echo -e "${BLUE}$1${NC}"
}

# 显示帮助信息
show_help() {
    echo "翻译API项目管理脚本"
    echo
    echo "用法: $0 [命令]"
    echo
    echo "命令:"
    echo "  start     启动服务"
    echo "  stop      停止服务"
    echo "  restart   重启服务"
    echo "  status    查看服务状态"
    echo "  logs      查看服务日志"
    echo "  test      测试API接口"
    echo "  backup    备份项目"
    echo "  help      显示此帮助信息"
    echo
}

# 启动服务
start_service() {
    print_message "启动服务..."
    sudo systemctl start $PROJECT_NAME
    sudo systemctl start nginx
    sleep 2
    show_status
}

# 停止服务
stop_service() {
    print_message "停止服务..."
    sudo systemctl stop $PROJECT_NAME
    print_message "服务已停止"
}

# 重启服务
restart_service() {
    print_message "重启服务..."
    sudo systemctl restart $PROJECT_NAME
    sudo systemctl restart nginx
    sleep 2
    show_status
}

# 查看服务状态
show_status() {
    print_title "=== 服务状态 ==="
    
    # 检查应用服务状态
    if sudo systemctl is-active --quiet $PROJECT_NAME; then
        print_message "应用服务: 运行中 ✅"
    else
        print_error "应用服务: 已停止 ❌"
    fi
    
    # 检查Nginx状态
    if sudo systemctl is-active --quiet nginx; then
        print_message "Nginx服务: 运行中 ✅"
    else
        print_error "Nginx服务: 已停止 ❌"
    fi
    
    # 检查Redis状态
    if sudo systemctl is-active --quiet redis-server; then
        print_message "Redis服务: 运行中 ✅"
    else
        print_error "Redis服务: 已停止 ❌"
    fi
    
    # 检查端口监听
    if netstat -tlnp 2>/dev/null | grep -q ":9000 "; then
        print_message "端口9000: 监听中 ✅"
    else
        print_error "端口9000: 未监听 ❌"
    fi
    
    # 获取服务器IP
    SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || echo "unknown")
    echo
    print_title "=== 访问地址 ==="
    echo "本地: http://localhost:9000"
    echo "外网: http://$SERVER_IP"
}

# 查看日志
show_logs() {
    print_message "查看服务日志 (按Ctrl+C退出)..."
    sudo journalctl -u $PROJECT_NAME -f
}

# 测试API接口
test_api() {
    print_title "=== API接口测试 ==="
    
    # 测试健康检查
    echo -n "健康检查: "
    if curl -s http://localhost:9000/health > /dev/null; then
        echo "✅ 通过"
    else
        echo "❌ 失败"
    fi
    
    # 测试语言列表
    echo -n "语言列表: "
    if curl -s http://localhost:9000/api/languages > /dev/null; then
        echo "✅ 通过"
    else
        echo "❌ 失败"
    fi
    
    # 测试翻译接口
    echo -n "翻译接口: "
    RESULT=$(curl -s -X POST http://localhost:9000/api/translate \
        -H "Content-Type: application/json" \
        -d '{"text":"你好","from_lang":"zh","to_lang":"en"}' 2>/dev/null)
    
    if echo "$RESULT" | grep -q "trans_result"; then
        echo "✅ 通过"
        echo "翻译结果: $(echo "$RESULT" | grep -o '"dst":"[^"]*"' | cut -d'"' -f4)"
    else
        echo "❌ 失败"
    fi
}

# 备份项目
backup_project() {
    print_message "备份项目..."
    
    cd "$PROJECT_DIR"
    
    # 创建备份目录
    BACKUP_DIR="backup_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    # 备份文件
    cp -r static "$BACKUP_DIR/" 2>/dev/null || true
    cp *.py "$BACKUP_DIR/" 2>/dev/null || true
    cp .env "$BACKUP_DIR/" 2>/dev/null || true
    cp requirements.txt "$BACKUP_DIR/" 2>/dev/null || true
    
    # 压缩备份
    tar -czf "${BACKUP_DIR}.tar.gz" "$BACKUP_DIR"
    rm -rf "$BACKUP_DIR"
    
    print_message "备份完成: ${BACKUP_DIR}.tar.gz"
}

# 主函数
main() {
    case "${1:-help}" in
        start)
            start_service
            ;;
        stop)
            stop_service
            ;;
        restart)
            restart_service
            ;;
        status)
            show_status
            ;;
        logs)
            show_logs
            ;;
        test)
            test_api
            ;;
        backup)
            backup_project
            ;;
        help|*)
            show_help
            ;;
    esac
}

# 运行主函数
main "$@"
