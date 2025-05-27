#!/bin/bash

# =============================================================================
# 翻译API项目部署脚本
# =============================================================================

set -e

# 项目配置
PROJECT_NAME="translation-api"
PROJECT_DIR="$(pwd)"
PORT=9000

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# 安装系统依赖
install_dependencies() {
    print_step "安装系统依赖..."

    apt update
    apt install -y \
        python3 \
        python3-pip \
        python3-venv \
        python3-full \
        redis-server \
        nginx \
        curl \
        net-tools

    print_success "系统依赖安装完成"
}

# 设置Python环境
setup_python() {
    print_step "设置Python环境..."

    cd "$PROJECT_DIR"

    # 删除旧虚拟环境
    rm -rf venv

    # 创建虚拟环境
    python3 -m venv venv
    source venv/bin/activate

    # 安装依赖
    python -m pip install --upgrade pip
    pip install -r requirements.txt

    print_success "Python环境设置完成"
}

# 配置Redis
setup_redis() {
    print_step "配置Redis..."

    systemctl start redis-server
    systemctl enable redis-server

    print_success "Redis配置完成"
}

# 配置Nginx
setup_nginx() {
    print_step "配置Nginx..."

    # 创建Nginx配置
    cat > /etc/nginx/sites-available/$PROJECT_NAME << EOF
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:$PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;

        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    location /static/ {
        alias $PROJECT_DIR/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";

        # 允许访问所有文件类型
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot|md|html|txt)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }

        # 确保可以访问markdown文件
        location ~* \.md$ {
            add_header Content-Type "text/plain; charset=utf-8";
        }
    }

    location /health {
        proxy_pass http://127.0.0.1:$PORT/health;
        access_log off;
    }

    client_max_body_size 10M;
}
EOF

    # 启用站点
    ln -sf /etc/nginx/sites-available/$PROJECT_NAME /etc/nginx/sites-enabled/
    rm -f /etc/nginx/sites-enabled/default

    # 启动Nginx
    systemctl start nginx
    systemctl enable nginx
    systemctl reload nginx

    print_success "Nginx配置完成"
}

# 创建systemd服务
create_service() {
    print_step "创建systemd服务..."

    cat > /etc/systemd/system/$PROJECT_NAME.service << EOF
[Unit]
Description=Translation API Service
After=network.target redis.service

[Service]
Type=simple
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$PROJECT_DIR/venv/bin
ExecStart=$PROJECT_DIR/venv/bin/python main.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable $PROJECT_NAME

    print_success "systemd服务创建完成"
}

# 创建管理脚本
create_scripts() {
    print_step "创建管理脚本..."

    cd "$PROJECT_DIR"

    # 状态脚本
    cat > status.sh << 'EOF'
#!/bin/bash
echo "=== 服务状态 ==="
systemctl status translation-api --no-pager -l
echo
echo "=== 端口监听 ==="
netstat -tlnp | grep :9000 || echo "端口9000未监听"
echo
echo "=== Redis状态 ==="
redis-cli ping || echo "Redis连接失败"
EOF

    # 重启脚本
    cat > restart.sh << 'EOF'
#!/bin/bash
systemctl restart translation-api
systemctl restart nginx
echo "服务已重启"
EOF

    # 日志脚本
    cat > logs.sh << 'EOF'
#!/bin/bash
journalctl -u translation-api -f --no-pager
EOF

    chmod +x status.sh restart.sh logs.sh

    print_success "管理脚本创建完成"
}

# 启动服务
start_service() {
    print_step "启动服务..."

    systemctl start $PROJECT_NAME
    sleep 3

    if systemctl is-active --quiet $PROJECT_NAME; then
        print_success "服务启动成功"
    else
        echo "服务启动失败，查看日志: journalctl -u $PROJECT_NAME -f"
        exit 1
    fi
}

# 测试部署
test_deployment() {
    print_step "测试部署..."

    if curl -s http://localhost:$PORT/health > /dev/null; then
        print_success "API测试通过"
    else
        echo "API测试失败"
    fi

    SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || echo "localhost")
    echo "访问地址: http://$SERVER_IP"
}

# 主函数
main() {
    echo "开始部署翻译API项目..."

    install_dependencies
    setup_python
    setup_redis
    setup_nginx
    create_service
    create_scripts
    start_service
    test_deployment

    echo
    echo "部署完成！"
    echo "管理命令:"
    echo "  查看状态: ./status.sh"
    echo "  重启服务: ./restart.sh"
    echo "  查看日志: ./logs.sh"
}

main "$@"
