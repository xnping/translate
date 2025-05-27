#!/bin/bash
# Jenkins环境调试脚本

echo "=== Jenkins环境调试信息 ==="

echo "1. 当前用户和工作目录:"
whoami
pwd
ls -la

echo -e "\n2. 环境变量:"
env | sort

echo -e "\n3. PATH变量:"
echo $PATH

echo -e "\n4. 可用命令检查:"
which python3 || echo "python3 not found"
which pip3 || echo "pip3 not found"
which git || echo "git not found"
which curl || echo "curl not found"
which ssh || echo "ssh not found"
which scp || echo "scp not found"

echo -e "\n5. Python版本:"
python3 --version 2>/dev/null || echo "Python3 not available"

echo -e "\n6. 系统信息:"
uname -a
cat /etc/os-release

echo -e "\n7. 磁盘空间:"
df -h

echo -e "\n8. 内存使用:"
free -h

echo -e "\n9. Jenkins工作空间:"
ls -la $WORKSPACE 2>/dev/null || echo "WORKSPACE not set"

echo -e "\n10. SSH配置检查:"
ls -la ~/.ssh/ 2>/dev/null || echo "No SSH directory"

echo "=== 调试信息收集完成 ==="
