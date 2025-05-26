#!/bin/bash

# Redis连接测试脚本
# 使用方法: ./test-redis.sh [password]

REDIS_PASSWORD="$1"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

echo "=========================================="
echo "           Redis 连接测试"
echo "=========================================="

# 检查Redis服务状态
log_info "检查Redis服务状态..."
if systemctl is-active --quiet redis-server; then
    log_info "✓ Redis服务正在运行"
else
    log_error "✗ Redis服务未运行"
    echo "启动Redis服务: sudo systemctl start redis-server"
    exit 1
fi

# 检查Redis端口
log_info "检查Redis端口..."
if ss -tlnp | grep -q :6379; then
    log_info "✓ Redis端口6379正在监听"
else
    log_error "✗ Redis端口6379未监听"
    exit 1
fi

# 测试Redis连接
log_info "测试Redis连接..."
if [ -n "$REDIS_PASSWORD" ]; then
    log_info "使用密码连接Redis..."
    if redis-cli -a "$REDIS_PASSWORD" ping > /dev/null 2>&1; then
        log_info "✓ Redis密码连接成功"
        REDIS_RESPONSE=$(redis-cli -a "$REDIS_PASSWORD" ping 2>/dev/null)
        echo "响应: $REDIS_RESPONSE"
    else
        log_error "✗ Redis密码连接失败"
        echo "请检查密码是否正确"
        exit 1
    fi
else
    log_info "使用无密码连接Redis..."
    if redis-cli ping > /dev/null 2>&1; then
        log_info "✓ Redis无密码连接成功"
        REDIS_RESPONSE=$(redis-cli ping)
        echo "响应: $REDIS_RESPONSE"
    else
        log_error "✗ Redis无密码连接失败"
        echo "Redis可能设置了密码，请提供密码参数"
        exit 1
    fi
fi

# 测试基本操作
log_info "测试Redis基本操作..."
TEST_KEY="test:$(date +%s)"
TEST_VALUE="Hello Redis"

if [ -n "$REDIS_PASSWORD" ]; then
    redis-cli -a "$REDIS_PASSWORD" set "$TEST_KEY" "$TEST_VALUE" > /dev/null 2>&1
    RESULT=$(redis-cli -a "$REDIS_PASSWORD" get "$TEST_KEY" 2>/dev/null)
    redis-cli -a "$REDIS_PASSWORD" del "$TEST_KEY" > /dev/null 2>&1
else
    redis-cli set "$TEST_KEY" "$TEST_VALUE" > /dev/null 2>&1
    RESULT=$(redis-cli get "$TEST_KEY")
    redis-cli del "$TEST_KEY" > /dev/null 2>&1
fi

if [ "$RESULT" = "$TEST_VALUE" ]; then
    log_info "✓ Redis读写操作正常"
else
    log_error "✗ Redis读写操作失败"
    exit 1
fi

# 显示Redis信息
log_info "Redis服务信息:"
if [ -n "$REDIS_PASSWORD" ]; then
    redis-cli -a "$REDIS_PASSWORD" info server 2>/dev/null | grep -E "redis_version|os|arch_bits|process_id|tcp_port"
else
    redis-cli info server | grep -E "redis_version|os|arch_bits|process_id|tcp_port"
fi

echo ""
log_info "✓ Redis连接测试完成，一切正常！"
echo "=========================================="
