#!/bin/bash

# =============================================================================
# Ubuntu系统Jenkins安装脚本 - 修复版
# 以root用户执行
# =============================================================================

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

print_step() {
    echo -e "${BLUE}[步骤]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[成功]${NC} $1"
}

print_error() {
    echo -e "${RED}[错误]${NC} $1"
}

# 检查root权限
if [ "$(id -u)" -ne 0 ]; then
    print_error "请以root用户运行此脚本"
    exit 1
fi

# 更新系统
update_system() {
    print_step "更新系统包..."
    apt update || true  # 即使失败也继续
    apt upgrade -y
    print_success "系统更新完成"
}

# 安装Java
install_java() {
    print_step "安装Java..."
    apt install -y openjdk-17-jdk
    
    if [ $? -eq 0 ]; then
        print_success "Java安装完成"
        java -version
    else
        print_error "Java安装失败"
        exit 1
    fi
}

# 安装Jenkins
install_jenkins() {
    print_step "安装Jenkins..."
    
    # 安装必要的工具
    apt install -y wget gnupg curl
    
    print_step "添加Jenkins仓库密钥..."
    
    # 方法1：使用apt-key (旧方法，但在某些系统上更可靠)
    wget -q -O - https://pkg.jenkins.io/debian-stable/jenkins.io.key | apt-key add -
    
    # 添加Jenkins存储库
    echo "deb https://pkg.jenkins.io/debian-stable binary/" > /etc/apt/sources.list.d/jenkins.list
    
    print_step "更新包列表..."
    apt update
    
    if [ $? -ne 0 ]; then
        print_step "尝试替代方法添加Jenkins仓库..."
        # 方法2：使用新的推荐方法
        rm -f /etc/apt/sources.list.d/jenkins.list
        
        curl -fsSL https://pkg.jenkins.io/debian-stable/jenkins.io-2023.key | sudo tee \
            /usr/share/keyrings/jenkins-keyring.asc > /dev/null
            
        echo "deb [signed-by=/usr/share/keyrings/jenkins-keyring.asc] https://pkg.jenkins.io/debian-stable binary/" | sudo tee \
            /etc/apt/sources.list.d/jenkins.list > /dev/null
            
        apt update
    fi
    
    # 如果仍然失败，尝试第三种方法
    if [ $? -ne 0 ]; then
        print_step "尝试第三种方法添加Jenkins仓库..."
        # 方法3：直接导入密钥
        rm -f /etc/apt/sources.list.d/jenkins.list
        apt-key del "Jenkins Project" 2>/dev/null || true
        
        curl -fsSL https://pkg.jenkins.io/debian-stable/jenkins.io-2023.key | gpg --dearmor | sudo tee \
            /usr/share/keyrings/jenkins.gpg > /dev/null
            
        echo "deb [signed-by=/usr/share/keyrings/jenkins.gpg] https://pkg.jenkins.io/debian-stable binary/" | sudo tee \
            /etc/apt/sources.list.d/jenkins.list > /dev/null
            
        apt update
    fi
    
    print_step "安装Jenkins包..."
    apt install -y jenkins
    
    if [ $? -eq 0 ]; then
        # 启动Jenkins服务
        systemctl start jenkins
        systemctl enable jenkins
        print_success "Jenkins安装完成"
    else
        print_error "Jenkins安装失败"
        exit 1
    fi
}

# 安装其他有用工具
install_tools() {
    print_step "安装其他工具..."
    apt install -y git curl wget unzip net-tools
    print_success "工具安装完成"
}

# 配置防火墙
configure_firewall() {
    print_step "配置防火墙..."
    
    # 检查ufw是否安装
    if ! command -v ufw &> /dev/null; then
        apt install -y ufw
    fi
    
    # 允许SSH和Jenkins端口
    ufw allow ssh
    ufw allow 8080
    
    # 如果防火墙未启用，则启用它
    if ! ufw status | grep -q "Status: active"; then
        echo "y" | ufw enable || true
    fi
    
    print_success "防火墙配置完成"
}

# 获取初始管理员密码
get_admin_password() {
    print_step "获取Jenkins初始管理员密码..."
    
    # 等待Jenkins完全启动
    echo "等待Jenkins启动，这可能需要几分钟..."
    sleep 30
    
    # 检查Jenkins是否正在运行
    if systemctl is-active --quiet jenkins; then
        print_success "Jenkins服务已成功启动"
    else
        print_error "Jenkins服务未能启动，请检查日志"
        systemctl status jenkins
    fi
    
    # 获取密码
    if [ -f /var/lib/jenkins/secrets/initialAdminPassword ]; then
        JENKINS_PASSWORD=$(cat /var/lib/jenkins/secrets/initialAdminPassword)
        echo "Jenkins初始管理员密码: $JENKINS_PASSWORD"
    else
        print_error "无法找到初始管理员密码文件，Jenkins可能尚未完全启动"
        echo "请稍后运行: cat /var/lib/jenkins/secrets/initialAdminPassword"
    fi
    
    # 获取服务器IP
    SERVER_IP=$(hostname -I | awk '{print $1}')
    echo "请访问 http://$SERVER_IP:8080 完成Jenkins设置"
}

# 创建管理脚本
create_management_scripts() {
    print_step "创建管理脚本..."
    
    # 状态检查脚本
    cat > /root/jenkins-status.sh << 'EOF'
#!/bin/bash
echo "=== Jenkins状态 ==="
systemctl status jenkins --no-pager -l
echo
echo "=== 端口监听 ==="
netstat -tlnp | grep :8080 || echo "端口8080未监听"
EOF
    
    # 重启脚本
    cat > /root/jenkins-restart.sh << 'EOF'
#!/bin/bash
systemctl restart jenkins
echo "Jenkins服务已重启"
EOF
    
    # 日志脚本
    cat > /root/jenkins-logs.sh << 'EOF'
#!/bin/bash
journalctl -u jenkins -f --no-pager
EOF
    
    # 获取密码脚本
    cat > /root/jenkins-password.sh << 'EOF'
#!/bin/bash
if [ -f /var/lib/jenkins/secrets/initialAdminPassword ]; then
    echo "Jenkins初始管理员密码:"
    cat /var/lib/jenkins/secrets/initialAdminPassword
else
    echo "密码文件不存在，Jenkins可能尚未完全启动"
fi
EOF
    
    chmod +x /root/jenkins-*.sh
    
    print_success "管理脚本创建完成"
}

# 主函数
main() {
    echo "开始安装Jenkins..."
    
    update_system
    install_java
    install_tools
    install_jenkins
    configure_firewall
    create_management_scripts
    get_admin_password
    
    echo
    echo "Jenkins安装完成！"
    echo "管理命令:"
    echo "  查看状态: /root/jenkins-status.sh"
    echo "  重启服务: /root/jenkins-restart.sh"
    echo "  查看日志: /root/jenkins-logs.sh"
    echo "  查看密码: /root/jenkins-password.sh"
}

# 执行主函数
main