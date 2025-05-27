"""
翻译服务
重构自原有的translator.py，保持所有功能
"""

import hashlib
import random
import json
import asyncio
import time
from typing import Dict, List, Any, Optional
import aiohttp

from app.core.config import Settings
from app.services.cache_service import CacheService


class TranslationResult:
    """翻译结果模型"""

    def __init__(self, success: bool, data: Any = None, error: str = None, id: str = None, index: int = None):
        self.success = success
        self.data = data
        self.error = error
        self.id = id
        self.index = index

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {"success": self.success}
        if self.data is not None:
            result.update(self.data)
        if self.error:
            result["error"] = self.error
        if self.id:
            result["id"] = self.id
        if self.index is not None:
            result["index"] = self.index
        return result


class TranslationService:
    """翻译服务，封装百度翻译API调用"""

    def __init__(self, settings: Settings, cache_service: CacheService):
        self.settings = settings
        self.cache_service = cache_service
        self.app_id = settings.baidu_app_id
        self.secret_key = settings.baidu_secret_key
        self.base_url = "https://fanyi-api.baidu.com/api/trans/vip/translate"
        self.timeout = settings.baidu_api_timeout
        self.semaphore = None  # 用于控制并发请求数量的信号量

    def _init_semaphore(self, max_concurrent: int = None):
        """初始化并发控制信号量"""
        if max_concurrent is None:
            max_concurrent = self.settings.max_concurrent_requests
        self.semaphore = asyncio.Semaphore(max_concurrent)

    def _get_sign(self, text: str, salt: str) -> str:
        """生成百度API签名"""
        sign = self.app_id + text + salt + self.secret_key
        return hashlib.md5(sign.encode()).hexdigest()

    def _generate_cache_key(self, from_lang: str, to_lang: str, text: str) -> str:
        """生成缓存键"""
        key_string = f"{from_lang}:{to_lang}:{text}"
        return f"trans:{hashlib.md5(key_string.encode()).hexdigest()}"

    async def translate_single(self, text: str, from_lang: str = "auto", to_lang: str = "zh",
                              use_cache: bool = True, font_size: str = None) -> TranslationResult:
        """翻译单个文本"""
        if not text.strip():
            return TranslationResult(False, error="文本不能为空")

        # 检查缓存
        if use_cache:
            cache_key = self._generate_cache_key(from_lang, to_lang, text)
            cached_result = await self.cache_service.get(cache_key)
            if cached_result:
                result = cached_result
                if font_size:
                    result['font_size'] = font_size
                return TranslationResult(True, data=result)

        # 创建并发控制信号量（如果尚未创建）
        if self.semaphore is None:
            self._init_semaphore()

        # 使用信号量控制并发
        async with self.semaphore:
            # 构建请求参数
            salt = str(random.randint(32768, 65536))
            sign = self._get_sign(text, salt)

            payload = {
                'appid': self.app_id,
                'q': text,
                'from': from_lang,
                'to': to_lang,
                'salt': salt,
                'sign': sign
            }

            # 发送请求
            try:
                headers = {'Content-Type': 'application/x-www-form-urlencoded'}

                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        self.base_url,
                        params=payload,
                        headers=headers,
                        timeout=self.timeout
                    ) as response:

                        if response.status != 200:
                            return TranslationResult(
                                False,
                                error=f"百度API请求失败，状态码: {response.status}"
                            )

                        result = await response.json()

                        if 'error_code' in result:
                            return TranslationResult(
                                False,
                                error=f"百度API错误: {result.get('error_msg', '未知错误')}"
                            )

                        # 添加字体大小（如果有）
                        if font_size:
                            result['font_size'] = font_size

                        # 缓存结果
                        if use_cache:
                            # 缓存时移除字体大小
                            cache_result = result.copy()
                            if 'font_size' in cache_result:
                                del cache_result['font_size']

                            await self.cache_service.set(cache_key, cache_result)

                        return TranslationResult(True, data=result)

            except asyncio.TimeoutError:
                return TranslationResult(False, error="翻译请求超时")
            except Exception as e:
                return TranslationResult(False, error=f"翻译请求异常: {str(e)}")

    async def translate_batch(self, items: List[Dict[str, Any]], from_lang: str = "auto",
                             to_lang: str = "zh", use_cache: bool = True, font_size: str = None,
                             max_concurrent: int = None) -> Dict[str, Any]:
        """批量翻译多个文本，支持并发控制"""
        if not items:
            return {"results": [], "total": 0, "success": 0, "failed": 0}

        # 设置并发控制
        if max_concurrent is not None or self.semaphore is None:
            self._init_semaphore(max_concurrent)

        results = []
        errors = []
        cache_hits = []

        # 首先检查所有缓存
        if use_cache:
            cache_keys = {}
            for i, item in enumerate(items):
                text = item.get("text", "")
                if not text.strip():
                    item_id = item.get("id", str(i))
                    errors.append({
                        "index": i,
                        "id": item_id,
                        "error": "文本不能为空"
                    })
                    continue

                # 生成缓存键并记录索引和ID
                cache_key = self._generate_cache_key(from_lang, to_lang, text)
                cache_keys[cache_key] = (i, item)

            # 批量查询缓存
            if cache_keys:
                cached_results = await self.cache_service.batch_get(list(cache_keys.keys()))

                # 处理缓存命中结果
                for cache_key, cached_result in cached_results.items():
                    if cached_result:
                        try:
                            i, item = cache_keys[cache_key]
                            result = cached_result

                            # 添加ID和索引
                            if "id" in item:
                                result["id"] = item["id"]
                            result["index"] = i

                            # 添加字体大小（如果有）
                            if font_size:
                                result["font_size"] = font_size

                            results.append(result)
                            cache_hits.append(cache_key)
                        except Exception as e:
                            # 缓存解析错误，忽略并继续
                            pass

        # 处理未缓存的项
        uncached_items = []

        for i, item in enumerate(items):
            text = item.get("text", "")
            if not text.strip():
                continue  # 已处理空文本错误

            cache_key = self._generate_cache_key(from_lang, to_lang, text)

            # 如果已从缓存获取，则跳过
            if cache_key in cache_hits:
                continue

            # 创建异步任务
            uncached_items.append((i, item, cache_key))

        # 并行处理所有未缓存项
        cache_updates = {}

        for i, item, cache_key in uncached_items:
            try:
                # 使用信号量控制并发（在translate_single中处理）
                result = await self.translate_single(
                    item["text"],
                    from_lang,
                    to_lang,
                    False,  # 不使用缓存，因为已经检查过了
                    font_size
                )

                if result.success:
                    # 添加ID和索引
                    data = result.data
                    if "id" in item:
                        data["id"] = item["id"]
                    data["index"] = i

                    # 保存到结果列表
                    results.append(data)

                    # 准备缓存更新
                    cache_data = data.copy()
                    if "font_size" in cache_data:
                        del cache_data["font_size"]
                    if "id" in cache_data:
                        del cache_data["id"]
                    if "index" in cache_data:
                        del cache_data["index"]

                    cache_updates[cache_key] = cache_data
                else:
                    # 处理错误
                    errors.append({
                        "index": i,
                        "id": item.get("id", str(i)),
                        "error": result.error
                    })
            except Exception as e:
                # 处理异常
                errors.append({
                    "index": i,
                    "id": item.get("id", str(i)),
                    "error": str(e)
                })

        # 批量更新缓存
        if cache_updates and use_cache:
            await self.cache_service.batch_set(cache_updates)

        # 构建响应
        response = {
            "results": results,
            "total": len(items),
            "success": len(results),
            "failed": len(errors),
            "cache_hits": len(cache_hits)
        }

        if errors:
            response["errors"] = errors

        return response
