#!/bin/bash

# =============================================================================
# 彻底修复403 Forbidden问题
# =============================================================================

set -e

PROJECT_NAME="translation-api"
PROJECT_DIR="$(pwd)"

echo "=== 彻底修复403 Forbidden问题 ==="
echo "项目目录: $PROJECT_DIR"
echo

# 1. 检查并修复目录权限
echo "1. 修复目录权限..."
chmod 755 "$PROJECT_DIR"
if [ -d "static" ]; then
    chmod 755 static/
    chmod -R 644 static/*
    # 确保子目录有执行权限
    find static/ -type d -exec chmod 755 {} \;
    echo "✅ 静态文件权限已修复"
else
    echo "❌ static目录不存在"
    exit 1
fi

# 2. 检查文件是否存在
echo "2. 检查关键文件..."
if [ ! -f "static/apidemo.md" ]; then
    echo "❌ apidemo.md 文件不存在，创建示例文件"
    echo "# API文档" > static/apidemo.md
    echo "这是API文档内容" >> static/apidemo.md
fi

if [ ! -f "static/index.html" ]; then
    echo "❌ index.html 文件不存在"
    exit 1
fi

# 3. 修复Nginx用户权限问题
echo "3. 修复Nginx用户权限..."

# 检查nginx用户
NGINX_USER=$(ps aux | grep "nginx: worker" | grep -v grep | awk '{print $1}' | head -1)
if [ -z "$NGINX_USER" ]; then
    NGINX_USER="www-data"  # Ubuntu默认
fi
echo "Nginx运行用户: $NGINX_USER"

# 确保nginx用户可以访问项目目录
# 方法1: 添加nginx用户到当前用户组
CURRENT_USER=$(stat -c '%U' "$PROJECT_DIR")
CURRENT_GROUP=$(stat -c '%G' "$PROJECT_DIR")
echo "项目目录所有者: $CURRENT_USER:$CURRENT_GROUP"

# 给其他用户读取权限
chmod o+rx "$PROJECT_DIR"
chmod -R o+r static/

# 4. 重新配置Nginx
echo "4. 重新配置Nginx..."
cat > /etc/nginx/sites-available/$PROJECT_NAME << EOF
server {
    listen 80;
    server_name _;
    
    # 主应用代理
    location / {
        proxy_pass http://127.0.0.1:9000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # 静态文件配置
    location /static/ {
        alias $PROJECT_DIR/static/;
        
        # 基本配置
        autoindex off;
        expires 1d;
        add_header Cache-Control "public";
        
        # 安全配置
        add_header X-Content-Type-Options nosniff;
        add_header X-Frame-Options DENY;
        
        # 文件类型配置
        location ~* \.(md|txt)$ {
            add_header Content-Type "text/plain; charset=utf-8";
        }
        
        location ~* \.(html|htm)$ {
            add_header Content-Type "text/html; charset=utf-8";
        }
        
        location ~* \.(js)$ {
            add_header Content-Type "application/javascript; charset=utf-8";
        }
        
        location ~* \.(css)$ {
            add_header Content-Type "text/css; charset=utf-8";
        }
        
        # 默认处理
        try_files \$uri \$uri/ =404;
    }
    
    # 健康检查
    location /health {
        proxy_pass http://127.0.0.1:9000/health;
        access_log off;
    }
    
    # 错误页面
    error_page 404 /404.html;
    error_page 500 502 503 504 /50x.html;
    
    # 日志配置
    access_log /var/log/nginx/translation-api-access.log;
    error_log /var/log/nginx/translation-api-error.log;
    
    client_max_body_size 10M;
}
EOF

# 5. 测试Nginx配置
echo "5. 测试Nginx配置..."
if nginx -t; then
    echo "✅ Nginx配置正确"
else
    echo "❌ Nginx配置错误"
    exit 1
fi

# 6. 重启Nginx
echo "6. 重启Nginx..."
systemctl reload nginx
sleep 2

# 7. 测试访问
echo "7. 测试文件访问..."

# 测试本地文件读取
echo "本地文件测试:"
if [ -f "static/apidemo.md" ]; then
    echo "✅ apidemo.md 文件存在"
    echo "文件大小: $(wc -c < static/apidemo.md) bytes"
else
    echo "❌ apidemo.md 文件不存在"
fi

# 测试HTTP访问
echo "HTTP访问测试:"
sleep 3

# 测试apidemo.md
echo "测试 /static/apidemo.md ..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/static/apidemo.md)
echo "HTTP状态码: $HTTP_CODE"

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ apidemo.md HTTP访问成功"
else
    echo "❌ apidemo.md HTTP访问失败"
    echo "检查Nginx错误日志:"
    tail -5 /var/log/nginx/translation-api-error.log 2>/dev/null || echo "无错误日志"
fi

# 测试index.html
echo "测试 /static/index.html ..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/static/index.html)
echo "HTTP状态码: $HTTP_CODE"

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ index.html HTTP访问成功"
else
    echo "❌ index.html HTTP访问失败"
fi

# 8. 显示最终状态
echo
echo "=== 最终状态 ==="
echo "项目目录权限: $(stat -c '%a %U:%G' "$PROJECT_DIR")"
echo "static目录权限: $(stat -c '%a %U:%G' static/)"
echo "apidemo.md权限: $(stat -c '%a %U:%G' static/apidemo.md)"

echo
echo "=== 修复完成 ==="
echo "如果仍有问题，请运行: ./diagnose.sh"

# 获取服务器IP
SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || echo "your-server-ip")
echo "访问地址: http://$SERVER_IP"
