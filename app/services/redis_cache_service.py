"""
Redis连接测试服务 - 极简版
"""

from typing import Dict, Any
import redis.asyncio as redis
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class RedisCacheService:
    """Redis连接测试服务类"""
    
    def __init__(self):
        """初始化Redis连接测试服务"""
        self.host = os.getenv('REDIS_HOST', 'localhost')
        self.port = int(os.getenv('REDIS_PORT', '6379'))
        self.db = int(os.getenv('REDIS_DB', '0'))
        self.password = os.getenv('REDIS_PASSWORD')
        self.cache_ttl = int(os.getenv('CACHE_TTL', '86400'))
        self.use_compression = True
        
        # Redis连接
        self.redis_client = None
    
    async def initialize(self) -> bool:
        """初始化Redis连接"""
        try:
            self.redis_client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=False
            )
            
            # 测试连接
            await self.redis_client.ping()
            return True
            
        except Exception as e:
            print(f"❌ Redis连接失败: {str(e)}")
            return False
    
    async def get_cache_info(self) -> Dict[str, Any]:
        """获取Redis状态信息"""
        if not self.redis_client:
            return {"status": "disconnected"}
        
        try:
            info = await self.redis_client.info()
            return {
                "status": "connected",
                "redis_version": info.get('redis_version', 'unknown'),
                "connected_clients": info.get('connected_clients', 0),
                "used_memory_human": info.get('used_memory_human', 'unknown')
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def close(self):
        """关闭Redis连接"""
        if self.redis_client:
            await self.redis_client.close()


# 创建全局实例
redis_cache_service = RedisCacheService()
