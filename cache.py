import json
import zlib
import pickle
import hashlib
import time
from typing import Any, Dict, List, Optional, Tuple, Union
import redis
from redis import asyncio as redis_asyncio
from config import config

class CacheManager:
    """Redis缓存管理器，支持压缩存储和批量操作"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CacheManager, cls).__new__(cls)
            cls._instance._init_clients()
        return cls._instance
    
    def _init_clients(self):
        """初始化Redis客户端"""
        # 同步客户端（主要用于健康检查）
        self.redis_pool = redis.ConnectionPool(
            host=config.get('redis', 'host'),
            port=config.get('redis', 'port'),
            db=config.get('redis', 'db'),
            password=config.get('redis', 'password'),
            decode_responses=True,
            socket_timeout=config.get('redis', 'socket_timeout', 1.0),
            socket_connect_timeout=1.0,  # 增加连接超时
            retry_on_timeout=True,      # 启用超时重试
            max_connections=config.get('redis', 'max_connections')
        )
        self.sync_client = redis.Redis(connection_pool=self.redis_pool)
        
        # 异步客户端（主要用于API请求处理）
        self.async_client = None
        
        # 统计计数器
        self.stats = {
            "hits": 0,
            "misses": 0,
            "compressed_keys": 0
        }
    
    async def init_async_client(self):
        """初始化异步Redis客户端（在应用启动时调用）"""
        if self.async_client is not None:
            return
            
        redis_url = f"redis://{config.get('redis', 'host')}:{config.get('redis', 'port')}/{config.get('redis', 'db')}"
        if config.get('redis', 'password'):
            redis_url = f"redis://:{config.get('redis', 'password')}@{config.get('redis', 'host')}:{config.get('redis', 'port')}/{config.get('redis', 'db')}"
            
        try:
            self.async_client = redis_asyncio.from_url(
                redis_url,
                decode_responses=True,
                socket_timeout=config.get('redis', 'socket_timeout', 1.0),
                socket_connect_timeout=1.0,  # 增加连接超时
                retry_on_timeout=True      # 启用超时重试
            )
            # 测试连接
            await self.async_client.ping()
            print("异步Redis客户端初始化成功")
        except Exception as e:
            print(f"异步Redis客户端初始化失败: {e}")
            print("缓存功能将被禁用")
            self.async_client = None
    
    async def close(self):
        """关闭Redis连接"""
        if self.async_client:
            await self.async_client.close()
    
    def _should_compress(self, value: str) -> bool:
        """判断是否应该压缩内容"""
        if not config.get('redis', 'use_compression'):
            return False
            
        min_size = config.get('redis', 'compression_min_size')
        return len(value) > min_size
    
    def _compress(self, value: Any) -> bytes:
        """压缩数据"""
        serialized = pickle.dumps(value)
        return zlib.compress(
            serialized, 
            level=config.get('redis', 'compression_level')
        )
    
    async def _decompress(self, compressed_data: bytes) -> Any:
        """解压数据"""
        try:
            decompressed = zlib.decompress(compressed_data)
            return pickle.loads(decompressed)
        except Exception as e:
            print(f"解压缓存数据失败: {e}")
            return None
    
    async def get(self, key: str) -> Any:
        """获取缓存数据，自动处理压缩"""
        if self.async_client is None:
            # Redis不可用时直接返回None
            self.stats["misses"] += 1
            return None
            
        try:  
            # 首先检查常规未压缩版本
            data = await self.async_client.get(key)
            if data is not None:
                self.stats["hits"] += 1
                try:
                    return json.loads(data)
                except json.JSONDecodeError:
                    return data
            
            # 检查是否有压缩版本（使用二进制客户端）
            # 为所有压缩数据操作使用二进制客户端
            redis_url = f"redis://{config.get('redis', 'host')}:{config.get('redis', 'port')}/{config.get('redis', 'db')}"
            if config.get('redis', 'password'):
                redis_url = f"redis://:{config.get('redis', 'password')}@{config.get('redis', 'host')}:{config.get('redis', 'port')}/{config.get('redis', 'db')}"
            
            binary_client = redis_asyncio.from_url(
                redis_url,
                decode_responses=False,
                socket_timeout=1.0,
                socket_connect_timeout=1.0,
                retry_on_timeout=True
            )
            
            compressed_key = f"comp:{key}"
            try:
                raw_data = await binary_client.get(compressed_key)
                await binary_client.close()
                
                if raw_data:
                    self.stats["hits"] += 1
                    return await self._decompress(raw_data)
            except Exception as e:
                print(f"获取压缩数据失败: {e}")
                await binary_client.close()
            
            # 缓存未命中
            self.stats["misses"] += 1
            return None
        except redis.exceptions.TimeoutError as e:
            print(f"Redis连接超时: {e}")
            self.stats["misses"] += 1
            return None
        except Exception as e:
            print(f"获取缓存数据异常: {e}")
            self.stats["misses"] += 1
            return None
    
    async def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """设置缓存数据，自动处理压缩"""
        if self.async_client is None:
            return False  # 如果Redis不可用，直接返回失败
            
        if ttl is None:
            ttl = config.get('redis', 'ttl')
            
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
                
                # 不能使用decode_responses的客户端设置二进制数据
                # 手动构建Redis URL而不是从连接池获取
                redis_url = f"redis://{config.get('redis', 'host')}:{config.get('redis', 'port')}/{config.get('redis', 'db')}"
                if config.get('redis', 'password'):
                    redis_url = f"redis://:{config.get('redis', 'password')}@{config.get('redis', 'host')}:{config.get('redis', 'port')}/{config.get('redis', 'db')}"
                
                binary_client = redis_asyncio.from_url(
                    redis_url,
                    decode_responses=False,
                    socket_timeout=1.0,
                    socket_connect_timeout=1.0,
                    retry_on_timeout=True
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
        except redis.exceptions.TimeoutError as e:
            print(f"设置缓存时Redis连接超时: {e}")
            return False
        except Exception as e:
            print(f"设置缓存失败: {e}")
            return False
    
    async def batch_get(self, keys: List[str]) -> Dict[str, Any]:
        """批量获取缓存，处理压缩"""
        if self.async_client is None or not keys:
            # Redis不可用或者键列表为空时返回空字典
            self.stats["misses"] += len(keys) if keys else 0
            return {}
            
        results = {}
        
        try:
            # 首先检查常规未压缩键
            pipeline = self.async_client.pipeline()
            for key in keys:
                pipeline.get(key)
            
            values = await pipeline.execute()
            
            # 检查那些未命中的键，看是否有压缩版本
            regular_hit_keys = []
            compressed_keys = []
            
            for i, (key, value) in enumerate(zip(keys, values)):
                if value is not None:
                    # 常规缓存命中
                    try:
                        results[key] = json.loads(value)
                    except json.JSONDecodeError:
                        results[key] = value
                    regular_hit_keys.append(key)
                else:
                    # 检查是否有压缩版本
                    compressed_keys.append(f"comp:{key}")
            
            # 如果有需要检查的压缩键
            if compressed_keys:
                try:
                    # 创建二进制客户端检查压缩数据
                    # 手动构建Redis URL而不是从连接池获取
                    redis_url = f"redis://{config.get('redis', 'host')}:{config.get('redis', 'port')}/{config.get('redis', 'db')}"
                    if config.get('redis', 'password'):
                        redis_url = f"redis://:{config.get('redis', 'password')}@{config.get('redis', 'host')}:{config.get('redis', 'port')}/{config.get('redis', 'db')}"
                    
                    binary_client = redis_asyncio.from_url(
                        redis_url,
                        decode_responses=False,
                        socket_timeout=1.0,
                        socket_connect_timeout=1.0,
                        retry_on_timeout=True
                    )
                    
                    pipeline = binary_client.pipeline()
                    for comp_key in compressed_keys:
                        pipeline.get(comp_key)
                    
                    comp_values = await pipeline.execute()
                    await binary_client.close()
                    
                    # 处理压缩数据结果
                    for i, (comp_key, comp_value) in enumerate(zip(compressed_keys, comp_values)):
                        if comp_value is not None:
                            # 解压数据
                            original_key = comp_key[5:]  # 去掉"comp:"前缀
                            decompressed = await self._decompress(comp_value)
                            if decompressed is not None:
                                results[original_key] = decompressed
                except Exception as e:
                    print(f"获取压缩数据失败: {e}")
                    # 继续处理，不因为压缩数据问题影响整个批量读取
            
            # 更新命中统计
            hits = len(results)
            misses = len(keys) - hits
            self.stats["hits"] += hits
            self.stats["misses"] += misses
            
            return results
        except redis.exceptions.TimeoutError as e:
            print(f"批量获取缓存时Redis连接超时: {e}")
            self.stats["misses"] += len(keys)
            return {}
        except Exception as e:
            print(f"批量获取缓存异常: {e}")
            self.stats["misses"] += len(keys)
            return {}
    
    async def batch_set(self, key_value_dict: Dict[str, Any], ttl: int = None) -> bool:
        """批量设置缓存，处理压缩"""
        if self.async_client is None:
            return False  # 如果Redis不可用，直接返回失败
            
        if not key_value_dict:
            return True
            
        if ttl is None:
            ttl = config.get('redis', 'ttl')
            
        success_count = 0
        failure_count = 0
        
        # 分离需要压缩的和不需要压缩的键值对
        regular_items = {}
        compress_items = {}
        
        try:
            # 首先准备常规和压缩数据
            for key, value in key_value_dict.items():
                # 转为字符串
                if not isinstance(value, str):
                    value_str = json.dumps(value)
                else:
                    value_str = value
                    
                # 判断是否需要压缩
                if self._should_compress(value_str):
                    compress_items[key] = value
                else:
                    regular_items[key] = value_str
            
            # 处理常规数据（批量写入）
            if regular_items:
                try:
                    pipeline = self.async_client.pipeline()
                    for key, value_str in regular_items.items():
                        pipeline.setex(key, ttl, value_str)
                    
                    await pipeline.execute()
                    success_count += len(regular_items)
                except Exception as e:
                    print(f"批量设置常规缓存失败: {e}")
                    failure_count += len(regular_items)
            
            # 处理需要压缩的数据（单独处理每个）
            if compress_items:
                # 为压缩数据准备二进制客户端
                redis_url = f"redis://{config.get('redis', 'host')}:{config.get('redis', 'port')}/{config.get('redis', 'db')}"
                if config.get('redis', 'password'):
                    redis_url = f"redis://:{config.get('redis', 'password')}@{config.get('redis', 'host')}:{config.get('redis', 'port')}/{config.get('redis', 'db')}"
                
                binary_client = redis_asyncio.from_url(
                    redis_url,
                    decode_responses=False,
                    socket_timeout=1.0,
                    socket_connect_timeout=1.0,
                    retry_on_timeout=True
                )
                
                for key, value in compress_items.items():
                    compressed_key = f"comp:{key}"
                    compressed_data = self._compress(value)
                    
                    try:
                        await binary_client.setex(compressed_key, ttl, compressed_data)
                        success_count += 1
                        self.stats["compressed_keys"] += 1
                    except Exception as e:
                        print(f"设置压缩缓存 {key} 失败: {e}")
                        
                        # 尝试使用常规方式保存
                        try:
                            if not isinstance(value, str):
                                value_str = json.dumps(value)
                            else:
                                value_str = value
                            
                            await self.async_client.setex(key, ttl, value_str)
                            success_count += 1
                        except Exception:
                            failure_count += 1
                
                await binary_client.close()
            
            return failure_count == 0
        except redis.exceptions.TimeoutError as e:
            print(f"批量设置缓存时Redis连接超时: {e}")
            return False
        except Exception as e:
            print(f"批量设置缓存异常: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """删除缓存"""
        if self.async_client is None:
            await self.init_async_client()
            
        # 删除两种版本
        pipeline = self.async_client.pipeline()
        pipeline.delete(key)
        pipeline.delete(f"comp:{key}")
        await pipeline.execute()
        return True
    
    async def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        if self.async_client is None:
            await self.init_async_client()
            
        # 从Redis获取命中计数
        pipeline = self.async_client.pipeline()
        pipeline.get("stats:cache_hits")
        pipeline.get("stats:cache_misses")
        
        redis_stats = await pipeline.execute()
        redis_hits = int(redis_stats[0] or 0)
        redis_misses = int(redis_stats[1] or 0)
        
        # 计算命中率
        total = redis_hits + redis_misses
        hit_rate = (redis_hits / total * 100) if total > 0 else 0
        
        # 测量Redis响应时间
        start = time.time()
        await self.async_client.ping()
        latency = (time.time() - start) * 1000  # 毫秒
        
        return {
            "status": "connected",
            "latency_ms": round(latency, 2),
            "hits": redis_hits + self.stats["hits"],
            "misses": redis_misses + self.stats["misses"],
            "hit_rate": round(hit_rate, 2),
            "compressed_keys": self.stats["compressed_keys"]
        }
        
    def generate_cache_key(self, from_lang: str, to_lang: str, text: str) -> str:
        """生成翻译缓存键"""
        text_hash = hashlib.md5(text.encode()).hexdigest()
        return f"trans:{from_lang}:{to_lang}:{text_hash}"

# 导出单例实例以便其他模块使用
cache_manager = CacheManager() 