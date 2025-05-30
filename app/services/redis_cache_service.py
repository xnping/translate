"""
Redis连接测试服务 - 简化版
"""

import asyncio
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
        self.max_connections = int(os.getenv('REDIS_MAX_CONNECTIONS', '50'))
        self.socket_timeout = float(os.getenv('REDIS_SOCKET_TIMEOUT', '5.0'))
        self.connect_timeout = float(os.getenv('REDIS_CONNECT_TIMEOUT', '5.0'))
        
        # 缓存配置
        self.cache_ttl = int(os.getenv('CACHE_TTL', '86400'))  # 默认24小时
        self.use_compression = True
        
        # Redis连接池
        self.pool = None
        self.redis_client = None
        
        print(f" Redis连接配置:")
        print(f"  主机: {self.host}")
        print(f"  端口: {self.port}")
        print(f"  数据库: {self.db}")
        print(f"  密码: {'***' if self.password else '无'}")
        print(f"  最大连接数: {self.max_connections}")
        print(f"  缓存TTL: {self.cache_ttl}秒")
    
    async def initialize(self) -> bool:
        """
        初始化Redis连接
        
        Returns:
            是否初始化成功
        """
        try:
            # 创建连接池
            self.pool = redis.ConnectionPool(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                max_connections=self.max_connections,
                socket_timeout=self.socket_timeout,
                socket_connect_timeout=self.connect_timeout,
                decode_responses=False  # 保持二进制数据
            )
            
            # 创建Redis客户端
            self.redis_client = redis.Redis(connection_pool=self.pool)
            
            # 测试连接
            await self.test_connection()
            
            return True
            
        except Exception as e:
            print(f" Redis连接初始化失败: {str(e)}")
            return False
    
    async def test_connection(self) -> Dict[str, Any]:
        """
        测试Redis连接
        
        Returns:
            连接测试结果
        """
        try:
            # 测试基本连接
            pong = await self.redis_client.ping()
            
            # 获取Redis信息
            info = await self.redis_client.info()
            
            # 测试写入和读取
            test_key = "test:connection"
            test_value = "Redis连接测试成功"
            
            await self.redis_client.set(test_key, test_value, ex=10)
            retrieved_value = await self.redis_client.get(test_key)
            await self.redis_client.delete(test_key)
            
            result = {
                "status": "success",
                "ping": pong,
                "redis_version": info.get('redis_version', 'unknown'),
                "connected_clients": info.get('connected_clients', 0),
                "used_memory_human": info.get('used_memory_human', 'unknown'),
                "test_write_read": retrieved_value.decode('utf-8') if retrieved_value else None
            }
            
            return result
            
        except Exception as e:
            error_result = {
                "status": "error",
                "error": str(e)
            }
            return error_result
    
    async def get_cache_info(self) -> Dict[str, Any]:
        """
        获取缓存统计信息
        
        Returns:
            缓存统计信息
        """
        if not self.redis_client:
            return {"status": "disconnected"}
        
        try:
            info = await self.redis_client.info()
            
            return {
                "status": "connected",
                "redis_version": info.get('redis_version', 'unknown'),
                "connected_clients": info.get('connected_clients', 0),
                "used_memory": info.get('used_memory', 0),
                "used_memory_human": info.get('used_memory_human', 'unknown'),
                "keyspace_hits": info.get('keyspace_hits', 0),
                "keyspace_misses": info.get('keyspace_misses', 0),
                "total_commands_processed": info.get('total_commands_processed', 0)
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def close(self):
        """关闭Redis连接"""
        if self.redis_client:
            await self.redis_client.close()
        if self.pool:
            await self.pool.disconnect()


# 创建全局实例
redis_cache_service = RedisCacheService()
