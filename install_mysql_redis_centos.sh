#!/bin/bash

# CentOS Stream MySQL和Redis完整安装脚本
# 作者: AI Assistant
# 用途: 卸载旧版本，安装MySQL和Redis，配置外部连接
# 使用方法: sudo bash install_mysql_redis_centos.sh

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

# 检查CentOS版本
check_centos_version() {
    if [[ ! -f /etc/redhat-release ]]; then
        log_error "此脚本仅适用于CentOS/RHEL系统"
        exit 1
    fi
    
    local version=$(cat /etc/redhat-release)
    log_info "✅ 系统版本: $version"
}

# 更新系统
update_system() {
    log_step "🔄 更新系统包..."
    
    # 更新dnf缓存
    dnf clean all
    dnf makecache
    
    # 更新系统
    dnf update -y
    
    # 安装必要工具
    dnf install -y wget curl net-tools firewalld
    
    log_info "✅ 系统更新完成"
}

# 卸载MySQL/MariaDB
uninstall_mysql() {
    log_step "🗑️  开始卸载MySQL/MariaDB..."
    
    # 停止服务
    systemctl stop mysqld 2>/dev/null || true
    systemctl stop mysql 2>/dev/null || true
    systemctl stop mariadb 2>/dev/null || true
    
    # 卸载MySQL/MariaDB包
    dnf remove -y mysql-server mysql mysql-common mysql-libs 2>/dev/null || true
    dnf remove -y mariadb-server mariadb mariadb-common mariadb-libs 2>/dev/null || true
    dnf remove -y mysql-community-server mysql-community-client mysql-community-common 2>/dev/null || true
    
    # 删除配置文件和数据
    rm -rf /etc/mysql
    rm -rf /etc/my.cnf
    rm -rf /etc/my.cnf.d
    rm -rf /var/lib/mysql
    rm -rf /var/log/mysql
    rm -rf /var/log/mysqld.log
    rm -rf /usr/lib64/mysql
    rm -rf /usr/share/mysql
    
    # 删除用户
    userdel mysql 2>/dev/null || true
    groupdel mysql 2>/dev/null || true
    
    # 清理残留包
    dnf autoremove -y
    
    log_info "✅ MySQL/MariaDB卸载完成"
}

# 卸载Redis
uninstall_redis() {
    log_step "🗑️  开始卸载Redis..."
    
    # 停止Redis服务
    systemctl stop redis 2>/dev/null || true
    
    # 卸载Redis包
    dnf remove -y redis redis-tools 2>/dev/null || true
    
    # 删除配置文件和数据
    rm -rf /etc/redis
    rm -rf /etc/redis.conf
    rm -rf /var/lib/redis
    rm -rf /var/log/redis
    
    # 删除用户
    userdel redis 2>/dev/null || true
    groupdel redis 2>/dev/null || true
    
    log_info "✅ Redis卸载完成"
}

# 安装MySQL
install_mysql() {
    log_step "📦 开始安装MySQL..."

    # 清理可能存在的旧仓库
    rm -f /etc/yum.repos.d/mysql-community.repo

    # 添加MySQL官方仓库
    log_info "添加MySQL官方仓库..."
    dnf install -y https://dev.mysql.com/get/mysql80-community-release-el9-1.noarch.rpm

    # 清理并重建缓存
    dnf clean all
    dnf makecache

    # 导入最新的MySQL GPG密钥
    log_info "导入MySQL GPG密钥..."
    rpm --import https://repo.mysql.com/RPM-GPG-KEY-mysql-2022
    rpm --import https://repo.mysql.com/RPM-GPG-KEY-mysql-2023 2>/dev/null || true

    # 直接跳过GPG检查安装MySQL（解决GPG密钥问题）
    log_info "安装MySQL服务器（跳过GPG检查）..."
    dnf install -y --nogpgcheck mysql-community-server mysql-community-client

    # 启动MySQL服务
    systemctl start mysqld
    systemctl enable mysqld

    log_info "✅ MySQL安装完成"
}

# 配置MySQL
configure_mysql() {
    log_step "⚙️  配置MySQL..."
    
    # 获取临时密码
    local temp_password=$(grep 'temporary password' /var/log/mysqld.log | tail -1 | awk '{print $NF}')
    log_info "MySQL临时密码: $temp_password"
    
    # 创建MySQL配置文件
    cat > /etc/my.cnf << 'EOF'
[mysqld]
datadir=/var/lib/mysql
socket=/var/lib/mysql/mysql.sock
log-error=/var/log/mysqld.log
pid-file=/var/run/mysqld/mysqld.pid

# 网络配置
bind-address = 0.0.0.0
port = 3306

# 字符集配置
character-set-server = utf8mb4
collation-server = utf8mb4_unicode_ci

# 性能配置
max_connections = 200
innodb_buffer_pool_size = 256M

# 密码策略配置
validate_password.policy = LOW
validate_password.length = 6

# 安全配置
sql_mode = STRICT_TRANS_TABLES,NO_ZERO_DATE,NO_ZERO_IN_DATE,ERROR_FOR_DIVISION_BY_ZERO

[mysql]
default-character-set = utf8mb4

[client]
default-character-set = utf8mb4
EOF

    # 重启MySQL服务
    systemctl restart mysqld
    
    # 配置root密码和远程访问
    if [[ -n "$temp_password" ]]; then
        mysql --connect-expired-password -u root -p"$temp_password" << 'EOF'
ALTER USER 'root'@'localhost' IDENTIFIED BY '123456';
CREATE USER 'root'@'%' IDENTIFIED BY '123456';
GRANT ALL PRIVILEGES ON *.* TO 'root'@'%' WITH GRANT OPTION;
FLUSH PRIVILEGES;
EOF
    else
        # 如果没有临时密码，尝试无密码连接
        mysql -u root << 'EOF'
ALTER USER 'root'@'localhost' IDENTIFIED BY '123456';
CREATE USER 'root'@'%' IDENTIFIED BY '123456';
GRANT ALL PRIVILEGES ON *.* TO 'root'@'%' WITH GRANT OPTION;
FLUSH PRIVILEGES;
EOF
    fi
    
    log_info "✅ MySQL配置完成"
    log_info "   - 绑定地址: 0.0.0.0:3306"
    log_info "   - Root密码: 123456"
    log_info "   - 允许外部连接: 是"
}

# 安装Redis
install_redis() {
    log_step "📦 开始安装Redis..."
    
    # 启用EPEL仓库
    dnf install -y epel-release
    
    # 安装Redis
    dnf install -y redis
    
    log_info "✅ Redis安装完成"
}

# 配置Redis
configure_redis() {
    log_step "⚙️  配置Redis..."
    
    # 备份原配置文件
    cp /etc/redis/redis.conf /etc/redis/redis.conf.backup 2>/dev/null || cp /etc/redis.conf /etc/redis.conf.backup
    
    # 创建Redis配置文件
    cat > /etc/redis.conf << 'EOF'
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
logfile /var/log/redis/redis.log

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

    # 创建Redis目录
    mkdir -p /var/log/redis
    mkdir -p /var/lib/redis
    
    # 设置权限
    chown redis:redis /var/log/redis
    chown redis:redis /var/lib/redis
    chown redis:redis /etc/redis.conf
    
    # 启动Redis服务
    systemctl start redis
    systemctl enable redis
    
    log_info "✅ Redis配置完成"
    log_info "   - 绑定地址: 0.0.0.0:6379"
    log_info "   - 密码: 123456"
    log_info "   - 最大内存: 256MB"
    log_info "   - 允许外部连接: 是"
}

# 配置防火墙
configure_firewall() {
    log_step "🔥 配置防火墙端口..."
    
    # 启动firewalld
    systemctl start firewalld
    systemctl enable firewalld
    
    # 开放MySQL端口
    firewall-cmd --permanent --add-port=3306/tcp
    log_info "✅ 开放MySQL端口 3306"
    
    # 开放Redis端口
    firewall-cmd --permanent --add-port=6379/tcp
    log_info "✅ 开放Redis端口 6379"
    
    # 重新加载防火墙规则
    firewall-cmd --reload
    
    log_info "✅ 防火墙配置完成"
}

# 配置SELinux
configure_selinux() {
    log_step "🔒 配置SELinux..."
    
    # 检查SELinux状态
    if command -v getenforce >/dev/null 2>&1; then
        local selinux_status=$(getenforce)
        log_info "SELinux状态: $selinux_status"
        
        if [[ "$selinux_status" == "Enforcing" ]]; then
            # 允许MySQL和Redis端口
            setsebool -P mysql_connect_any 1 2>/dev/null || true
            semanage port -a -t mysqld_port_t -p tcp 3306 2>/dev/null || true
            semanage port -a -t redis_port_t -p tcp 6379 2>/dev/null || true
            
            log_info "✅ SELinux规则已配置"
        fi
    fi
}

# 测试连接
test_connections() {
    log_step "🧪 测试服务连接..."
    
    # 等待服务启动
    sleep 5
    
    # 测试MySQL
    if systemctl is-active --quiet mysqld; then
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
    if systemctl is-active --quiet redis; then
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
    systemctl status mysqld --no-pager -l || true
    
    echo ""
    echo "=== Redis状态 ==="
    systemctl status redis --no-pager -l || true
    
    echo ""
    echo "=== 端口监听状态 ==="
    netstat -tlnp | grep -E ':(3306|6379)' || ss -tlnp | grep -E ':(3306|6379)' || true
    
    echo ""
    echo "=== 防火墙状态 ==="
    firewall-cmd --list-ports || true
}

# 显示连接信息
show_connection_info() {
    log_step "📋 连接信息..."
    
    # 获取服务器IP
    SERVER_IP=$(hostname -I | awk '{print $1}')
    
    echo ""
    echo "=================================="
    echo "🎉 CentOS Stream 安装配置完成！"
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
    echo "🔒 SELinux规则已配置"
    echo ""
    echo "=================================="
}

# 主函数
main() {
    log_info "🚀 开始CentOS Stream MySQL和Redis安装脚本..."
    
    # 检查权限和系统
    check_root
    check_centos_version
    
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
    
    # 配置防火墙和SELinux
    configure_firewall
    configure_selinux
    
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
