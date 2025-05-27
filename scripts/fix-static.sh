#!/bin/bash

# =============================================================================
# 修复静态文件访问问题
# =============================================================================

PROJECT_NAME="translation-api"
PROJECT_DIR="$(pwd)"

echo "修复静态文件访问问题..."

# 1. 设置静态文件权限
echo "设置静态文件权限..."
chmod -R 755 static/
chmod 644 static/*.md
chmod 644 static/*.html
chmod 644 static/js/*.js 2>/dev/null || true

# 2. 重新配置Nginx
echo "重新配置Nginx..."
cat > /etc/nginx/sites-available/$PROJECT_NAME << EOF
server {
    listen 80;
    server_name _;
    
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
    
    location /static/ {
        alias $PROJECT_DIR/static/;
        autoindex off;
        
        # 允许访问所有文件类型
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot|md|html|txt)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
            add_header Access-Control-Allow-Origin "*";
        }
        
        # 确保可以访问markdown文件
        location ~* \.md$ {
            add_header Content-Type "text/plain; charset=utf-8";
            add_header Access-Control-Allow-Origin "*";
        }
        
        # 默认处理
        try_files \$uri \$uri/ =404;
    }
    
    location /health {
        proxy_pass http://127.0.0.1:9000/health;
        access_log off;
    }
    
    client_max_body_size 10M;
}
EOF

# 3. 测试Nginx配置
echo "测试Nginx配置..."
if nginx -t; then
    echo "Nginx配置正确"
else
    echo "Nginx配置错误"
    exit 1
fi

# 4. 重启Nginx
echo "重启Nginx..."
systemctl reload nginx

# 5. 测试静态文件访问
echo "测试静态文件访问..."
sleep 2

# 测试apidemo.md文件
if curl -s http://localhost/static/apidemo.md | head -1 | grep -q "#"; then
    echo "✅ apidemo.md 访问正常"
else
    echo "❌ apidemo.md 访问失败"
fi

# 测试index.html文件
if curl -s http://localhost/static/index.html | grep -q "<!DOCTYPE html"; then
    echo "✅ index.html 访问正常"
else
    echo "❌ index.html 访问失败"
fi

# 6. 显示文件权限
echo "静态文件权限:"
ls -la static/

echo "修复完成！"
echo "请访问: http://your-server-ip"
