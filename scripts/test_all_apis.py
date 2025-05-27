#!/usr/bin/env python3
"""
翻译API全接口测试脚本
测试所有API接口的功能和性能
"""

import asyncio
import aiohttp
import json
import time
import sys
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class TestResult:
    """测试结果"""
    name: str
    success: bool
    status_code: int
    response_time: float
    response_data: Any = None
    error_message: str = None


class APITester:
    """API测试器"""
    
    def __init__(self, base_url: str = "http://8.138.177.105"):
        self.base_url = base_url.rstrip('/')
        self.session: Optional[aiohttp.ClientSession] = None
        self.results: List[TestResult] = []
        
        # 测试统计
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.total_time = 0.0
        
        # 测试数据
        self.test_texts = {
            "zh": ["你好世界", "早上好", "谢谢", "再见", "欢迎"],
            "en": ["Hello World", "Good morning", "Thank you", "Goodbye", "Welcome"],
            "simple": ["测试", "API", "翻译"]
        }
        
        # 支持的语言
        self.languages = ["en", "th", "vie", "id", "ms", "fil", "my", "km", "lo", "ta"]
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            connector=aiohttp.TCPConnector(limit=100)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()
    
    def print_header(self, title: str):
        """打印标题"""
        print(f"\n{'='*60}")
        print(f"🧪 {title}")
        print(f"{'='*60}")
    
    def print_result(self, result: TestResult):
        """打印测试结果"""
        status = "✅ PASS" if result.success else "❌ FAIL"
        print(f"{status} {result.name} - {result.response_time:.3f}s - HTTP {result.status_code}")
        
        if not result.success and result.error_message:
            print(f"     错误: {result.error_message}")
        elif result.success and result.response_data:
            # 显示部分响应数据
            if isinstance(result.response_data, dict):
                if "trans_result" in result.response_data:
                    trans = result.response_data["trans_result"][0]
                    print(f"     翻译: {trans.get('src', '')} → {trans.get('dst', '')}")
                elif "status" in result.response_data:
                    print(f"     状态: {result.response_data['status']}")
                elif "results" in result.response_data:
                    count = len(result.response_data["results"])
                    print(f"     批量结果: {count} 项")
    
    async def make_request(self, method: str, endpoint: str, data: Dict = None) -> TestResult:
        """发送HTTP请求"""
        start_time = time.time()
        test_name = f"{method} {endpoint}"
        
        try:
            url = f"{self.base_url}{endpoint}"
            
            if method.upper() == "GET":
                async with self.session.get(url) as response:
                    response_time = time.time() - start_time
                    response_data = await response.json()
                    
                    return TestResult(
                        name=test_name,
                        success=response.status == 200,
                        status_code=response.status,
                        response_time=response_time,
                        response_data=response_data,
                        error_message=None if response.status == 200 else f"HTTP {response.status}"
                    )
            
            elif method.upper() == "POST":
                headers = {"Content-Type": "application/json"}
                async with self.session.post(url, json=data, headers=headers) as response:
                    response_time = time.time() - start_time
                    
                    try:
                        response_data = await response.json()
                    except:
                        response_data = await response.text()
                    
                    return TestResult(
                        name=test_name,
                        success=response.status == 200,
                        status_code=response.status,
                        response_time=response_time,
                        response_data=response_data,
                        error_message=None if response.status == 200 else f"HTTP {response.status}"
                    )
        
        except Exception as e:
            response_time = time.time() - start_time
            return TestResult(
                name=test_name,
                success=False,
                status_code=0,
                response_time=response_time,
                error_message=str(e)
            )
    
    async def test_basic_endpoints(self):
        """测试基础接口"""
        self.print_header("基础接口测试")
        
        tests = [
            ("GET", "/health"),
            ("GET", "/api/languages"),
        ]
        
        for method, endpoint in tests:
            result = await self.make_request(method, endpoint)
            self.results.append(result)
            self.print_result(result)
            
            if result.success:
                self.passed_tests += 1
            else:
                self.failed_tests += 1
            self.total_tests += 1
            self.total_time += result.response_time
    
    async def test_translation_endpoints(self):
        """测试翻译接口"""
        self.print_header("翻译接口测试")
        
        # 通用翻译接口
        test_cases = [
            {
                "name": "中文→英语",
                "data": {"text": "你好世界", "from_lang": "zh", "to_lang": "en"}
            },
            {
                "name": "自动检测→中文", 
                "data": {"text": "Hello World", "from_lang": "auto", "to_lang": "zh"}
            },
            {
                "name": "中文→泰语",
                "data": {"text": "你好", "from_lang": "zh", "to_lang": "th"}
            },
            {
                "name": "中文→越南语",
                "data": {"text": "谢谢", "from_lang": "zh", "to_lang": "vie"}
            }
        ]
        
        for case in test_cases:
            result = await self.make_request("POST", "/api/translate", case["data"])
            result.name = f"通用翻译 - {case['name']}"
            self.results.append(result)
            self.print_result(result)
            
            if result.success:
                self.passed_tests += 1
            else:
                self.failed_tests += 1
            self.total_tests += 1
            self.total_time += result.response_time
        
        # 优化翻译接口
        result = await self.make_request("POST", "/api/translate_optimized", {
            "text": "优化接口测试", "from_lang": "zh", "to_lang": "en"
        })
        result.name = "优化翻译接口"
        self.results.append(result)
        self.print_result(result)
        
        if result.success:
            self.passed_tests += 1
        else:
            self.failed_tests += 1
        self.total_tests += 1
        self.total_time += result.response_time
    
    async def test_single_target_endpoints(self):
        """测试单一目标语言接口"""
        self.print_header("单一目标语言接口测试")
        
        for lang in self.languages:
            endpoint = f"/api/translate_to_{lang}" if lang != "vie" else "/api/translate_to_vietnamese"
            if lang == "id":
                endpoint = "/api/translate_to_indonesian"
            elif lang == "ms":
                endpoint = "/api/translate_to_malay"
            elif lang == "fil":
                endpoint = "/api/translate_to_filipino"
            elif lang == "my":
                endpoint = "/api/translate_to_burmese"
            elif lang == "km":
                endpoint = "/api/translate_to_khmer"
            elif lang == "lo":
                endpoint = "/api/translate_to_lao"
            elif lang == "ta":
                endpoint = "/api/translate_to_tamil"
            elif lang == "th":
                endpoint = "/api/translate_to_thai"
            elif lang == "en":
                endpoint = "/api/translate_to_english"
            
            data = {"text": "你好世界", "font_size": "24px"}
            result = await self.make_request("POST", endpoint, data)
            result.name = f"翻译到{lang}"
            self.results.append(result)
            self.print_result(result)
            
            if result.success:
                self.passed_tests += 1
            else:
                self.failed_tests += 1
            self.total_tests += 1
            self.total_time += result.response_time
            
            # 避免请求过快
            await asyncio.sleep(0.1)
    
    async def test_batch_endpoints(self):
        """测试批量翻译接口"""
        self.print_header("批量翻译接口测试")
        
        # 通用批量翻译
        batch_data = {
            "items": [
                {"text": "你好", "id": "greeting"},
                {"text": "世界", "id": "world"},
                "中国",
                "朋友"
            ],
            "from_lang": "zh",
            "to_lang": "en",
            "font_size": "20px"
        }
        
        result = await self.make_request("POST", "/api/batch/translate", batch_data)
        result.name = "批量翻译"
        self.results.append(result)
        self.print_result(result)
        
        if result.success:
            self.passed_tests += 1
        else:
            self.failed_tests += 1
        self.total_tests += 1
        self.total_time += result.response_time
        
        # 批量单一目标语言（测试几个主要语言）
        main_languages = ["english", "thai", "vietnamese"]
        for lang in main_languages:
            endpoint = f"/api/batch/translate_to_{lang}"
            data = {
                "items": ["你好", "世界", "朋友"],
                "font_size": "18px"
            }
            
            result = await self.make_request("POST", endpoint, data)
            result.name = f"批量翻译到{lang}"
            self.results.append(result)
            self.print_result(result)
            
            if result.success:
                self.passed_tests += 1
            else:
                self.failed_tests += 1
            self.total_tests += 1
            self.total_time += result.response_time
            
            await asyncio.sleep(0.1)
    
    async def test_system_endpoints(self):
        """测试系统接口"""
        self.print_header("系统监控接口测试")
        
        endpoints = [
            "/api/performance_stats",
            "/api/cache_info",
            "/api/system/status",
            "/api/config/current",
            "/api/config/versions"
        ]
        
        for endpoint in endpoints:
            result = await self.make_request("GET", endpoint)
            self.results.append(result)
            self.print_result(result)
            
            if result.success:
                self.passed_tests += 1
            else:
                self.failed_tests += 1
            self.total_tests += 1
            self.total_time += result.response_time
    
    async def test_static_files(self):
        """测试静态文件"""
        self.print_header("静态文件测试")
        
        static_files = [
            "/static/apidemo.md",
            "/static/index.html",
            "/"  # 主页
        ]
        
        for file_path in static_files:
            result = await self.make_request("GET", file_path)
            result.name = f"静态文件 - {file_path}"
            self.results.append(result)
            self.print_result(result)
            
            if result.success:
                self.passed_tests += 1
            else:
                self.failed_tests += 1
            self.total_tests += 1
            self.total_time += result.response_time
    
    async def test_error_cases(self):
        """测试错误情况"""
        self.print_header("错误情况测试")
        
        error_tests = [
            {
                "name": "无效接口",
                "method": "GET",
                "endpoint": "/api/invalid_endpoint",
                "expected_status": 404
            },
            {
                "name": "空文本翻译",
                "method": "POST", 
                "endpoint": "/api/translate",
                "data": {"text": "", "from_lang": "zh", "to_lang": "en"},
                "expected_status": 422
            },
            {
                "name": "无效参数",
                "method": "POST",
                "endpoint": "/api/translate", 
                "data": {"invalid": "data"},
                "expected_status": 422
            }
        ]
        
        for test in error_tests:
            result = await self.make_request(test["method"], test["endpoint"], test.get("data"))
            result.name = f"错误测试 - {test['name']}"
            
            # 对于错误测试，期望的状态码不是200
            expected = test.get("expected_status", 400)
            result.success = result.status_code == expected
            
            self.results.append(result)
            self.print_result(result)
            
            if result.success:
                self.passed_tests += 1
            else:
                self.failed_tests += 1
            self.total_tests += 1
            self.total_time += result.response_time
    
    async def run_performance_test(self):
        """运行性能测试"""
        self.print_header("性能压力测试")
        
        print("🚀 并发翻译测试 (10个并发请求)...")
        
        # 创建10个并发翻译请求
        tasks = []
        for i in range(10):
            data = {"text": f"测试文本{i+1}", "from_lang": "zh", "to_lang": "en"}
            task = self.make_request("POST", "/api/translate", data)
            tasks.append(task)
        
        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()
        
        successful = sum(1 for r in results if isinstance(r, TestResult) and r.success)
        total_time = end_time - start_time
        
        print(f"✅ 并发测试完成: {successful}/10 成功, 总耗时: {total_time:.3f}s")
        print(f"📊 平均响应时间: {total_time/10:.3f}s")
        print(f"🔥 QPS: {10/total_time:.2f}")
        
        # 更新统计
        for result in results:
            if isinstance(result, TestResult):
                if result.success:
                    self.passed_tests += 1
                else:
                    self.failed_tests += 1
                self.total_tests += 1
    
    def print_summary(self):
        """打印测试总结"""
        self.print_header("测试总结")
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        avg_response_time = (self.total_time / self.total_tests) if self.total_tests > 0 else 0
        
        print(f"📊 测试统计:")
        print(f"   总测试数: {self.total_tests}")
        print(f"   ✅ 通过: {self.passed_tests}")
        print(f"   ❌ 失败: {self.failed_tests}")
        print(f"   📈 成功率: {success_rate:.1f}%")
        print(f"   ⏱️  平均响应时间: {avg_response_time:.3f}s")
        print(f"   🕐 总耗时: {self.total_time:.3f}s")
        
        # 失败的测试
        failed_tests = [r for r in self.results if not r.success]
        if failed_tests:
            print(f"\n❌ 失败的测试:")
            for test in failed_tests:
                print(f"   - {test.name}: {test.error_message or f'HTTP {test.status_code}'}")
        
        # 最慢的测试
        slowest_tests = sorted(self.results, key=lambda x: x.response_time, reverse=True)[:5]
        print(f"\n🐌 最慢的5个测试:")
        for test in slowest_tests:
            print(f"   - {test.name}: {test.response_time:.3f}s")
        
        # 最快的测试
        fastest_tests = sorted([r for r in self.results if r.success], key=lambda x: x.response_time)[:5]
        if fastest_tests:
            print(f"\n🚀 最快的5个测试:")
            for test in fastest_tests:
                print(f"   - {test.name}: {test.response_time:.3f}s")
        
        print(f"\n{'='*60}")
        if success_rate >= 90:
            print("🎉 测试结果: 优秀! API服务运行正常")
        elif success_rate >= 70:
            print("⚠️  测试结果: 良好, 但有部分问题需要关注")
        else:
            print("❌ 测试结果: 需要修复, 发现多个问题")
        
        return success_rate >= 70
    
    async def run_all_tests(self):
        """运行所有测试"""
        print(f"🧪 开始测试翻译API服务")
        print(f"🌐 测试地址: {self.base_url}")
        print(f"🕐 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            await self.test_basic_endpoints()
            await self.test_translation_endpoints()
            await self.test_single_target_endpoints()
            await self.test_batch_endpoints()
            await self.test_system_endpoints()
            await self.test_static_files()
            await self.test_error_cases()
            await self.run_performance_test()
            
        except KeyboardInterrupt:
            print("\n⚠️ 测试被用户中断")
        except Exception as e:
            print(f"\n❌ 测试过程中发生错误: {e}")
        
        return self.print_summary()


async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="翻译API全接口测试")
    parser.add_argument("--url", default="http://localhost:9000", help="API服务地址")
    parser.add_argument("--timeout", type=int, default=30, help="请求超时时间(秒)")
    args = parser.parse_args()
    
    async with APITester(args.url) as tester:
        success = await tester.run_all_tests()
        return 0 if success else 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n👋 测试已取消")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 程序异常: {e}")
        sys.exit(1)
