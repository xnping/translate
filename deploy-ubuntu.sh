#!/bin/bash

# Ubuntu 翻译服务一键部署脚本
# 项目将部署到 /home/translation-service
# 使用方法: sudo ./deploy-ubuntu.sh

set -e

# 配置变量
PROJECT_NAME="translation-service"
PROJECT_DIR="/home/$PROJECT_NAME"
SERVICE_USER="translation"
CURRENT_DIR=$(pwd)
REDIS_PASSWORD=""
BAIDU_APP_ID=""
BAIDU_SECRET_KEY=""

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
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
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "此脚本需要root权限运行"
        log_info "请使用: sudo $0"
        exit 1
    fi
}

# 获取用户输入
get_user_input() {
    log_step "配置部署参数"

    echo -n "请输入Redis密码 (留空表示不设置密码): "
    read REDIS_PASSWORD
    if [ -z "$REDIS_PASSWORD" ]; then
        log_info "Redis将不设置密码"
    else
        log_info "Redis密码已设置"
    fi

    echo -n "请输入百度翻译APP ID: "
    read BAIDU_APP_ID
    while [ -z "$BAIDU_APP_ID" ]; do
        log_warn "百度APP ID不能为空"
        echo -n "请输入百度翻译APP ID: "
        read BAIDU_APP_ID
    done

    echo -n "请输入百度翻译SECRET KEY: "
    read BAIDU_SECRET_KEY
    while [ -z "$BAIDU_SECRET_KEY" ]; do
        log_warn "百度SECRET KEY不能为空"
        echo -n "请输入百度翻译SECRET KEY: "
        read BAIDU_SECRET_KEY
    done

    echo -n "请输入域名 (留空使用IP访问): "
    read DOMAIN_NAME

    log_info "配置完成！"
}

# 更新系统
update_system() {
    log_step "更新系统包"
    apt update && apt upgrade -y
    apt install -y wget curl git vim net-tools software-properties-common build-essential
}

# 安装Python 3.10
install_python() {
    log_step "安装Python 3.10"

    # 检查是否已安装Python 3.10
    if command -v python3.10 &> /dev/null; then
        log_info "Python 3.10 已安装"
        return
    fi

    # 添加deadsnakes PPA
    add-apt-repository ppa:deadsnakes/ppa -y
    apt update
    apt install -y python3.10 python3.10-venv python3.10-dev

    # 安装pip
    curl https://bootstrap.pypa.io/get-pip.py | python3.10

    log_info "Python 3.10 安装完成"
}

# 安装Redis
install_redis() {
    log_step "安装和配置Redis"

    apt install -y redis-server

    # 配置Redis
    cp /etc/redis/redis.conf /etc/redis/redis.conf.backup

    # 设置密码 (如果提供了密码)
    if [ -n "$REDIS_PASSWORD" ]; then
        sed -i "s/# requirepass foobared/requirepass $REDIS_PASSWORD/" /etc/redis/redis.conf
        log_info "Redis密码已设置"
    else
        # 确保密码行被注释掉
        sed -i "s/^requirepass/#requirepass/" /etc/redis/redis.conf
        log_info "Redis未设置密码"
    fi

    # 确保绑定到本地
    sed -i "s/bind 127.0.0.1 ::1/bind 127.0.0.1/" /etc/redis/redis.conf

    # 设置为systemd管理
    sed -i "s/supervised no/supervised systemd/" /etc/redis/redis.conf

    systemctl restart redis-server
    systemctl enable redis-server

    log_info "Redis 安装配置完成"
}

# 安装Nginx
install_nginx() {
    log_step "安装Nginx"

    apt install -y nginx
    systemctl start nginx
    systemctl enable nginx

    log_info "Nginx 安装完成"
}

# 创建用户和目录
setup_user_and_dirs() {
    log_step "创建用户和目录"

    # 创建用户
    if ! id "$SERVICE_USER" &>/dev/null; then
        useradd -r -s /bin/false -d $PROJECT_DIR $SERVICE_USER
        log_info "用户 $SERVICE_USER 创建成功"
    else
        log_info "用户 $SERVICE_USER 已存在"
    fi

    # 创建日志目录
    mkdir -p /var/log/$PROJECT_NAME

    # 检查当前目录是否就是项目目录
    if [ "$CURRENT_DIR" = "$PROJECT_DIR" ]; then
        log_info "当前已在项目目录中，跳过文件复制"
    else
        # 创建项目目录并复制文件
        mkdir -p $PROJECT_DIR
        cp -r $CURRENT_DIR/* $PROJECT_DIR/
        log_info "项目文件已复制到 $PROJECT_DIR"
    fi

    # 设置权限
    chown -R $SERVICE_USER:$SERVICE_USER $PROJECT_DIR
    chown -R $SERVICE_USER:$SERVICE_USER /var/log/$PROJECT_NAME
    chmod -R 755 $PROJECT_DIR

    log_info "用户和目录设置完成"
}

# 安装Python依赖
install_python_deps() {
    log_step "创建虚拟环境并安装Python依赖"

    cd $PROJECT_DIR

    # 创建虚拟环境
    sudo -u $SERVICE_USER python3.10 -m venv venv

    # 安装依赖
    sudo -u $SERVICE_USER $PROJECT_DIR/venv/bin/pip install --upgrade pip

    # 安装兼容的包版本
    sudo -u $SERVICE_USER $PROJECT_DIR/venv/bin/pip install fastapi==0.104.1
    sudo -u $SERVICE_USER $PROJECT_DIR/venv/bin/pip install "uvicorn[standard]==0.24.0"
    sudo -u $SERVICE_USER $PROJECT_DIR/venv/bin/pip install pydantic==2.5.0
    sudo -u $SERVICE_USER $PROJECT_DIR/venv/bin/pip install python-dotenv==1.0.0
    sudo -u $SERVICE_USER $PROJECT_DIR/venv/bin/pip install aiohttp==3.9.1
    sudo -u $SERVICE_USER $PROJECT_DIR/venv/bin/pip install redis==5.0.1
    sudo -u $SERVICE_USER $PROJECT_DIR/venv/bin/pip install python-multipart==0.0.6
    sudo -u $SERVICE_USER $PROJECT_DIR/venv/bin/pip install flask-cors==4.0.0
    sudo -u $SERVICE_USER $PROJECT_DIR/venv/bin/pip install gunicorn==21.2.0

    log_info "Python依赖安装完成"
}

# 创建环境配置文件
create_env_file() {
    log_step "创建环境配置文件"

    cat > $PROJECT_DIR/.env << EOF
# Redis配置
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=${REDIS_PASSWORD}
REDIS_TTL=86400
REDIS_SOCKET_TIMEOUT=1.0
REDIS_MAX_CONNECTIONS=50
REDIS_USE_COMPRESSION=true
REDIS_COMPRESSION_MIN_SIZE=1024
REDIS_COMPRESSION_LEVEL=6

# 百度翻译API配置
BAIDU_APP_ID=$BAIDU_APP_ID
BAIDU_SECRET_KEY=$BAIDU_SECRET_KEY
BAIDU_API_URL=https://api.fanyi.baidu.com/api/trans/vip/translate
BAIDU_API_TIMEOUT=2.0

# 批处理配置
MAX_CONCURRENT_REQUESTS=10
DEFAULT_BATCH_SIZE=20

# 应用配置
DEBUG=false
LOG_LEVEL=INFO
EOF

    chown $SERVICE_USER:$SERVICE_USER $PROJECT_DIR/.env
    chmod 600 $PROJECT_DIR/.env

    log_info "环境配置文件创建完成"
}

# 创建Gunicorn配置
create_gunicorn_config() {
    log_step "创建Gunicorn配置文件"

    cat > $PROJECT_DIR/gunicorn.conf.py << 'EOF'
import multiprocessing

# 服务器配置
bind = "127.0.0.1:9000"
workers = min(multiprocessing.cpu_count() * 2 + 1, 8)
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100

# 超时配置
timeout = 30
keepalive = 2
graceful_timeout = 30

# 日志配置
accesslog = "/var/log/translation-service/access.log"
errorlog = "/var/log/translation-service/error.log"
loglevel = "info"

# 进程配置
preload_app = True
daemon = False
user = "translation"
group = "translation"

# 性能配置
worker_tmp_dir = "/dev/shm"
EOF

    chown $SERVICE_USER:$SERVICE_USER $PROJECT_DIR/gunicorn.conf.py

    log_info "Gunicorn配置文件创建完成"
}

# 创建systemd服务
create_systemd_service() {
    log_step "创建systemd服务"

    cat > /etc/systemd/system/$PROJECT_NAME.service << EOF
[Unit]
Description=Translation Service API
After=network.target redis-server.service
Wants=redis-server.service

[Service]
Type=exec
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$PROJECT_DIR/venv/bin
Environment=PYTHONPATH=$PROJECT_DIR
ExecStart=$PROJECT_DIR/venv/bin/gunicorn main:app -c gunicorn.conf.py
ExecReload=/bin/kill -s HUP \$MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable $PROJECT_NAME

    log_info "systemd服务创建完成"
}

# 配置Nginx
configure_nginx() {
    log_step "配置Nginx"

    # 备份默认配置
    cp /etc/nginx/sites-available/default /etc/nginx/sites-available/default.backup

    # 创建站点配置
    cat > /etc/nginx/sites-available/$PROJECT_NAME << EOF
upstream translation_backend {
    server 127.0.0.1:9000;
    keepalive 32;
}

server {
    listen 80;
    listen [::]:80;
    server_name ${DOMAIN_NAME:-_};

    client_max_body_size 10M;

    access_log /var/log/nginx/translation-access.log;
    error_log /var/log/nginx/translation-error.log;

    # 安全头
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";

    # API代理
    location /api/ {
        proxy_pass http://translation_backend;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;

        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }

    # 健康检查
    location /health {
        proxy_pass http://translation_backend;
        access_log off;
    }

    # 静态文件
    location /static/ {
        alias $PROJECT_DIR/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # 主页和其他路径
    location / {
        proxy_pass http://translation_backend;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

    # 启用站点
    ln -sf /etc/nginx/sites-available/$PROJECT_NAME /etc/nginx/sites-enabled/
    rm -f /etc/nginx/sites-enabled/default

    # 测试配置
    nginx -t
    systemctl reload nginx

    log_info "Nginx配置完成"
}

# 配置防火墙
configure_firewall() {
    log_step "配置防火墙"

    ufw --force enable
    ufw allow ssh
    ufw allow 'Nginx Full'
    ufw allow 80/tcp
    ufw allow 443/tcp

    log_info "防火墙配置完成"
}

# 启动服务
start_services() {
    log_step "启动服务"

    systemctl start $PROJECT_NAME

    # 等待服务启动
    sleep 5

    if systemctl is-active --quiet $PROJECT_NAME; then
        log_info "翻译服务启动成功"
    else
        log_error "翻译服务启动失败"
        journalctl -u $PROJECT_NAME --no-pager -l
        exit 1
    fi
}

# 验证部署
verify_deployment() {
    log_step "验证部署"

    # 检查端口
    if ss -tlnp | grep -q :9000; then
        log_info "✓ 端口9000正在监听"
    else
        log_error "✗ 端口9000未监听"
        return 1
    fi

    # 测试API
    sleep 2
    if curl -s http://localhost:9000/health > /dev/null; then
        log_info "✓ API健康检查通过"
    else
        log_error "✗ API健康检查失败"
        return 1
    fi

    # 测试Nginx代理
    if curl -s http://localhost/health > /dev/null; then
        log_info "✓ Nginx代理正常"
    else
        log_error "✗ Nginx代理失败"
        return 1
    fi

    log_info "部署验证完成"
}

# 创建管理脚本
create_management_script() {
    log_step "创建管理脚本"

    cat > $PROJECT_DIR/manage.sh << 'EOF'
#!/bin/bash

SERVICE_NAME="translation-service"

case "$1" in
    start)
        sudo systemctl start $SERVICE_NAME
        echo "服务已启动"
        ;;
    stop)
        sudo systemctl stop $SERVICE_NAME
        echo "服务已停止"
        ;;
    restart)
        sudo systemctl restart $SERVICE_NAME
        echo "服务已重启"
        ;;
    status)
        sudo systemctl status $SERVICE_NAME
        ;;
    logs)
        sudo journalctl -u $SERVICE_NAME -f
        ;;
    test)
        echo "测试API健康检查..."
        curl http://localhost:9000/health
        echo ""
        echo "测试翻译功能..."
        curl -X POST "http://localhost:9000/api/translate" \
          -H "Content-Type: application/json" \
          -d '{"text":"Hello World","from_lang":"en","to_lang":"zh"}'
        echo ""
        echo "测试Redis连接..."
        if [ -n "$REDIS_PASSWORD" ]; then
            redis-cli -a "$REDIS_PASSWORD" ping
        else
            redis-cli ping
        fi
        echo ""
        ;;
    *)
        echo "使用方法: $0 {start|stop|restart|status|logs|test}"
        exit 1
        ;;
esac
EOF

    chmod +x $PROJECT_DIR/manage.sh
    chown $SERVICE_USER:$SERVICE_USER $PROJECT_DIR/manage.sh

    log_info "管理脚本创建完成: $PROJECT_DIR/manage.sh"
}

# 显示部署信息
show_deployment_info() {
    log_step "部署完成！"

    echo ""
    echo "=========================================="
    echo "           部署信息"
    echo "=========================================="
    echo "项目目录: $PROJECT_DIR"
    echo "服务用户: $SERVICE_USER"
    if [ -n "$REDIS_PASSWORD" ]; then
        echo "Redis密码: $REDIS_PASSWORD"
    else
        echo "Redis密码: 未设置 (无密码)"
    fi
    echo "服务端口: 9000"
    echo ""
    echo "访问地址:"
    if [ -n "$DOMAIN_NAME" ]; then
        echo "  - http://$DOMAIN_NAME"
        echo "  - http://$DOMAIN_NAME/health"
    else
        echo "  - http://$(hostname -I | awk '{print $1}')"
        echo "  - http://$(hostname -I | awk '{print $1}')/health"
    fi
    echo ""
    echo "管理命令:"
    echo "  启动服务: sudo systemctl start $PROJECT_NAME"
    echo "  停止服务: sudo systemctl stop $PROJECT_NAME"
    echo "  重启服务: sudo systemctl restart $PROJECT_NAME"
    echo "  查看状态: sudo systemctl status $PROJECT_NAME"
    echo "  查看日志: sudo journalctl -u $PROJECT_NAME -f"
    echo ""
    echo "快捷管理: $PROJECT_DIR/manage.sh {start|stop|restart|status|logs|test}"
    echo ""
    echo "配置文件: $PROJECT_DIR/.env"
    echo "=========================================="
}

# 主函数
main() {
    log_info "开始Ubuntu翻译服务一键部署"

    # 检查当前目录
    if [ "$(basename $CURRENT_DIR)" = "$PROJECT_NAME" ] && [ "$CURRENT_DIR" = "$PROJECT_DIR" ]; then
        log_info "检测到当前在项目目录中运行脚本，将跳过文件复制步骤"
    fi

    check_root
    get_user_input
    update_system
    install_python
    install_redis
    install_nginx
    setup_user_and_dirs
    install_python_deps
    create_env_file
    create_gunicorn_config
    create_systemd_service
    configure_nginx
    configure_firewall
    start_services
    verify_deployment
    create_management_script
    show_deployment_info

    log_info "部署完成！"
}

# 执行主函数
main "$@"
