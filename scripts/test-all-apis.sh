#!/bin/bash

# =============================================================================
# 翻译API接口全面测试脚本
# 测试 http://8.138.177.105 的所有API接口
# =============================================================================

BASE_URL="http://8.138.177.105"
TIMEOUT=15

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 统计变量
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================${NC}"
}

print_test() {
    echo -e "${YELLOW}[TEST]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✅ PASS]${NC} $1"
    ((PASSED_TESTS++))
}

print_fail() {
    echo -e "${RED}[❌ FAIL]${NC} $1"
    ((FAILED_TESTS++))
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# 通用API测试函数
test_api() {
    local name="$1"
    local method="$2"
    local endpoint="$3"
    local data="$4"
    local expected_status="${5:-200}"

    ((TOTAL_TESTS++))
    print_test "$name"

    local curl_cmd="curl -s -w '%{http_code}' -o /tmp/api_response.json --connect-timeout $TIMEOUT"

    if [ "$method" = "POST" ]; then
        curl_cmd="$curl_cmd -X POST -H 'Content-Type: application/json'"
        if [ -n "$data" ]; then
            curl_cmd="$curl_cmd -d '$data'"
        fi
    fi

    curl_cmd="$curl_cmd $BASE_URL$endpoint"

    # 执行请求
    local http_code
    http_code=$(eval $curl_cmd)

    # 读取响应内容
    local response=""
    if [ -f "/tmp/api_response.json" ]; then
        response=$(cat /tmp/api_response.json)
    fi

    # 判断结果
    if [ "$http_code" = "$expected_status" ]; then
        print_success "$name - HTTP $http_code"

        # 显示响应内容并验证
        if [ -n "$response" ] && [ "$response" != "null" ]; then
            # 验证翻译接口响应
            if [[ "$endpoint" == *"/translate"* ]] && [[ "$method" == "POST" ]]; then
                if echo "$response" | grep -q "trans_result"; then
                    print_info "✅ 翻译响应格式正确"
                    # 提取翻译结果
                    local translated=$(echo "$response" | grep -o '"dst":"[^"]*"' | head -1 | cut -d'"' -f4)
                    if [ -n "$translated" ]; then
                        print_info "翻译结果: $translated"
                    fi
                else
                    print_info "⚠️ 翻译响应格式异常"
                fi
            elif [[ "$endpoint" == "/health" ]]; then
                if echo "$response" | grep -q "status"; then
                    print_info "✅ 健康检查响应正确"
                else
                    print_info "⚠️ 健康检查响应异常"
                fi
            else
                local short_response=$(echo "$response" | head -c 100)
                print_info "响应: $short_response..."
            fi
        fi
    else
        print_fail "$name - HTTP $http_code (期望: $expected_status)"
        if [ -n "$response" ]; then
            print_info "错误响应: $response"
        fi
    fi

    echo
}

# 开始测试
main() {
    print_header "翻译API接口全面测试"
    echo "测试服务器: $BASE_URL"
    echo "超时时间: ${TIMEOUT}秒"
    echo

    # 1. 基础接口测试
    print_header "基础接口测试"

    test_api "健康检查" "GET" "/health"
    test_api "获取支持语言列表" "GET" "/api/languages"

    # 2. 通用翻译接口测试
    print_header "通用翻译接口测试"

    test_api "中文翻译为英文" "POST" "/api/translate" \
        '{"text":"你好世界","from_lang":"zh","to_lang":"en","font_size":"24px"}'

    test_api "自动检测语言翻译为中文" "POST" "/api/translate" \
        '{"text":"Hello World","from_lang":"auto","to_lang":"zh"}'

    test_api "中文翻译为泰语" "POST" "/api/translate" \
        '{"text":"你好","from_lang":"zh","to_lang":"th"}'

    test_api "中文翻译为越南语" "POST" "/api/translate" \
        '{"text":"谢谢","from_lang":"zh","to_lang":"vie"}'

    # 3. 批量翻译接口测试
    print_header "批量翻译接口测试"

    test_api "批量翻译(对象格式)" "POST" "/api/batch/translate" \
        '{"items":[{"text":"你好","id":"greeting"},{"text":"世界","id":"world"}],"from_lang":"zh","to_lang":"en","font_size":"20px"}'

    test_api "批量翻译(混合格式)" "POST" "/api/batch/translate" \
        '{"items":[{"text":"朋友","id":"friend"},"中国"],"from_lang":"zh","to_lang":"en"}'

    # 4. 单一目标语言翻译接口测试
    print_header "单一目标语言翻译接口测试"

    # 支持的语言接口
    declare -A languages=(
        ["english"]="en"
        ["thai"]="th"
        ["vietnamese"]="vie"
        ["indonesian"]="id"
        ["malay"]="may"
        ["filipino"]="fil"
        ["burmese"]="bur"
        ["khmer"]="hkm"
        ["lao"]="lao"
        ["tamil"]="tam"
    )

    for lang_name in "${!languages[@]}"; do
        test_api "翻译到${lang_name}" "POST" "/api/translate_to_${lang_name}" \
            '{"text":"你好世界","font_size":"24px"}'
    done

    # 5. 批量单一目标语言翻译接口测试
    print_header "批量单一目标语言翻译接口测试"

    # 测试几个主要语言的批量接口
    for lang_name in "english" "thai" "vietnamese"; do
        test_api "批量翻译到${lang_name}" "POST" "/api/batch/translate_to_${lang_name}" \
            '{"items":[{"text":"你好","id":"greeting"},{"text":"世界","id":"world"},"中国"],"font_size":"20px"}'
    done

    # 6. 优化翻译接口测试
    print_header "优化翻译接口测试"

    test_api "优化翻译接口" "POST" "/api/translate_optimized" \
        '{"text":"优化接口测试","from_lang":"zh","to_lang":"en"}'

    # 7. 监控和统计接口测试
    print_header "监控和统计接口测试"

    test_api "性能统计" "GET" "/api/performance_stats"
    test_api "缓存信息" "GET" "/api/cache_info"

    # 8. 错误情况测试
    print_header "错误情况测试"

    test_api "无效接口" "GET" "/api/invalid_endpoint" "" "404"
    test_api "无效参数" "POST" "/api/translate" '{"invalid":"data"}' "422"
    test_api "空文本翻译" "POST" "/api/translate" '{"text":"","from_lang":"zh","to_lang":"en"}' "422"

    # 9. 静态文件测试
    print_header "静态文件测试"

    test_api "API文档文件" "GET" "/static/apidemo.md"
    test_api "主页文件" "GET" "/static/index.html"

    # 10. 压力测试（简单）
    print_header "简单压力测试"

    print_test "连续5次翻译请求"
    local success_count=0
    for i in {1..5}; do
        local http_code
        http_code=$(curl -s -w '%{http_code}' -o /dev/null --connect-timeout 5 \
            -X POST -H 'Content-Type: application/json' \
            -d '{"text":"测试'$i'","from_lang":"zh","to_lang":"en"}' \
            "$BASE_URL/api/translate")

        if [ "$http_code" = "200" ]; then
            ((success_count++))
        fi
        sleep 0.5
    done

    if [ $success_count -eq 5 ]; then
        print_success "压力测试 - 5/5 请求成功"
        ((PASSED_TESTS++))
    else
        print_fail "压力测试 - $success_count/5 请求成功"
        ((FAILED_TESTS++))
    fi
    ((TOTAL_TESTS++))

    # 测试结果汇总
    print_header "测试结果汇总"

    echo "总测试数: $TOTAL_TESTS"
    echo -e "通过测试: ${GREEN}$PASSED_TESTS${NC}"
    echo -e "失败测试: ${RED}$FAILED_TESTS${NC}"

    local success_rate
    success_rate=$(echo "scale=1; $PASSED_TESTS * 100 / $TOTAL_TESTS" | bc -l 2>/dev/null || echo "0")
    echo "成功率: ${success_rate}%"

    echo
    if [ $FAILED_TESTS -eq 0 ]; then
        print_success "🎉 所有测试通过！API服务运行正常"
    elif [ $PASSED_TESTS -gt $FAILED_TESTS ]; then
        echo -e "${YELLOW}⚠️ 部分测试失败，但主要功能正常${NC}"
    else
        echo -e "${RED}❌ 多数测试失败，请检查服务状态${NC}"
    fi

    # 清理临时文件
    rm -f /tmp/api_response.json

    echo
    echo "详细测试完成！"
    echo "如需查看服务日志: journalctl -u translation-api -f"
}

# 检查依赖
if ! command -v curl &> /dev/null; then
    echo "错误: 需要安装curl"
    exit 1
fi

if ! command -v bc &> /dev/null; then
    echo "安装bc计算器..."
    apt install -y bc 2>/dev/null || echo "警告: 无法安装bc，成功率计算可能不准确"
fi

# 运行测试
main "$@"
