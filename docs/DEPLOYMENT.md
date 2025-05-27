# 翻译API部署指南

## 📋 概述

本文档介绍如何使用Jenkins进行翻译API的CI/CD部署。

## 🏗️ 部署架构

```
GitHub Repository
       ↓
   Jenkins Pipeline
       ↓
   Production Server (8.138.177.105)
       ↓
   [Nginx] → [Translation API] → [Redis]
```

## 🔧 Jenkins配置

### 1. 创建Jenkins Pipeline项目

1. 登录Jenkins管理界面
2. 点击"新建任务"
3. 选择"Pipeline"类型
4. 配置Git仓库地址

### 2. 配置SSH密钥

1. 在Jenkins中添加SSH私钥凭据
2. 凭据ID设置为: `production-server-key`
3. 确保公钥已添加到生产服务器

### 3. 环境变量配置

在Jenkins项目中配置以下环境变量：

```bash
DEPLOY_HOST=8.138.177.105
DEPLOY_USER=root
DEPLOY_PORT=9000
PROJECT_PATH=/home/translation-api
```

## 🚀 部署流程

### 自动部署（推荐）

当代码推送到`main`或`master`分支时，Jenkins会自动触发部署：

1. **代码检出**: 从GitHub拉取最新代码
2. **质量检查**: 语法检查、配置验证、安全扫描
3. **构建测试**: 创建测试环境并验证
4. **部署**: 上传文件到生产服务器
5. **配置**: 设置systemd服务和Nginx
6. **启动**: 启动服务并验证

### 手动部署

如果需要手动部署，可以使用部署脚本：

```bash
# 检查连接
./scripts/deploy.sh --check

# 创建备份
./scripts/deploy.sh --backup

# 完整部署
./scripts/deploy.sh
```

## 🔍 部署验证

部署完成后，系统会自动进行以下验证：

1. **健康检查**: `curl http://8.138.177.105/health`
2. **API测试**: `curl http://8.138.177.105/api/languages`
3. **服务状态**: `systemctl status translation-api`

## 📊 监控和日志

### 服务监控

```bash
# 查看服务状态
systemctl status translation-api

# 查看服务日志
journalctl -u translation-api -f

# 查看Nginx日志
tail -f /var/log/nginx/translation-api.access.log
tail -f /var/log/nginx/translation-api.error.log
```

### 性能监控

```bash
# 查看进程资源使用
top -p $(pgrep -f "python.*main.py")

# 查看端口监听
netstat -tlnp | grep :9000

# 查看Redis连接
redis-cli ping
```

## 🔄 回滚操作

如果部署出现问题，可以快速回滚：

### 自动回滚

Jenkins Pipeline配置了自动回滚功能，当部署验证失败时会自动回滚到上一个版本。

### 手动回滚

```bash
# 1. 停止服务
systemctl stop translation-api

# 2. 恢复备份
cd /home/backups/translation-api
tar -xzf backup_YYYYMMDD_HHMMSS.tar.gz -C /home/translation-api

# 3. 重启服务
systemctl start translation-api
```

## 🛠️ 故障排除

### 常见问题

1. **服务启动失败**
   ```bash
   # 查看详细错误
   journalctl -u translation-api --no-pager -n 50
   
   # 检查配置文件
   cd /home/translation-api
   source venv/bin/activate
   python scripts/config_manager.py validate
   ```

2. **Nginx配置错误**
   ```bash
   # 测试Nginx配置
   nginx -t
   
   # 重新加载配置
   systemctl reload nginx
   ```

3. **Redis连接失败**
   ```bash
   # 检查Redis状态
   systemctl status redis
   
   # 测试连接
   redis-cli ping
   ```

### 日志分析

```bash
# 应用日志
tail -f /home/translation-api/logs/app.log

# 系统日志
journalctl -u translation-api -f

# Nginx访问日志
tail -f /var/log/nginx/translation-api.access.log

# Nginx错误日志
tail -f /var/log/nginx/translation-api.error.log
```

## 🔐 安全配置

### 防火墙设置

```bash
# 允许HTTP和HTTPS
ufw allow 80/tcp
ufw allow 443/tcp

# 允许SSH（如果需要）
ufw allow 22/tcp

# 启用防火墙
ufw enable
```

### SSL证书（可选）

如果需要HTTPS支持：

```bash
# 安装Certbot
apt install certbot python3-certbot-nginx

# 获取SSL证书
certbot --nginx -d your-domain.com

# 自动续期
crontab -e
# 添加: 0 12 * * * /usr/bin/certbot renew --quiet
```

## 📈 性能优化

### 系统优化

```bash
# 增加文件描述符限制
echo "* soft nofile 65536" >> /etc/security/limits.conf
echo "* hard nofile 65536" >> /etc/security/limits.conf

# 优化内核参数
echo "net.core.somaxconn = 65536" >> /etc/sysctl.conf
echo "net.ipv4.tcp_max_syn_backlog = 65536" >> /etc/sysctl.conf
sysctl -p
```

### 应用优化

```bash
# 调整worker进程数
# 编辑 /etc/systemd/system/translation-api.service
# 添加环境变量: Environment=WORKERS=4
```

## 📞 联系支持

如果遇到部署问题，请：

1. 检查Jenkins构建日志
2. 查看服务器日志
3. 验证配置文件
4. 联系运维团队

---

**注意**: 请确保在生产环境中妥善保管SSH密钥和环境变量文件。
