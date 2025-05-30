"""
MySQL数据库连接服务
"""

import aiomysql
import os
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class MySQLService:
    """MySQL数据库服务类"""
    
    def __init__(self):
        """初始化MySQL连接配置"""
        self.host = os.getenv('DB_HOST', 'localhost')
        self.port = int(os.getenv('DB_PORT', '3306'))
        self.user = os.getenv('DB_USER', 'root')
        self.password = os.getenv('DB_PASSWORD', '')
        self.database = os.getenv('DB_NAME', 'baidu')
        self.charset = 'utf8mb4'
        
        self.pool = None
        
        print(f"🔧 MySQL服务配置:")
        print(f"  主机: {self.host}:{self.port}")
        print(f"  数据库: {self.database}")
        print(f"  用户: {self.user}")
        print(f"  字符集: {self.charset}")
    
    async def create_pool(self):
        """创建连接池"""
        try:
            self.pool = await aiomysql.create_pool(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                db=self.database,
                charset=self.charset,
                autocommit=True,  # 改为自动提交
                minsize=5,
                maxsize=20
            )
            print("✅ MySQL连接池创建成功")
            return True
        except Exception as e:
            print(f"❌ MySQL连接池创建失败: {e}")
            return False
    
    async def execute_query(self, query: str, params: tuple = None) -> List[Dict]:
        """执行查询语句"""
        if not self.pool:
            await self.create_pool()

        try:
            print(f"🔍 MySQL执行查询: {query}, 参数: {params}")
            async with self.pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute(query, params)
                    result = await cursor.fetchall()
                    print(f"✅ MySQL查询成功，结果数量: {len(result)}, 结果: {result}")
                    return result
        except Exception as e:
            print(f"❌ MySQL查询失败: {e}")
            raise e
    
    async def execute_insert(self, query: str, params: tuple = None) -> int:
        """执行插入语句，返回插入的ID"""
        if not self.pool:
            print("🔍 连接池不存在，创建连接池...")
            await self.create_pool()

        try:
            print(f"🔍 MySQL执行插入: {query}, 参数: {params}")
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(query, params)
                    # 不需要手动commit，因为autocommit=True
                    last_id = cursor.lastrowid
                    print(f"✅ MySQL插入成功，lastrowid: {last_id}")
                    return last_id
        except Exception as e:
            print(f"❌ MySQL插入失败: {e}")
            raise e
    
    async def execute_update(self, query: str, params: tuple = None) -> int:
        """执行更新语句，返回影响的行数"""
        if not self.pool:
            await self.create_pool()
        
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(query, params)
                # 不需要手动commit，因为autocommit=True
                return cursor.rowcount
    
    async def execute_delete(self, query: str, params: tuple = None) -> int:
        """执行删除语句，返回影响的行数"""
        if not self.pool:
            await self.create_pool()
        
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(query, params)
                # 不需要手动commit，因为autocommit=True
                return cursor.rowcount
    
    async def close_pool(self):
        """关闭连接池"""
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()
            print("✅ MySQL连接池已关闭")


# 创建全局实例
mysql_service = MySQLService()
