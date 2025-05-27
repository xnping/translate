#!/usr/bin/env python3
"""
快速API测试脚本
"""

import requests
import json
import time

BASE_URL = "http://localhost:9000"

def test_api(name, method, endpoint, data=None):
    """测试API接口"""
    print(f"测试 {name}...", end=" ")

    try:
        start_time = time.time()

        if method == "GET":
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
        else:
            response = requests.post(f"{BASE_URL}{endpoint}", json=data, timeout=10)

        elapsed = time.time() - start_time

        if response.status_code == 200:
            print(f"✅ 成功 ({elapsed:.3f}s)")

            # 显示翻译结果
            if "translate" in endpoint and response.json().get("trans_result"):
                result = response.json()["trans_result"][0]
                print(f"   翻译: {result['src']} → {result['dst']}")

            return True
        else:
            print(f"❌ 失败 (HTTP {response.status_code})")
            return False

    except Exception as e:
        print(f"❌ 错误: {e}")
        return False

def main():
    print("🧪 快速API测试")
    print("=" * 40)

    tests = [
        ("健康检查", "GET", "/health", None),
        ("语言列表", "GET", "/api/languages", None),
        ("中文→英语", "POST", "/api/translate", {"text": "你好世界", "from_lang": "zh", "to_lang": "en"}),
        ("翻译到英语", "POST", "/api/translate_to_english", {"text": "你好世界"}),
        ("批量翻译", "POST", "/api/batch/translate", {"items": ["你好", "世界"], "from_lang": "zh", "to_lang": "en"}),
        ("性能统计", "GET", "/api/performance_stats", None),
        ("主页", "GET", "/", None),
    ]

    passed = 0
    total = len(tests)

    for name, method, endpoint, data in tests:
        if test_api(name, method, endpoint, data):
            passed += 1
        time.sleep(0.5)  # 避免请求过快

    print("\n" + "=" * 40)
    print(f"测试结果: {passed}/{total} 通过")

    if passed == total:
        print("🎉 所有测试通过！API服务运行正常")
    elif passed >= total * 0.8:
        print("⚠️ 大部分测试通过，有少量问题")
    else:
        print("❌ 多个测试失败，需要检查服务")

if __name__ == "__main__":
    main()
