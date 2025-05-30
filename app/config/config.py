"""
应用配置管理 - 自动同步.env文件
修改.env文件后自动生效，无需修改此配置文件
"""

import os
from functools import lru_cache
from typing import Optional, AsyncGenerator, Any
from pydantic_settings import BaseSettings
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """数据库模型基类"""
    pass



class Settings(BaseSettings):
    """应用配置类 - 自动同步.env文件的所有配置"""

    # ===== 应用基本信息 =====
    app_name: str = "翻译API服务"
    version: str = "1.0.0"

    # ===== 服务器配置 =====
    host: str = "localhost"
    port: int = 9000
    debug: bool = False
    log_level: str = "INFO"
    log_file: Optional[str] = None

    # ===== Redis配置 =====
    redis_host: str = "127.0.0.1"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    redis_max_connections: int = 50
    redis_socket_timeout: float = 5.0
    redis_connect_timeout: float = 5.0
    redis_use_compression: bool = True
    redis_compression_min_size: int = 1024
    redis_compression_level: int = 6

    # ===== 缓存配置 =====
    cache_ttl: int = 86400
    memory_cache_size: int = 1000
    memory_cache_ttl: int = 300

    # ===== 文件缓存配置 =====
    file_cache_ttl_days: int = 7
    file_cache_max_size_mb: int = 1024
    file_cache_cleanup_interval_hours: int = 24

    # ===== 百度翻译API配置 =====
    baidu_app_id: str = ""
    baidu_secret_key: str = ""
    baidu_api_timeout: float = 2.0

    # ===== 请求处理配置 =====
    merge_window: float = 0.1
    max_batch_size: int = 100
    max_concurrent_requests: int = 50

    # ===== MySQL数据库配置 =====
    db_username: str = "root"
    db_password: str = "123456"
    db_host: str = "8.138.177.105"
    db_port: int = 3306
    db_name: str = "baidu"

    # ===== JWT认证配置 =====
    jwt_secret: str = "default-jwt-secret"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 30
    jwt_refresh_expire_days: int = 7

    # ===== 数据库连接配置（非敏感信息）=====
    db_charset: str = "utf8mb4"
    db_pool_size: int = 20
    db_max_overflow: int = 30
    db_pool_timeout: int = 30
    db_pool_recycle: int = 3600
    db_pool_pre_ping: bool = True
    db_echo: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        # 自动从环境变量读取，不区分大小写
        case_sensitive = False
        # 允许额外的字段
        extra = "allow"

    @property
    def redis_url(self) -> str:
        """构建Redis连接URL"""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @property
    def database_url(self) -> str:
        """构建异步数据库连接URL"""
        return (
            f"mysql+aiomysql://{self.db_username}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
            f"?charset={self.db_charset}"
        )

    @property
    def sync_database_url(self) -> str:
        """构建同步数据库连接URL（用于迁移等）"""
        return (
            f"mysql+pymysql://{self.db_username}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
            f"?charset={self.db_charset}"
        )

    def get_database_engine_config(self) -> dict:
        """获取数据库引擎配置"""
        return {
            "echo": self.db_echo,
            "pool_size": self.db_pool_size,
            "max_overflow": self.db_max_overflow,
            "pool_timeout": self.db_pool_timeout,
            "pool_recycle": self.db_pool_recycle,
            "pool_pre_ping": self.db_pool_pre_ping,
        }

    def get_config_dict(self) -> dict:
        """获取所有配置的字典形式"""
        return self.dict()

    def get_env_config(self, key: str, default: Any = None) -> Any:
        """动态获取环境变量配置"""
        return getattr(self, key.lower(), default)



class DatabaseManager:
    """数据库管理器"""

    def __init__(self):
        self.engine = None
        self.session_factory = None
        self._initialized = False

    def initialize(self):
        """初始化数据库连接"""
        if self._initialized:
            return

        settings = get_settings()

        # 创建异步引擎
        self.engine = create_async_engine(
            settings.database_url,
            **settings.get_database_engine_config()
        )

        # 创建会话工厂
        self.session_factory = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            autocommit=False,
            autoflush=True,
            expire_on_commit=False
        )

        self._initialized = True

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """获取数据库会话"""
        if not self._initialized:
            raise RuntimeError("数据库未初始化，请先调用 initialize()")

        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def create_tables(self):
        """创建所有表"""
        if not self.engine:
            raise RuntimeError("数据库引擎未初始化")

        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def close(self):
        """关闭数据库连接"""
        if self.engine:
            await self.engine.dispose()
            self._initialized = False


# 全局实例
@lru_cache()
def get_settings() -> Settings:
    """获取应用配置单例"""
    return Settings()


# 全局数据库管理器实例
db_manager = DatabaseManager()


# FastAPI依赖注入函数
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话的依赖注入函数"""
    async for session in db_manager.get_session():
        yield session


# 数据库生命周期管理函数
async def init_database():
    """初始化数据库"""
    db_manager.initialize()
    await db_manager.create_tables()


async def close_database():
    """关闭数据库连接"""
    await db_manager.close()
