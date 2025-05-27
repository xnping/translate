#!/bin/bash

# =============================================================================
# 修复Redis连接问题
# =============================================================================

echo "=== 修复Redis连接问题 ==="

# 1. 检查Redis状态
echo "1. 检查Redis状态..."
if systemctl is-active --quiet redis-server; then
    echo "✅ Redis服务运行中"
else
    echo "❌ Redis服务未运行，启动中..."
    systemctl start redis-server
    systemctl enable redis-server
    sleep 2
fi

# 2. 测试Redis连接
echo "2. 测试Redis连接..."
if redis-cli ping | grep -q "PONG"; then
    echo "✅ Redis连接正常"
else
    echo "❌ Redis连接失败，重启Redis..."
    systemctl restart redis-server
    sleep 3
    if redis-cli ping | grep -q "PONG"; then
        echo "✅ Redis重启后连接正常"
    else
        echo "❌ Redis仍然无法连接"
        exit 1
    fi
fi

# 3. 检查Redis配置
echo "3. 检查Redis配置..."
echo "Redis配置信息:"
redis-cli info server | grep redis_version
redis-cli config get bind
redis-cli config get port

# 4. 检查.env文件中的Redis配置
echo "4. 检查.env文件中的Redis配置..."
if [ -f ".env" ]; then
    echo "当前Redis配置:"
    grep -E "REDIS_" .env || echo "未找到Redis配置"
else
    echo "❌ .env文件不存在"
    exit 1
fi

# 5. 确保.env中有正确的Redis配置
echo "5. 确保Redis配置正确..."
if ! grep -q "REDIS_HOST" .env; then
    echo "添加Redis配置到.env文件..."
    cat >> .env << EOF

# Redis配置
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
REDIS_MAX_CONNECTIONS=50
EOF
    echo "✅ Redis配置已添加"
fi

# 6. 重启应用服务
echo "6. 重启应用服务..."
systemctl restart translation-api
sleep 5

# 7. 检查应用状态
echo "7. 检查应用状态..."
if systemctl is-active --quiet translation-api; then
    echo "✅ 应用服务运行中"
else
    echo "❌ 应用服务启动失败"
    echo "查看错误日志:"
    journalctl -u translation-api -n 10 --no-pager
    exit 1
fi

# 8. 测试健康检查
echo "8. 测试健康检查..."
sleep 3
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:9000/health)
echo "健康检查HTTP状态码: $HTTP_CODE"

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ 健康检查通过"
    echo "测试响应内容:"
    curl -s http://localhost:9000/health | head -3
else
    echo "❌ 健康检查失败"
    echo "应用日志:"
    journalctl -u translation-api -n 20 --no-pager
fi

# 9. 测试翻译接口
echo "9. 测试翻译接口..."
TRANSLATE_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:9000/api/translate \
    -H "Content-Type: application/json" \
    -d '{"text":"测试","from_lang":"zh","to_lang":"en"}')

echo "翻译接口HTTP状态码: $TRANSLATE_CODE"

if [ "$TRANSLATE_CODE" = "200" ]; then
    echo "✅ 翻译接口正常"
else
    echo "❌ 翻译接口异常"
fi

echo
echo "=== 修复完成 ==="
echo "如果仍有问题，请查看详细日志: journalctl -u translation-api -f"

# 获取服务器IP
SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || echo "localhost")
echo "访问地址: http://$SERVER_IP"
