"""
缓存服务
重构自原有的cache.py，保持所有功能
"""

import json
import zlib
import pickle
import time
import asyncio
from typing import Any, Dict, List, Optional
import redis
from redis import asyncio as redis_asyncio

from app.core.config import Settings


class CacheService:
    """Redis缓存服务，支持压缩存储、批量操作和多级缓存"""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.async_client: Optional[redis_asyncio.Redis] = None
        self.sync_client: Optional[redis.Redis] = None

        # 内存缓存（一级缓存）
        self.memory_cache = {}
        self.memory_cache_ttl = {}
        self.memory_cache_max_size = settings.memory_cache_size
        self.memory_cache_default_ttl = settings.memory_cache_ttl

        # Redis连接配置
        self.socket_timeout = settings.redis_socket_timeout
        self.connect_timeout = settings.redis_connect_timeout
        self.use_compression = settings.redis_use_compression
        self.compression_min_size = settings.redis_compression_min_size
        self.compression_level = settings.redis_compression_level

        # 统计计数器
        self.stats = {
            "hits": 0,
            "misses": 0,
            "compressed_keys": 0,
            "memory_hits": 0,
            "redis_hits": 0,
            "connection_errors": 0,
            "cache_evictions": 0
        }

        # 连接池统计
        self.pool_stats = {
            "created_connections": 0,
            "available_connections": 0,
            "in_use_connections": 0
        }

    async def initialize(self):
        """初始化异步Redis客户端"""
        if self.async_client is not None:
            return

        try:
            self.async_client = redis_asyncio.from_url(
                self.settings.redis_url,
                decode_responses=True,
                socket_timeout=self.socket_timeout,
                socket_connect_timeout=self.connect_timeout,
                retry_on_timeout=True,
                health_check_interval=60,
                max_connections=self.settings.redis_max_connections
            )

            # 测试连接
            await self.async_client.ping()
            print("Redis异步客户端初始化成功")

        except Exception as e:
            # Redis连接失败，静默处理，使用内存缓存
            self.async_client = None

    async def close(self):
        """关闭Redis连接"""
        if self.async_client:
            await self.async_client.close()

    def _clean_memory_cache(self):
        """清理过期的内存缓存"""
        current_time = time.time()
        expired_keys = []

        for key, expire_time in self.memory_cache_ttl.items():
            if current_time > expire_time:
                expired_keys.append(key)

        for key in expired_keys:
            self.memory_cache.pop(key, None)
            self.memory_cache_ttl.pop(key, None)
            self.stats["cache_evictions"] += 1

    def _evict_memory_cache(self):
        """当内存缓存达到最大容量时，移除最旧的条目"""
        if len(self.memory_cache) >= self.memory_cache_max_size:
            oldest_key = min(self.memory_cache_ttl.keys(),
                           key=lambda k: self.memory_cache_ttl[k])
            self.memory_cache.pop(oldest_key, None)
            self.memory_cache_ttl.pop(oldest_key, None)
            self.stats["cache_evictions"] += 1

    def _set_memory_cache(self, key: str, value: Any, ttl: int = None):
        """设置内存缓存"""
        if ttl is None:
            ttl = self.memory_cache_default_ttl

        self._clean_memory_cache()
        self._evict_memory_cache()

        expire_time = time.time() + ttl
        self.memory_cache[key] = value
        self.memory_cache_ttl[key] = expire_time

    def _get_memory_cache(self, key: str) -> Optional[Any]:
        """获取内存缓存"""
        current_time = time.time()

        if key in self.memory_cache:
            if current_time <= self.memory_cache_ttl.get(key, 0):
                self.stats["memory_hits"] += 1
                return self.memory_cache[key]
            else:
                # 过期，删除
                self.memory_cache.pop(key, None)
                self.memory_cache_ttl.pop(key, None)
                self.stats["cache_evictions"] += 1

        return None

    def _should_compress(self, value: str) -> bool:
        """判断是否应该压缩内容"""
        return self.use_compression and len(value) > self.compression_min_size

    def _compress(self, value: Any) -> bytes:
        """压缩数据"""
        serialized = pickle.dumps(value)
        return zlib.compress(serialized, level=self.compression_level)

    async def _decompress(self, compressed_data: bytes) -> Any:
        """解压数据"""
        try:
            decompressed = zlib.decompress(compressed_data)
            return pickle.loads(decompressed)
        except Exception as e:
            print(f"解压缓存数据失败: {e}")
            return None

    async def get(self, key: str) -> Any:
        """获取缓存数据，支持多级缓存（内存+Redis）"""
        # 1. 首先检查内存缓存
        memory_result = self._get_memory_cache(key)
        if memory_result is not None:
            self.stats["hits"] += 1
            return memory_result

        # 2. 检查Redis缓存
        if self.async_client is None:
            self.stats["misses"] += 1
            return None

        try:
            # 检查常规未压缩版本
            data = await self.async_client.get(key)
            if data is not None:
                self.stats["hits"] += 1
                self.stats["redis_hits"] += 1
                try:
                    result = json.loads(data)
                    self._set_memory_cache(key, result)
                    return result
                except json.JSONDecodeError:
                    self._set_memory_cache(key, data)
                    return data

            # 检查压缩版本
            binary_client = redis_asyncio.from_url(
                self.settings.redis_url,
                decode_responses=False,
                socket_timeout=5.0,
                socket_connect_timeout=5.0,
                retry_on_timeout=True,
                max_connections=50
            )

            compressed_key = f"comp:{key}"
            try:
                raw_data = await binary_client.get(compressed_key)
                await binary_client.close()

                if raw_data:
                    self.stats["hits"] += 1
                    self.stats["redis_hits"] += 1
                    result = await self._decompress(raw_data)
                    self._set_memory_cache(key, result)
                    return result
            except Exception as e:
                print(f"获取压缩数据失败: {e}")
                await binary_client.close()

            # 缓存未命中
            self.stats["misses"] += 1
            return None

        except (redis.exceptions.TimeoutError, redis.exceptions.ConnectionError) as e:
            self.stats["connection_errors"] += 1
            self.stats["misses"] += 1
            return None
        except Exception as e:
            self.stats["misses"] += 1
            return None

    async def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """设置缓存数据，支持多级缓存（内存+Redis）"""
        if ttl is None:
            ttl = self.settings.cache_ttl

        # 1. 设置内存缓存
        self._set_memory_cache(key, value, min(ttl, 300))

        # 2. 设置Redis缓存
        if self.async_client is None:
            return True

        try:
            # 转换为JSON字符串
            if not isinstance(value, str):
                value_str = json.dumps(value)
            else:
                value_str = value

            # 判断是否应该压缩
            if self._should_compress(value_str):
                # 保存压缩版本
                compressed_key = f"comp:{key}"
                compressed_data = self._compress(value)

                binary_client = redis_asyncio.from_url(
                    self.settings.redis_url,
                    decode_responses=False,
                    socket_timeout=5.0,
                    socket_connect_timeout=5.0,
                    retry_on_timeout=True,
                    max_connections=50
                )

                try:
                    await binary_client.setex(compressed_key, ttl, compressed_data)
                    await binary_client.close()
                    self.stats["compressed_keys"] += 1
                    return True
                except Exception as e:
                    print(f"设置压缩缓存失败: {e}")
                    await binary_client.close()
                    # 压缩失败后，尝试使用普通方式保存
                    await self.async_client.setex(key, ttl, value_str)
                    return True
            else:
                # 保存普通版本
                await self.async_client.setex(key, ttl, value_str)
                return True

        except (redis.exceptions.TimeoutError, redis.exceptions.ConnectionError) as e:
            self.stats["connection_errors"] += 1
            return True  # 内存缓存已设置，返回成功
        except Exception as e:
            return True  # 内存缓存已设置，返回成功

    async def batch_get(self, keys: List[str]) -> Dict[str, Any]:
        """批量获取缓存数据"""
        results = {}
        for key in keys:
            value = await self.get(key)
            if value is not None:
                results[key] = value
        return results

    async def batch_set(self, items: Dict[str, Any], ttl: int = None) -> bool:
        """批量设置缓存数据"""
        success = True
        for key, value in items.items():
            result = await self.set(key, value, ttl)
            if not result:
                success = False
        return success

    async def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        try:
            if self.async_client:
                pipeline = self.async_client.pipeline()
                await pipeline.execute()
        except Exception:
            pass

        return {
            "cache_stats": self.stats.copy(),
            "memory_cache_size": len(self.memory_cache),
            "memory_cache_max_size": self.memory_cache_max_size,
            "pool_stats": self.pool_stats.copy()
        }
