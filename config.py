import os
from dotenv import load_dotenv
from typing import Dict, Any, Optional
import json
import time

# 加载初始环境变量
load_dotenv()

class ConfigManager:
    """集中化配置管理，支持动态刷新"""
    
    _instance = None
    _config_cache = {}
    _last_refresh_time = 0
    _refresh_interval = 60  # 默认配置刷新间隔(秒)
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance
    
    def _load_config(self):
        """加载所有配置"""
        self._config_cache = {
            # Redis 配置
            "redis": {
                "host": os.getenv('REDIS_HOST', 'localhost'),
                "port": int(os.getenv('REDIS_PORT', 6379)),
                "db": int(os.getenv('REDIS_DB', 0)),
                "password": os.getenv('REDIS_PASSWORD'),
                "ttl": int(os.getenv('REDIS_TTL', 86400)),
                "socket_timeout": float(os.getenv('REDIS_SOCKET_TIMEOUT', 1.0)),
                "max_connections": int(os.getenv('REDIS_MAX_CONNECTIONS', 50)),
                "use_compression": os.getenv('REDIS_USE_COMPRESSION', 'true').lower() == 'true',
                "compression_min_size": int(os.getenv('REDIS_COMPRESSION_MIN_SIZE', 1024)),
                "compression_level": int(os.getenv('REDIS_COMPRESSION_LEVEL', 6))
            },
            
            # 百度翻译API配置
            "baidu_api": {
                "app_id": os.getenv('BAIDU_APP_ID', ''),
                "secret_key": os.getenv('BAIDU_SECRET_KEY', ''),
                "base_url": os.getenv('BAIDU_API_URL', 'https://api.fanyi.baidu.com/api/trans/vip/translate'),
                "timeout": float(os.getenv('BAIDU_API_TIMEOUT', 2.0))
            },
            
            # 批处理配置
            "batch": {
                "max_concurrent_requests": int(os.getenv('MAX_CONCURRENT_REQUESTS', 5)),
                "default_batch_size": int(os.getenv('DEFAULT_BATCH_SIZE', 10))
            },
            
            # 应用配置
            "app": {
                "debug": os.getenv('DEBUG', 'false').lower() == 'true',
                "log_level": os.getenv('LOG_LEVEL', 'INFO')
            }
        }
        self._last_refresh_time = time.time()
    
    def get(self, section: str, key: Optional[str] = None, default: Any = None) -> Any:
        """获取配置值"""
        self._check_refresh()
        
        if section not in self._config_cache:
            return default
            
        if key is None:
            return self._config_cache[section]
            
        return self._config_cache[section].get(key, default)
    
    def _check_refresh(self):
        """检查是否需要刷新配置"""
        current_time = time.time()
        if current_time - self._last_refresh_time > self._refresh_interval:
            self._load_config()
    
    def set_refresh_interval(self, seconds: int):
        """设置配置刷新间隔"""
        self._refresh_interval = max(1, seconds)
    
    def refresh(self):
        """强制刷新配置"""
        self._load_config()
        
    def update(self, section: str, key: str, value: Any):
        """更新配置（仅内存中）"""
        if section not in self._config_cache:
            self._config_cache[section] = {}
        self._config_cache[section][key] = value
        
    def get_all(self) -> Dict[str, Dict[str, Any]]:
        """获取所有配置"""
        self._check_refresh()
        return self._config_cache.copy()
        
# 导出单例实例以便其他模块使用
config = ConfigManager()

# Redis配置
REDIS_CONFIG = {
    'HOST': config.get('redis', 'host'),
    'PORT': config.get('redis', 'port'),
    'DB': config.get('redis', 'db'),
    'PASSWORD': config.get('redis', 'password'),
    'SOCKET_TIMEOUT': config.get('redis', 'socket_timeout'),
    'DECODE_RESPONSES': True,  # 返回字符串而非字节
}

# Redis TTL配置
redis_ttl_value = config.get('redis', 'ttl')
# if redis_ttl_value and '#' in redis_ttl_value:
#     # 如果包含井号，只取井号前的部分并去除空白
#     redis_ttl_value = redis_ttl_value.split('#')[0].strip()
# REDIS_TTL = int(redis_ttl_value)

redis_ttl_value = config.get('redis', 'ttl')
REDIS_TTL = int(redis_ttl_value)


# 百度翻译API配置
BAIDU_TRANSLATE_CONFIG = {
    'APP_ID': config.get('baidu_api', 'app_id'),
    'SECRET_KEY': config.get('baidu_api', 'secret_key'),
}

# 翻译API配置
TRANSLATION_CONFIG = {
    'BASE_URL': config.get('baidu_api', 'base_url'),
    'MAX_CONCURRENT': config.get('batch', 'max_concurrent_requests'),
    'MAX_GROUP_SIZE': config.get('batch', 'default_batch_size'),
    'RETRY_COUNT': 3,       # 重试次数
    'RETRY_DELAY': 0.2,     # 初始重试延迟
    'REQUEST_TIMEOUT': 5,   # 单个请求超时时间(秒)
    'TOTAL_TIMEOUT': 60,    # 总超时时间(秒)
}

# HTTP客户端配置
HTTP_CLIENT_CONFIG = {
    'TTL_DNS_CACHE': 300,   # DNS缓存时间
    'USE_DNS_CACHE': True,  # 使用DNS缓存
    'FORCE_CLOSE': False,   # 允许连接复用
}

# 应用配置
APP_CONFIG = {
    'TITLE': 'TranslationAPI',
    'CORS_ORIGINS': ["*"],  # 允许所有来源，生产环境中应限制
    'STATIC_DIR': 'static',
    'HOST': '0.0.0.0',
    'PORT': 8000,
    'DEBUG': config.get('app', 'debug'),
} 