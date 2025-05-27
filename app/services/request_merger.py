"""
请求合并服务
重构自原有的request_merger.py，保持所有功能
"""

import asyncio
import hashlib
import time
from typing import Dict, List, Any, Optional, Callable, Tuple
from dataclasses import dataclass
from collections import defaultdict

from app.core.config import Settings


@dataclass
class PendingRequest:
    """待处理的请求"""
    text: str
    from_lang: str
    to_lang: str
    font_size: Optional[str]
    future: asyncio.Future
    timestamp: float
    request_id: str


class RequestMerger:
    """API请求合并器，防止短时间内重复请求"""

    def __init__(self, settings: Settings, translator_service):
        """
        初始化请求合并器

        Args:
            settings: 应用配置
            translator_service: 翻译服务
        """
        self.settings = settings
        self.translator_service = translator_service
        self.merge_window = settings.merge_window
        self.max_batch_size = settings.max_batch_size

        # 待处理的请求队列，按请求键分组
        self.pending_requests: Dict[str, List[PendingRequest]] = defaultdict(list)

        # 正在处理的请求，防止重复处理
        self.processing_requests: Dict[str, asyncio.Future] = {}

        # 统计信息
        self.stats = {
            "total_requests": 0,
            "merged_requests": 0,
            "batch_requests": 0,
            "cache_hits": 0,
            "processing_time": 0.0
        }

        # 请求结果缓存（短期缓存，防止极短时间内的重复请求）
        self.result_cache: Dict[str, Tuple[Any, float]] = {}
        self.cache_ttl = 5.0  # 缓存5秒

        # 后台任务
        self._cleanup_task = None
        self._initialized = False

    def _start_cleanup_task(self):
        """启动清理任务"""
        try:
            if self._cleanup_task is None or self._cleanup_task.done():
                self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        except RuntimeError:
            # 没有运行的事件循环，稍后再启动
            pass

    async def _cleanup_loop(self):
        """定期清理过期的缓存和请求"""
        while True:
            try:
                await asyncio.sleep(10)  # 每10秒清理一次
                current_time = time.time()

                # 清理过期的结果缓存
                expired_keys = []
                for key, (result, timestamp) in self.result_cache.items():
                    if current_time - timestamp > self.cache_ttl:
                        expired_keys.append(key)

                for key in expired_keys:
                    self.result_cache.pop(key, None)

                # 清理超时的待处理请求
                for request_key, requests in list(self.pending_requests.items()):
                    expired_requests = []
                    for req in requests:
                        if current_time - req.timestamp > self.merge_window * 10:  # 超时10倍合并窗口
                            expired_requests.append(req)

                    for req in expired_requests:
                        requests.remove(req)
                        if not req.future.done():
                            req.future.set_exception(TimeoutError("请求超时"))

                    if not requests:
                        self.pending_requests.pop(request_key, None)

            except Exception as e:
                print(f"清理任务异常: {e}")

    def _generate_request_key(self, text: str, from_lang: str, to_lang: str) -> str:
        """生成请求键"""
        content = f"{text}:{from_lang}:{to_lang}"
        return hashlib.md5(content.encode()).hexdigest()

    def _check_result_cache(self, request_key: str) -> Optional[Any]:
        """检查结果缓存"""
        if request_key in self.result_cache:
            result, timestamp = self.result_cache[request_key]
            if time.time() - timestamp <= self.cache_ttl:
                self.stats["cache_hits"] += 1
                return result
            else:
                # 过期，删除
                self.result_cache.pop(request_key, None)
        return None

    def _cache_result(self, request_key: str, result: Any):
        """缓存结果"""
        self.result_cache[request_key] = (result, time.time())

    async def initialize(self):
        """初始化请求合并器（在有事件循环时调用）"""
        if not self._initialized:
            self._start_cleanup_task()
            self._initialized = True

    async def submit_request(self,
                           text: str,
                           from_lang: str,
                           to_lang: str,
                           font_size: Optional[str] = None) -> Any:
        """
        提交翻译请求，自动处理合并

        Args:
            text: 要翻译的文本
            from_lang: 源语言
            to_lang: 目标语言
            font_size: 字体大小

        Returns:
            翻译结果
        """
        # 确保已初始化
        if not self._initialized:
            await self.initialize()

        self.stats["total_requests"] += 1

        # 生成请求键
        request_key = self._generate_request_key(text, from_lang, to_lang)

        # 检查结果缓存
        cached_result = self._check_result_cache(request_key)
        if cached_result is not None:
            # 添加字体大小（如果需要）
            if font_size and isinstance(cached_result, dict):
                cached_result = cached_result.copy()
                cached_result['font_size'] = font_size
            return cached_result

        # 检查是否已有相同请求正在处理
        if request_key in self.processing_requests:
            try:
                result = await self.processing_requests[request_key]
                self.stats["merged_requests"] += 1
                # 添加字体大小（如果需要）
                if font_size and isinstance(result, dict):
                    result = result.copy()
                    result['font_size'] = font_size
                return result
            except Exception as e:
                # 如果正在处理的请求失败，继续创建新请求
                self.processing_requests.pop(request_key, None)

        # 创建新的待处理请求
        future = asyncio.Future()
        request = PendingRequest(
            text=text,
            from_lang=from_lang,
            to_lang=to_lang,
            font_size=font_size,
            future=future,
            timestamp=time.time(),
            request_id=f"{request_key}_{time.time()}"
        )

        # 添加到待处理队列
        self.pending_requests[request_key].append(request)

        # 如果是第一个请求，启动处理任务
        if len(self.pending_requests[request_key]) == 1:
            asyncio.create_task(self._process_request_group(request_key))

        # 等待结果
        return await future

    async def _process_request_group(self, request_key: str):
        """处理请求组"""
        # 等待合并窗口
        await asyncio.sleep(self.merge_window)

        # 获取所有待处理的请求
        requests = self.pending_requests.pop(request_key, [])
        if not requests:
            return

        # 标记为正在处理
        processing_future = asyncio.Future()
        self.processing_requests[request_key] = processing_future

        try:
            start_time = time.time()

            # 取第一个请求作为代表（因为text、from_lang、to_lang都相同）
            representative_request = requests[0]

            # 调用翻译服务
            translation_result = await self.translator_service.translate_single(
                representative_request.text,
                representative_request.from_lang,
                representative_request.to_lang,
                use_cache=True,
                font_size=None  # 不在这里设置字体大小
            )

            if translation_result.success:
                result = translation_result.data
            else:
                raise Exception(translation_result.error)

            # 缓存结果
            self._cache_result(request_key, result)

            # 设置处理结果
            processing_future.set_result(result)

            # 为所有请求设置结果
            for request in requests:
                if not request.future.done():
                    # 为每个请求添加特定的字体大小
                    request_result = result
                    if request.font_size and isinstance(result, dict):
                        request_result = result.copy()
                        request_result['font_size'] = request.font_size

                    request.future.set_result(request_result)

            # 更新统计
            if len(requests) > 1:
                self.stats["merged_requests"] += len(requests) - 1

            processing_time = time.time() - start_time
            self.stats["processing_time"] += processing_time

        except Exception as e:
            # 处理失败，为所有请求设置异常
            processing_future.set_exception(e)
            for request in requests:
                if not request.future.done():
                    request.future.set_exception(e)
        finally:
            # 清理处理状态
            self.processing_requests.pop(request_key, None)

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        stats = self.stats.copy()
        stats.update({
            "pending_request_groups": len(self.pending_requests),
            "processing_requests": len(self.processing_requests),
            "cached_results": len(self.result_cache),
            "merge_efficiency": (
                self.stats["merged_requests"] / max(self.stats["total_requests"], 1) * 100
            )
        })
        return stats

    async def close(self):
        """关闭请求合并器"""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
