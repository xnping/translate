#!/bin/bash

echo "=== 诊断静态文件访问问题 ==="
echo

# 1. 检查当前目录
echo "1. 当前目录:"
pwd
echo

# 2. 检查项目结构
echo "2. 项目结构:"
ls -la
echo

# 3. 检查static目录
echo "3. static目录权限和内容:"
if [ -d "static" ]; then
    ls -la static/
    echo
    echo "static目录权限: $(stat -c '%a %U:%G' static/)"
else
    echo "❌ static目录不存在"
fi
echo

# 4. 检查关键文件
echo "4. 关键文件检查:"
files=("static/apidemo.md" "static/index.html")
for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file 存在"
        echo "   权限: $(stat -c '%a %U:%G' "$file")"
        echo "   大小: $(stat -c '%s' "$file") bytes"
    else
        echo "❌ $file 不存在"
    fi
done
echo

# 5. 检查Nginx配置
echo "5. Nginx配置:"
if [ -f "/etc/nginx/sites-enabled/translation-api" ]; then
    echo "✅ Nginx配置文件存在"
    echo "配置内容:"
    cat /etc/nginx/sites-enabled/translation-api
else
    echo "❌ Nginx配置文件不存在"
fi
echo

# 6. 检查Nginx进程用户
echo "6. Nginx进程用户:"
ps aux | grep nginx | grep -v grep
echo

# 7. 检查Nginx错误日志
echo "7. Nginx错误日志 (最近10行):"
if [ -f "/var/log/nginx/error.log" ]; then
    tail -10 /var/log/nginx/error.log
else
    echo "错误日志文件不存在"
fi
echo

# 8. 测试文件访问
echo "8. 测试文件访问:"
if [ -f "static/apidemo.md" ]; then
    echo "尝试读取 static/apidemo.md:"
    if head -3 static/apidemo.md; then
        echo "✅ 文件可读"
    else
        echo "❌ 文件不可读"
    fi
else
    echo "❌ apidemo.md 文件不存在"
fi
echo

# 9. 检查SELinux状态
echo "9. SELinux状态:"
if command -v getenforce &> /dev/null; then
    getenforce
else
    echo "SELinux 未安装"
fi
echo

echo "=== 诊断完成 ==="
