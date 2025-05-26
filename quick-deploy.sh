#!/bin/bash

# 快速部署脚本 - 用于更新已部署的服务
# 使用方法: sudo ./quick-deploy.sh

set -e

PROJECT_DIR="/home/translation-service"
SERVICE_NAME="translation-service"
CURRENT_DIR=$(pwd)

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# 检查是否以root权限运行
if [[ $EUID -ne 0 ]]; then
    log_error "此脚本需要root权限运行"
    log_info "请使用: sudo $0"
    exit 1
fi

# 检查服务是否存在
if [ ! -d "$PROJECT_DIR" ]; then
    log_error "项目目录不存在: $PROJECT_DIR"
    log_info "请先运行完整部署脚本: sudo ./deploy-ubuntu.sh"
    exit 1
fi

log_step "开始快速更新部署"

# 停止服务
log_info "停止服务..."
systemctl stop $SERVICE_NAME

# 备份当前配置
log_info "备份配置文件..."
cp $PROJECT_DIR/.env /tmp/.env.backup

# 更新代码
if [ "$CURRENT_DIR" = "$PROJECT_DIR" ]; then
    log_info "当前已在项目目录中，跳过代码复制"
else
    log_info "更新项目代码..."
    cp -r $CURRENT_DIR/* $PROJECT_DIR/
fi
chown -R translation:translation $PROJECT_DIR

# 恢复配置文件
log_info "恢复配置文件..."
cp /tmp/.env.backup $PROJECT_DIR/.env
chown translation:translation $PROJECT_DIR/.env

# 更新Python依赖
log_info "更新Python依赖..."
sudo -u translation $PROJECT_DIR/venv/bin/pip install --upgrade pip
sudo -u translation $PROJECT_DIR/venv/bin/pip install -r $PROJECT_DIR/requirements.txt

# 重启服务
log_info "重启服务..."
systemctl start $SERVICE_NAME

# 等待服务启动
sleep 5

# 验证服务
if systemctl is-active --quiet $SERVICE_NAME; then
    log_info "✓ 服务重启成功"

    # 测试API
    if curl -s http://localhost:9000/health > /dev/null; then
        log_info "✓ API健康检查通过"
    else
        log_warn "✗ API健康检查失败"
    fi
else
    log_error "✗ 服务启动失败"
    journalctl -u $SERVICE_NAME --no-pager -l
    exit 1
fi

log_info "快速部署完成！"
echo ""
echo "管理命令:"
echo "  查看状态: sudo systemctl status $SERVICE_NAME"
echo "  查看日志: sudo journalctl -u $SERVICE_NAME -f"
echo "  快捷管理: $PROJECT_DIR/manage.sh {start|stop|restart|status|logs|test}"
