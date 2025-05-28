"""
应用配置管理
整合原有的config.py功能
"""

import os
from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置类"""

    # 应用基本信息
    app_name: str = "翻译API服务"
    version: str = "2.0.0"
    debug: bool = False

    # 服务器配置
    host: str = "0.0.0.0"
    port: int = 9000

    # Redis配置
    redis_host: str = "45.204.6.32"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    redis_max_connections: int = 50
    redis_socket_timeout: float = 5.0
    redis_connect_timeout: float = 5.0
    redis_use_compression: bool = True
    redis_compression_min_size: int = 1024
    redis_compression_level: int = 6

    # 百度翻译API配置
    baidu_app_id: str
    baidu_secret_key: str

    # 缓存配置
    cache_ttl: int = 86400  # 24小时，与.env保持一致
    memory_cache_size: int = 1000
    memory_cache_ttl: int = 300  # 内存缓存5分钟

    # 请求合并配置
    merge_window: float = 0.1  # 100ms
    max_batch_size: int = 100  # 与.env保持一致
    max_concurrent_requests: int = 50

    # 百度API配置
    baidu_api_timeout: float = 2.0

    # 日志配置
    log_level: str = "INFO"
    log_file: Optional[str] = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @property
    def redis_url(self) -> str:
        """构建Redis连接URL"""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    def get_supported_languages(self) -> dict:
        """获取支持的语言列表"""
        from app.core.language_config import get_supported_languages
        return get_supported_languages()


@lru_cache()
def get_settings() -> Settings:
    """获取应用配置单例"""
    return Settings()
