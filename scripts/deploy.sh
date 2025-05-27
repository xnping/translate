#!/bin/bash
# 翻译API项目部署脚本
# 支持手动部署和Jenkins自动部署

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置变量
PROJECT_NAME="translation-api"
DEPLOY_USER="root"
DEPLOY_HOST="8.138.177.105"
DEPLOY_PORT="9000"
PROJECT_PATH="/home/translation-api"
BACKUP_PATH="/home/backups/translation-api"
SERVICE_NAME="translation-api"

# 函数定义
print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE} $1${NC}"
    echo -e "${BLUE}================================${NC}"
}

print_step() {
    echo -e "${GREEN}[$(date '+%H:%M:%S')] $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# 检查依赖
check_dependencies() {
    print_step "检查部署依赖..."
    
    # 检查SSH连接
    if ! ssh -o ConnectTimeout=5 -o BatchMode=yes $DEPLOY_USER@$DEPLOY_HOST exit 2>/dev/null; then
        print_error "无法连接到服务器 $DEPLOY_HOST"
        echo "请确保:"
        echo "1. SSH密钥已配置"
        echo "2. 服务器可访问"
        echo "3. 用户权限正确"
        exit 1
    fi
    
    print_success "SSH连接正常"
}

# 创建备份
create_backup() {
    print_step "创建备份..."
    
    ssh $DEPLOY_USER@$DEPLOY_HOST << EOF
        mkdir -p $BACKUP_PATH
        
        if [ -d "$PROJECT_PATH" ]; then
            BACKUP_NAME="backup_\$(date +%Y%m%d_%H%M%S)"
            cd $PROJECT_PATH
            tar -czf "$BACKUP_PATH/\$BACKUP_NAME.tar.gz" . 2>/dev/null || true
            echo "备份创建: \$BACKUP_NAME.tar.gz"
            
            # 保留最近5个备份
            cd $BACKUP_PATH
            ls -t *.tar.gz 2>/dev/null | tail -n +6 | xargs -r rm -f
            echo "清理旧备份完成"
        fi
EOF
    
    print_success "备份创建完成"
}

# 停止服务
stop_service() {
    print_step "停止服务..."
    
    ssh $DEPLOY_USER@$DEPLOY_HOST << EOF
        # 停止systemd服务
        if systemctl is-active --quiet $SERVICE_NAME; then
            systemctl stop $SERVICE_NAME
            echo "systemd服务已停止"
        fi
        
        # 停止可能的进程
        pkill -f "python.*main.py" 2>/dev/null || true
        pkill -f "uvicorn.*main" 2>/dev/null || true
        
        # 等待进程完全停止
        sleep 2
EOF
    
    print_success "服务停止完成"
}

# 上传文件
upload_files() {
    print_step "上传项目文件..."
    
    # 创建临时目录
    TEMP_DIR="/tmp/translation-api-$(date +%s)"
    
    # 排除不需要的文件
    rsync -avz --delete \
        --exclude='.git' \
        --exclude='.venv' \
        --exclude='__pycache__' \
        --exclude='*.pyc' \
        --exclude='.env' \
        --exclude='logs/' \
        --exclude='*.log' \
        ./ $DEPLOY_USER@$DEPLOY_HOST:$TEMP_DIR/
    
    ssh $DEPLOY_USER@$DEPLOY_HOST << EOF
        # 创建项目目录
        mkdir -p $PROJECT_PATH
        
        # 备份.env文件
        if [ -f "$PROJECT_PATH/.env" ]; then
            cp "$PROJECT_PATH/.env" "/tmp/.env.backup"
        fi
        
        # 复制新文件
        cp -r $TEMP_DIR/* $PROJECT_PATH/
        
        # 恢复.env文件
        if [ -f "/tmp/.env.backup" ]; then
            cp "/tmp/.env.backup" "$PROJECT_PATH/.env"
            rm "/tmp/.env.backup"
        fi
        
        # 清理临时目录
        rm -rf $TEMP_DIR
        
        # 设置权限
        chown -R www-data:www-data $PROJECT_PATH
        chmod -R 755 $PROJECT_PATH
EOF
    
    print_success "文件上传完成"
}

# 安装依赖
install_dependencies() {
    print_step "安装Python依赖..."
    
    ssh $DEPLOY_USER@$DEPLOY_HOST << EOF
        cd $PROJECT_PATH
        
        # 创建虚拟环境
        if [ ! -d "venv" ]; then
            python3 -m venv venv
        fi
        
        # 激活虚拟环境并安装依赖
        source venv/bin/activate
        pip install --upgrade pip
        pip install -r requirements.txt
        
        echo "依赖安装完成"
EOF
    
    print_success "依赖安装完成"
}

# 配置服务
configure_service() {
    print_step "配置系统服务..."
    
    ssh $DEPLOY_USER@$DEPLOY_HOST << 'EOF'
        # 创建systemd服务文件
        cat > /etc/systemd/system/translation-api.service << 'SERVICEEOF'
[Unit]
Description=Translation API Service
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/home/translation-api
Environment=PATH=/home/translation-api/venv/bin
ExecStart=/home/translation-api/venv/bin/python main.py
Restart=always
RestartSec=3
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SERVICEEOF

        # 重新加载systemd
        systemctl daemon-reload
        systemctl enable translation-api
EOF
    
    print_success "服务配置完成"
}

# 配置Nginx
configure_nginx() {
    print_step "配置Nginx..."
    
    ssh $DEPLOY_USER@$DEPLOY_HOST << 'EOF'
        # 创建Nginx配置
        cat > /etc/nginx/sites-available/translation-api << 'NGINXEOF'
server {
    listen 80;
    server_name _;
    
    client_max_body_size 10M;
    
    # 日志配置
    access_log /var/log/nginx/translation-api.access.log;
    error_log /var/log/nginx/translation-api.error.log;
    
    # API代理
    location / {
        proxy_pass http://127.0.0.1:9000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # 缓冲设置
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
    }
    
    # 静态文件
    location /static/ {
        alias /home/translation-api/static/;
        expires 1d;
        add_header Cache-Control "public";
    }
    
    # 健康检查
    location /health {
        proxy_pass http://127.0.0.1:9000/health;
        access_log off;
    }
    
    # 安全头
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
}
NGINXEOF

        # 启用站点
        ln -sf /etc/nginx/sites-available/translation-api /etc/nginx/sites-enabled/
        
        # 删除默认站点（如果存在）
        rm -f /etc/nginx/sites-enabled/default
        
        # 测试Nginx配置
        if nginx -t; then
            echo "Nginx配置测试通过"
            systemctl reload nginx
        else
            echo "Nginx配置测试失败"
            exit 1
        fi
EOF
    
    print_success "Nginx配置完成"
}

# 启动服务
start_service() {
    print_step "启动服务..."
    
    ssh $DEPLOY_USER@$DEPLOY_HOST << EOF
        cd $PROJECT_PATH
        
        # 启动服务
        systemctl start $SERVICE_NAME
        
        # 等待服务启动
        sleep 5
        
        # 检查服务状态
        if systemctl is-active --quiet $SERVICE_NAME; then
            echo "服务启动成功"
        else
            echo "服务启动失败，查看日志:"
            systemctl status $SERVICE_NAME --no-pager
            journalctl -u $SERVICE_NAME --no-pager -n 20
            exit 1
        fi
EOF
    
    print_success "服务启动完成"
}

# 验证部署
verify_deployment() {
    print_step "验证部署..."
    
    # 等待服务完全启动
    sleep 10
    
    # 健康检查
    if curl -f -s http://$DEPLOY_HOST/health > /dev/null; then
        print_success "健康检查通过"
    else
        print_error "健康检查失败"
        return 1
    fi
    
    # API测试
    if curl -f -s http://$DEPLOY_HOST/api/languages > /dev/null; then
        print_success "API测试通过"
    else
        print_warning "API测试失败，但服务可能正在启动中"
    fi
    
    print_success "部署验证完成"
}

# 显示部署信息
show_deployment_info() {
    print_header "部署完成"
    
    echo -e "${GREEN}🎉 翻译API部署成功！${NC}"
    echo ""
    echo -e "${BLUE}📋 服务信息:${NC}"
    echo "• 服务器: $DEPLOY_HOST"
    echo "• 端口: $DEPLOY_PORT"
    echo "• 项目路径: $PROJECT_PATH"
    echo ""
    echo -e "${BLUE}🔗 访问地址:${NC}"
    echo "• 主页: http://$DEPLOY_HOST"
    echo "• API文档: http://$DEPLOY_HOST/docs"
    echo "• 健康检查: http://$DEPLOY_HOST/health"
    echo ""
    echo -e "${BLUE}🛠️ 管理命令:${NC}"
    echo "• 查看状态: systemctl status $SERVICE_NAME"
    echo "• 查看日志: journalctl -u $SERVICE_NAME -f"
    echo "• 重启服务: systemctl restart $SERVICE_NAME"
}

# 主函数
main() {
    print_header "翻译API部署脚本"
    
    # 检查参数
    if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
        echo "用法: $0 [选项]"
        echo ""
        echo "选项:"
        echo "  --help, -h     显示帮助信息"
        echo "  --check        仅检查连接"
        echo "  --backup       仅创建备份"
        echo ""
        exit 0
    fi
    
    if [ "$1" = "--check" ]; then
        check_dependencies
        print_success "连接检查完成"
        exit 0
    fi
    
    if [ "$1" = "--backup" ]; then
        check_dependencies
        create_backup
        exit 0
    fi
    
    # 执行完整部署流程
    check_dependencies
    create_backup
    stop_service
    upload_files
    install_dependencies
    configure_service
    configure_nginx
    start_service
    verify_deployment
    show_deployment_info
}

# 错误处理
trap 'print_error "部署过程中发生错误，请检查日志"; exit 1' ERR

# 执行主函数
main "$@"
