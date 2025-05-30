#!/bin/bash

# Ubuntu MySQL和Redis完整安装脚本
# 作者: AI Assistant
# 用途: 卸载旧版本，安装MySQL和Redis，配置外部连接
# 使用方法: sudo bash install_mysql_redis.sh

set -e  # 遇到错误立即退出

# 颜色定义
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

# 检查是否为root用户
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "此脚本需要root权限运行"
        log_info "请使用: sudo bash $0"
        exit 1
    fi
    log_info "✅ Root权限检查通过"
}

# 更新系统
update_system() {
    log_step "🔄 更新系统包列表..."
    apt update -y
    apt upgrade -y
    log_info "✅ 系统更新完成"
}

# 卸载MySQL
uninstall_mysql() {
    log_step "🗑️  开始卸载MySQL..."
    
    # 停止MySQL服务
    systemctl stop mysql 2>/dev/null || true
    systemctl stop mysqld 2>/dev/null || true
    
    # 卸载MySQL包
    apt remove --purge mysql-server mysql-client mysql-common mysql-server-core-* mysql-client-core-* -y 2>/dev/null || true
    apt remove --purge mariadb-server mariadb-client mariadb-common -y 2>/dev/null || true
    
    # 删除MySQL配置文件和数据
    rm -rf /etc/mysql
    rm -rf /var/lib/mysql
    rm -rf /var/log/mysql
    rm -rf /usr/lib/mysql
    rm -rf /usr/share/mysql
    
    # 删除MySQL用户
    userdel mysql 2>/dev/null || true
    groupdel mysql 2>/dev/null || true
    
    # 清理残留包
    apt autoremove -y
    apt autoclean
    
    log_info "✅ MySQL卸载完成"
}

# 卸载Redis
uninstall_redis() {
    log_step "🗑️  开始卸载Redis..."
    
    # 停止Redis服务
    systemctl stop redis-server 2>/dev/null || true
    systemctl stop redis 2>/dev/null || true
    
    # 卸载Redis包
    apt remove --purge redis-server redis-tools redis-sentinel -y 2>/dev/null || true
    
    # 删除Redis配置文件和数据
    rm -rf /etc/redis
    rm -rf /var/lib/redis
    rm -rf /var/log/redis
    rm -rf /usr/share/redis
    
    # 删除Redis用户
    userdel redis 2>/dev/null || true
    groupdel redis 2>/dev/null || true
    
    log_info "✅ Redis卸载完成"
}

# 安装MySQL
install_mysql() {
    log_step "📦 开始安装MySQL..."
    
    # 预配置MySQL密码
    echo "mysql-server mysql-server/root_password password 123456" | debconf-set-selections
    echo "mysql-server mysql-server/root_password_again password 123456" | debconf-set-selections
    
    # 安装MySQL
    apt install mysql-server -y
    
    # 启动MySQL服务
    systemctl start mysql
    systemctl enable mysql
    
    log_info "✅ MySQL安装完成"
}

# 配置MySQL
configure_mysql() {
    log_step "⚙️  配置MySQL..."
    
    # 配置MySQL允许外部连接
    cat > /etc/mysql/mysql.conf.d/mysqld.cnf << 'EOF'
[mysqld]
pid-file        = /var/run/mysqld/mysqld.pid
socket          = /var/run/mysqld/mysqld.sock
datadir         = /var/lib/mysql
log-error       = /var/log/mysql/error.log
bind-address    = 0.0.0.0
mysqlx-bind-address = 0.0.0.0
port            = 3306

# 字符集配置
character-set-server = utf8mb4
collation-server = utf8mb4_unicode_ci

# 性能配置
max_connections = 200
innodb_buffer_pool_size = 256M
query_cache_size = 64M
query_cache_type = 1

# 安全配置
sql_mode = STRICT_TRANS_TABLES,NO_ZERO_DATE,NO_ZERO_IN_DATE,ERROR_FOR_DIVISION_BY_ZERO
EOF

    # 重启MySQL服务
    systemctl restart mysql
    
    # 配置root用户远程访问
    mysql -u root -p123456 << 'EOF'
USE mysql;
UPDATE user SET host='%' WHERE user='root';
ALTER USER 'root'@'%' IDENTIFIED WITH mysql_native_password BY '123456';
FLUSH PRIVILEGES;
EOF

    log_info "✅ MySQL配置完成"
    log_info "   - 绑定地址: 0.0.0.0:3306"
    log_info "   - Root密码: 123456"
    log_info "   - 允许外部连接: 是"
}

# 安装Redis
install_redis() {
    log_step "📦 开始安装Redis..."
    
    # 安装Redis
    apt install redis-server -y
    
    log_info "✅ Redis安装完成"
}

# 配置Redis
configure_redis() {
    log_step "⚙️  配置Redis..."
    
    # 备份原配置文件
    cp /etc/redis/redis.conf /etc/redis/redis.conf.backup
    
    # 配置Redis
    cat > /etc/redis/redis.conf << 'EOF'
# Redis配置文件 - 允许外部连接
bind 0.0.0.0
port 6379
timeout 0
tcp-keepalive 300

# 安全配置
requirepass 123456
protected-mode no

# 持久化配置
save 900 1
save 300 10
save 60 10000

# 内存配置
maxmemory 256mb
maxmemory-policy allkeys-lru

# 日志配置
loglevel notice
logfile /var/log/redis/redis-server.log

# 数据目录
dir /var/lib/redis

# 后台运行
daemonize yes
supervised systemd

# 客户端连接
maxclients 10000

# 网络配置
tcp-backlog 511
EOF

    # 创建Redis日志目录
    mkdir -p /var/log/redis
    chown redis:redis /var/log/redis
    
    # 重启Redis服务
    systemctl restart redis-server
    systemctl enable redis-server
    
    log_info "✅ Redis配置完成"
    log_info "   - 绑定地址: 0.0.0.0:6379"
    log_info "   - 密码: 123456"
    log_info "   - 最大内存: 256MB"
    log_info "   - 允许外部连接: 是"
}

# 配置防火墙
configure_firewall() {
    log_step "🔥 配置防火墙端口..."
    
    # 检查ufw是否安装
    if command -v ufw >/dev/null 2>&1; then
        # 开放MySQL端口
        ufw allow 3306/tcp
        log_info "✅ 开放MySQL端口 3306"
        
        # 开放Redis端口
        ufw allow 6379/tcp
        log_info "✅ 开放Redis端口 6379"
        
        # 重新加载防火墙规则
        ufw reload 2>/dev/null || true
    else
        log_warn "⚠️  UFW防火墙未安装，请手动配置防火墙规则"
    fi
    
    # 如果使用iptables
    if command -v iptables >/dev/null 2>&1; then
        iptables -A INPUT -p tcp --dport 3306 -j ACCEPT
        iptables -A INPUT -p tcp --dport 6379 -j ACCEPT
        
        # 保存iptables规则
        if command -v iptables-save >/dev/null 2>&1; then
            iptables-save > /etc/iptables/rules.v4 2>/dev/null || true
        fi
        
        log_info "✅ iptables规则已添加"
    fi
}

# 测试连接
test_connections() {
    log_step "🧪 测试服务连接..."
    
    # 测试MySQL
    if systemctl is-active --quiet mysql; then
        log_info "✅ MySQL服务运行正常"
        
        # 测试MySQL连接
        if mysql -u root -p123456 -e "SELECT 1;" >/dev/null 2>&1; then
            log_info "✅ MySQL连接测试成功"
        else
            log_error "❌ MySQL连接测试失败"
        fi
    else
        log_error "❌ MySQL服务未运行"
    fi
    
    # 测试Redis
    if systemctl is-active --quiet redis-server; then
        log_info "✅ Redis服务运行正常"
        
        # 测试Redis连接
        if redis-cli -a 123456 ping >/dev/null 2>&1; then
            log_info "✅ Redis连接测试成功"
        else
            log_error "❌ Redis连接测试失败"
        fi
    else
        log_error "❌ Redis服务未运行"
    fi
}

# 显示服务状态
show_status() {
    log_step "📊 服务状态信息..."
    
    echo ""
    echo "=== MySQL状态 ==="
    systemctl status mysql --no-pager -l || true
    
    echo ""
    echo "=== Redis状态 ==="
    systemctl status redis-server --no-pager -l || true
    
    echo ""
    echo "=== 端口监听状态 ==="
    netstat -tlnp | grep -E ':(3306|6379)' || true
}

# 显示连接信息
show_connection_info() {
    log_step "📋 连接信息..."
    
    # 获取服务器IP
    SERVER_IP=$(hostname -I | awk '{print $1}')
    
    echo ""
    echo "=================================="
    echo "🎉 安装配置完成！"
    echo "=================================="
    echo ""
    echo "📊 MySQL连接信息:"
    echo "   主机: $SERVER_IP"
    echo "   端口: 3306"
    echo "   用户: root"
    echo "   密码: 123456"
    echo "   连接命令: mysql -h $SERVER_IP -u root -p123456"
    echo ""
    echo "📊 Redis连接信息:"
    echo "   主机: $SERVER_IP"
    echo "   端口: 6379"
    echo "   密码: 123456"
    echo "   连接命令: redis-cli -h $SERVER_IP -p 6379 -a 123456"
    echo ""
    echo "🔥 防火墙端口已开放: 3306, 6379"
    echo "🌐 已配置允许外部连接"
    echo ""
    echo "=================================="
}

# 主函数
main() {
    log_info "🚀 开始Ubuntu MySQL和Redis安装脚本..."
    
    # 检查权限
    check_root
    
    # 更新系统
    update_system
    
    # 卸载旧版本
    uninstall_mysql
    uninstall_redis
    
    # 安装MySQL
    install_mysql
    configure_mysql
    
    # 安装Redis
    install_redis
    configure_redis
    
    # 配置防火墙
    configure_firewall
    
    # 测试连接
    test_connections
    
    # 显示状态
    show_status
    
    # 显示连接信息
    show_connection_info
    
    log_info "🎉 所有操作完成！"
}

# 执行主函数
main "$@"
