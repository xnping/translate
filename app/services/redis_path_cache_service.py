"""
Redis路径缓存服务 - 基于路径MD5哈希
"""

import hashlib
import json
import gzip
from typing import Optional, Dict, Any
import redis.asyncio as redis
from app.config.config import get_settings


class RedisPathCacheService:
    """Redis路径缓存服务类 - 基于路径MD5哈希"""
    
    def __init__(self):
        """初始化Redis路径缓存服务"""
        # 从配置文件读取设置
        self.settings = get_settings()
        
        self.host = self.settings.redis_host
        self.port = self.settings.redis_port
        self.db = self.settings.redis_db
        self.password = self.settings.redis_password
        self.cache_ttl = self.settings.cache_ttl  # Redis TTL (秒)
        self.use_compression = True
        self.compression_min_size = 1024  # 1KB以上启用压缩
        
        # 中文转其他10种语言映射
        self.source_language = "zh"  # 固定源语言为中文
        self.target_languages = {
            "en": "english",      # 英语
            "ms": "malay",        # 马来语
            "km": "khmer",        # 高棉语
            "id": "indonesian",   # 印尼语
            "my": "myanmar",      # 缅甸语
            "fil": "filipino",    # 菲律宾语
            "th": "thai",         # 泰语
            "vi": "vietnamese",   # 越南语
            "ta": "tamil",        # 泰米尔语
            "lo": "lao"           # 老挝语
        }
        
        # Redis连接
        self.redis_client = None
        
        print(f"🔄 Redis路径缓存服务初始化完成")
        print(f"  Redis主机: {self.host}:{self.port}")
        print(f"  数据库: {self.db}")
        print(f"  密码: {'***' if self.password else '无'}")
        print(f"  缓存TTL: {self.cache_ttl}秒 (来自配置)")
        print(f"  压缩: {self.use_compression}")
        print(f"  源语言: 中文 (zh)")
        print(f"  目标语言: {len(self.target_languages)}种")
    
    def normalize_path(self, path: str) -> str:
        """标准化路径"""
        # 移除查询参数和锚点
        if '?' in path:
            path = path.split('?')[0]
        if '#' in path:
            path = path.split('#')[0]
        
        # 标准化斜杠和大小写
        path = path.lower().rstrip('/')
        
        return path
    
    def generate_cache_key(self, path: str, source_lang: str, target_lang: str) -> str:
        """生成基于路径的Redis缓存键"""
        # 验证语言支持
        if source_lang != "zh":
            raise ValueError(f"只支持中文(zh)作为源语言，当前源语言: {source_lang}")
        
        if target_lang not in self.target_languages:
            raise ValueError(f"不支持的目标语言: {target_lang}，支持的语言: {list(self.target_languages.keys())}")
        
        # 标准化路径
        normalized_path = self.normalize_path(path)
        
        # 组合路径和语言对
        content = f"{normalized_path}|{source_lang}|{target_lang}"
        
        # 生成MD5哈希并截取10位 (Redis键名更短)
        path_hash = hashlib.md5(content.encode('utf-8')).hexdigest()[:10]
        
        # Redis键格式: r:路径哈希:语言对
        target_name = self.target_languages[target_lang]
        return f"r:{path_hash}:zh-{target_name[:3]}"  # 例如: r:a1b2c3d4e5:zh-eng
    
    def compress_data(self, data: str) -> bytes:
        """压缩数据"""
        data_bytes = data.encode('utf-8')
        
        if self.use_compression and len(data_bytes) >= self.compression_min_size:
            return gzip.compress(data_bytes)
        
        return data_bytes
    
    def decompress_data(self, data: bytes) -> str:
        """解压数据"""
        if self.use_compression and data.startswith(b'\x1f\x8b'):  # gzip魔数
            return gzip.decompress(data).decode('utf-8')
        
        return data.decode('utf-8')
    
    async def initialize(self) -> bool:
        """初始化Redis连接"""
        try:
            self.redis_client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=False  # 保持二进制数据用于压缩
            )
            
            # 测试连接
            await self.redis_client.ping()
            print(f"✅ Redis路径缓存连接成功")
            return True
            
        except Exception as e:
            print(f"❌ Redis路径缓存连接失败: {str(e)}")
            return False
    
    async def get_cache(self, path: str, source_lang: str, target_lang: str) -> Optional[Dict]:
        """获取Redis缓存"""
        if not self.redis_client:
            return None
        
        try:
            # 1. 生成基于路径的缓存键
            cache_key = self.generate_cache_key(path, source_lang, target_lang)
            
            # 2. 从Redis获取数据
            cached_data = await self.redis_client.get(cache_key)
            
            if cached_data is None:
                print(f"❌ Redis缓存未命中: {cache_key}")
                return None
            
            # 3. 解压和反序列化数据
            decompressed_data = self.decompress_data(cached_data)
            cache_result = json.loads(decompressed_data)
            
            print(f"✅ Redis缓存命中: {cache_key}")
            return cache_result["content"]
            
        except Exception as e:
            print(f"❌ 获取Redis缓存失败: {e}")
            return None
    
    async def set_cache(self, path: str, source_lang: str, target_lang: str, translation_result: Dict) -> bool:
        """设置Redis缓存"""
        if not self.redis_client:
            return False
        
        try:
            # 1. 生成基于路径的缓存键
            cache_key = self.generate_cache_key(path, source_lang, target_lang)
            
            # 2. 准备缓存数据
            cache_data = {
                "metadata": {
                    "cache_key": cache_key,
                    "path": path,
                    "source_lang": source_lang,
                    "target_lang": target_lang,
                    "cache_method": "redis_path_hash_md5",
                    "ttl_seconds": self.cache_ttl
                },
                "content": translation_result
            }
            
            # 3. 序列化和压缩数据
            serialized_data = json.dumps(cache_data, ensure_ascii=False)
            compressed_data = self.compress_data(serialized_data)
            
            # 4. 保存到Redis并设置TTL
            await self.redis_client.set(cache_key, compressed_data, ex=self.cache_ttl)
            
            print(f"💾 Redis缓存已保存: {cache_key} (TTL: {self.cache_ttl}秒)")
            return True
            
        except Exception as e:
            print(f"❌ 保存Redis缓存失败: {e}")
            return False
    
    async def delete_cache(self, path: str, source_lang: str, target_lang: str) -> bool:
        """删除Redis缓存"""
        if not self.redis_client:
            return False
        
        try:
            cache_key = self.generate_cache_key(path, source_lang, target_lang)
            result = await self.redis_client.delete(cache_key)
            
            if result:
                print(f"🗑️ Redis缓存已删除: {cache_key}")
                return True
            else:
                print(f"⚠️ Redis缓存不存在: {cache_key}")
                return False
                
        except Exception as e:
            print(f"❌ 删除Redis缓存失败: {e}")
            return False
    
    async def exists(self, path: str, source_lang: str, target_lang: str) -> bool:
        """检查Redis缓存是否存在"""
        if not self.redis_client:
            return False
        
        try:
            cache_key = self.generate_cache_key(path, source_lang, target_lang)
            result = await self.redis_client.exists(cache_key)
            return bool(result)
            
        except Exception as e:
            print(f"❌ 检查Redis缓存存在性失败: {e}")
            return False
    
    async def get_cache_info(self) -> Dict[str, Any]:
        """获取Redis缓存统计信息"""
        if not self.redis_client:
            return {"status": "disconnected"}
        
        try:
            info = await self.redis_client.info()
            
            # 统计路径缓存键数量
            pattern = "r:*:zh-*"
            cache_keys = await self.redis_client.keys(pattern)
            
            return {
                "status": "connected",
                "redis_version": info.get('redis_version', 'unknown'),
                "connected_clients": info.get('connected_clients', 0),
                "used_memory_human": info.get('used_memory_human', 'unknown'),
                "keyspace_hits": info.get('keyspace_hits', 0),
                "keyspace_misses": info.get('keyspace_misses', 0),
                "path_cache_keys": len(cache_keys),
                "cache_method": "redis_path_hash_md5",
                "config": {
                    "ttl_seconds": self.cache_ttl,
                    "compression": self.use_compression,
                    "supported_languages": len(self.target_languages)
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def clear_all_cache(self) -> bool:
        """清空所有路径缓存"""
        if not self.redis_client:
            return False
        
        try:
            pattern = "r:*:zh-*"
            cache_keys = await self.redis_client.keys(pattern)
            
            if cache_keys:
                await self.redis_client.delete(*cache_keys)
                print(f"🗑️ 已清空 {len(cache_keys)} 个Redis路径缓存")
                return True
            else:
                print("⚠️ 没有找到Redis路径缓存")
                return True
                
        except Exception as e:
            print(f"❌ 清空Redis缓存失败: {e}")
            return False
    
    async def close(self):
        """关闭Redis连接"""
        if self.redis_client:
            await self.redis_client.close()
            print("✅ Redis路径缓存连接已关闭")


# 创建全局实例
redis_path_cache_service = RedisPathCacheService()
