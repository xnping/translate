# 🚨 Jenkins CI/CD 故障排除指南

## 常见错误代码及解决方案

### 错误代码 127: Command not found

**症状**: `script returned exit code 127`

**原因**: 
- 命令未找到
- PATH环境变量问题
- Jenkins节点环境配置问题

**解决步骤**:

#### 1. 检查Jenkins节点环境

```bash
# 在Jenkins Pipeline中添加调试步骤
sh '''
    echo "当前用户: $(whoami)"
    echo "当前目录: $(pwd)"
    echo "PATH: $PATH"
    which python3 || echo "python3 not found"
    which git || echo "git not found"
'''
```

#### 2. 修复PATH环境变量

在Jenkinsfile中添加:
```groovy
environment {
    PATH = "/usr/local/bin:/usr/bin:/bin:/usr/local/sbin:/usr/sbin:/sbin:${env.PATH}"
}
```

#### 3. 检查Jenkins节点配置

1. 进入 Jenkins → Manage Jenkins → Manage Nodes and Clouds
2. 点击节点名称 → Configure
3. 检查 "Environment variables" 设置

### 错误代码 1: General errors

**症状**: `script returned exit code 1`

**常见原因**:
- SSH连接失败
- 权限问题
- 文件不存在
- 命令执行失败

**解决步骤**:

#### 1. SSH连接问题
```bash
# 测试SSH连接
ssh -o ConnectTimeout=10 root@45.204.6.32 "echo 'SSH连接正常'"
```

#### 2. 检查SSH密钥
- 确保私钥格式正确
- 检查公钥是否添加到服务器
- 验证凭据ID是否正确

### 错误代码 2: Misuse of shell builtins

**症状**: `script returned exit code 2`

**原因**: Shell脚本语法错误

**解决方案**:
- 检查脚本语法
- 使用 `bash -n script.sh` 验证语法
- 确保脚本有执行权限

## 🔧 调试步骤

### 步骤1: 使用调试版Jenkinsfile

1. 将 `Jenkinsfile` 重命名为 `Jenkinsfile.backup`
2. 将 `Jenkinsfile.debug` 重命名为 `Jenkinsfile`
3. 提交并推送到GitHub
4. 观察调试输出

### 步骤2: 检查Jenkins系统配置

#### 检查Java版本
```bash
java -version
```

#### 检查Jenkins版本
- 进入 Jenkins → Manage Jenkins → System Information

#### 检查插件状态
- 进入 Jenkins → Manage Jenkins → Manage Plugins
- 确保以下插件已安装并启用:
  - Git plugin
  - SSH Agent Plugin
  - Pipeline plugin

### 步骤3: 验证服务器环境

#### 连接到服务器
```bash
ssh root@45.204.6.32
```

#### 检查必需软件
```bash
# 检查Python
python3 --version

# 检查系统服务
systemctl status nginx
systemctl status redis

# 检查磁盘空间
df -h

# 检查内存
free -h
```

### 步骤4: 手动部署测试

如果Jenkins部署失败，可以尝试手动部署:

```bash
# 1. 克隆仓库到本地
git clone https://github.com/yourusername/translation-api.git
cd translation-api

# 2. 运行部署脚本
chmod +x scripts/deploy.sh
./scripts/deploy.sh --check  # 仅检查连接
./scripts/deploy.sh          # 完整部署
```

## 🔍 日志分析

### Jenkins构建日志

1. 进入失败的构建
2. 点击 "Console Output"
3. 查找错误关键词:
   - `ERROR`
   - `FAILED`
   - `exit code`
   - `Permission denied`

### 服务器日志

```bash
# 系统日志
journalctl -f

# Nginx日志
tail -f /var/log/nginx/error.log

# 应用日志
journalctl -u translation-api -f
```

## 🛠️ 常见修复方案

### 修复1: 重新配置SSH密钥

```bash
# 1. 生成新的SSH密钥
ssh-keygen -t rsa -b 4096 -C "jenkins@yourdomain.com"

# 2. 复制公钥到服务器
ssh-copy-id root@45.204.6.32

# 3. 在Jenkins中更新私钥
```

### 修复2: 重新安装Jenkins节点

```bash
# 1. 停止Jenkins
systemctl stop jenkins

# 2. 清理工作空间
rm -rf /var/lib/jenkins/workspace/*

# 3. 重启Jenkins
systemctl start jenkins
```

### 修复3: 更新服务器环境

```bash
# 1. 更新系统
apt update && apt upgrade -y

# 2. 重新安装Python
apt install -y python3 python3-pip python3-venv

# 3. 检查服务
systemctl restart nginx
systemctl restart redis
```

## 📞 获取帮助

### 收集调试信息

运行以下命令收集调试信息:

```bash
# 在Jenkins服务器上
./debug-jenkins.sh > jenkins-debug.log 2>&1

# 在目标服务器上
ssh root@45.204.6.32 "
    echo '=== 服务器环境信息 ===' > server-debug.log
    uname -a >> server-debug.log
    python3 --version >> server-debug.log 2>&1
    systemctl status nginx >> server-debug.log 2>&1
    systemctl status redis >> server-debug.log 2>&1
    df -h >> server-debug.log
    free -h >> server-debug.log
"
```

### 联系支持时提供

1. Jenkins构建日志
2. 错误代码和错误信息
3. 调试脚本输出
4. 服务器环境信息
5. 具体的操作步骤

---

**记住**: 大多数部署问题都是环境配置问题，耐心排查通常能找到解决方案！
