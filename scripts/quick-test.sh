#!/bin/bash

# =============================================================================
# 快速API测试脚本
# =============================================================================

BASE_URL="http://8.138.177.105"

echo "🚀 快速测试翻译API接口"
echo "服务器: $BASE_URL"
echo

# 测试函数
test_quick() {
    local name="$1"
    local method="$2"
    local endpoint="$3"
    local data="$4"
    
    echo -n "测试 $name ... "
    
    local cmd="curl -s -w '%{http_code}' -o /tmp/response.json --connect-timeout 10"
    if [ "$method" = "POST" ]; then
        cmd="$cmd -X POST -H 'Content-Type: application/json' -d '$data'"
    fi
    cmd="$cmd $BASE_URL$endpoint"
    
    local http_code
    http_code=$(eval $cmd)
    
    if [ "$http_code" = "200" ]; then
        echo "✅ 成功 (HTTP $http_code)"
        
        # 显示翻译结果
        if [[ "$endpoint" == *"/translate"* ]] && [ -f "/tmp/response.json" ]; then
            local result=$(cat /tmp/response.json | grep -o '"dst":"[^"]*"' | head -1 | cut -d'"' -f4)
            if [ -n "$result" ]; then
                echo "   翻译结果: $result"
            fi
        fi
    else
        echo "❌ 失败 (HTTP $http_code)"
        if [ -f "/tmp/response.json" ]; then
            local error=$(cat /tmp/response.json | head -c 100)
            echo "   错误: $error"
        fi
    fi
}

# 核心接口测试
echo "=== 核心接口测试 ==="
test_quick "健康检查" "GET" "/health"
test_quick "语言列表" "GET" "/api/languages"

echo
echo "=== 翻译功能测试 ==="
test_quick "中文→英语" "POST" "/api/translate" '{"text":"你好世界","from_lang":"zh","to_lang":"en"}'
test_quick "中文→泰语" "POST" "/api/translate" '{"text":"你好","from_lang":"zh","to_lang":"th"}'
test_quick "中文→越南语" "POST" "/api/translate" '{"text":"谢谢","from_lang":"zh","to_lang":"vie"}'

echo
echo "=== 单一目标语言接口测试 ==="
test_quick "翻译到英语" "POST" "/api/translate_to_english" '{"text":"你好世界"}'
test_quick "翻译到泰语" "POST" "/api/translate_to_thai" '{"text":"早上好"}'
test_quick "翻译到越南语" "POST" "/api/translate_to_vietnamese" '{"text":"晚安"}'

echo
echo "=== 批量翻译测试 ==="
test_quick "批量翻译" "POST" "/api/batch/translate" '{"items":[{"text":"你好","id":"1"},"世界"],"from_lang":"zh","to_lang":"en"}'
test_quick "批量翻译到英语" "POST" "/api/batch/translate_to_english" '{"items":["你好","世界","朋友"]}'

echo
echo "=== 监控接口测试 ==="
test_quick "性能统计" "GET" "/api/performance_stats"
test_quick "缓存信息" "GET" "/api/cache_info"

echo
echo "=== 静态文件测试 ==="
test_quick "API文档" "GET" "/static/apidemo.md"
test_quick "主页文件" "GET" "/static/index.html"

# 清理
rm -f /tmp/response.json

echo
echo "🎯 快速测试完成！"
echo "如需详细测试，请运行: ./test-all-apis.sh"
