"""
依赖注入管理
整合原有的dependencies.py功能
"""

from functools import lru_cache
from app.core.config import get_settings
from app.services.cache_service import CacheService
from app.services.translation_service import TranslationService
from app.services.request_merger import RequestMerger
from app.services.config_manager import ConfigManager


@lru_cache()
def get_cache() -> CacheService:
    """获取缓存服务单例"""
    settings = get_settings()
    return CacheService(settings)


@lru_cache()
def get_translator() -> TranslationService:
    """获取翻译服务单例"""
    settings = get_settings()
    cache = get_cache()
    return TranslationService(settings, cache)


@lru_cache()
def get_request_merger() -> RequestMerger:
    """获取请求合并器单例"""
    settings = get_settings()
    translator = get_translator()
    return RequestMerger(settings, translator)


@lru_cache()
def get_config_manager() -> ConfigManager:
    """获取配置管理器单例"""
    settings = get_settings()
    return ConfigManager(settings)


# 依赖注入函数（用于FastAPI路由）
async def get_cache_dependency() -> CacheService:
    """缓存服务依赖"""
    return get_cache()


async def get_translator_dependency() -> TranslationService:
    """翻译服务依赖"""
    return get_translator()


async def get_merger_dependency() -> RequestMerger:
    """请求合并器依赖"""
    return get_request_merger()


async def get_config_dependency() -> ConfigManager:
    """配置管理器依赖"""
    return get_config_manager()
