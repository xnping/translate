"""
语言配置管理器
从配置文件加载语言相关配置，避免重复代码
"""

import yaml
import os
from typing import Dict, List, Optional, Any
from functools import lru_cache
from pathlib import Path


class LanguageConfig:
    """语言配置管理器"""
    
    def __init__(self, config_path: Optional[str] = None):
        if config_path is None:
            # 默认配置文件路径
            config_path = Path(__file__).parent.parent.parent / "config" / "languages.yaml"
        
        self.config_path = config_path
        self._config = None
        self._load_config()
    
    def _load_config(self):
        """加载配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"语言配置文件未找到: {self.config_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"语言配置文件格式错误: {e}")
    
    def get_supported_languages(self) -> Dict[str, str]:
        """获取支持的语言列表（代码 -> 名称映射）"""
        languages = {}
        for code, config in self._config['languages'].items():
            if config.get('enabled', True):
                languages[code] = config['name']
        return languages
    
    def get_target_languages(self) -> Dict[str, str]:
        """获取目标语言列表"""
        languages = {}
        for code, config in self._config['languages'].items():
            if config.get('enabled', True) and config.get('is_target', True):
                languages[code] = config['name']
        return languages
    
    def get_source_languages(self) -> Dict[str, str]:
        """获取源语言列表"""
        languages = {}
        for code, config in self._config['languages'].items():
            if config.get('enabled', True) and config.get('is_source', True):
                languages[code] = config['name']
        return languages
    
    def get_single_target_endpoints(self) -> List[Dict[str, str]]:
        """获取单一目标语言接口配置"""
        return self._config.get('single_target_endpoints', [])
    
    def get_frontend_source_languages(self) -> List[Dict[str, str]]:
        """获取前端源语言选项"""
        return self._config.get('frontend', {}).get('source_languages', [])
    
    def get_frontend_target_languages(self) -> List[Dict[str, str]]:
        """获取前端目标语言选项"""
        return self._config.get('frontend', {}).get('target_languages', [])
    
    def get_testing_languages(self) -> List[str]:
        """获取测试用语言代码列表"""
        return self._config.get('testing', {}).get('target_languages', [])
    
    def get_test_texts(self) -> Dict[str, List[str]]:
        """获取测试文本"""
        return self._config.get('testing', {}).get('test_texts', {})
    
    def get_language_info(self, code: str) -> Optional[Dict[str, Any]]:
        """获取指定语言的详细信息"""
        return self._config.get('languages', {}).get(code)
    
    def is_language_enabled(self, code: str) -> bool:
        """检查语言是否启用"""
        lang_info = self.get_language_info(code)
        return lang_info.get('enabled', False) if lang_info else False
    
    def can_be_source(self, code: str) -> bool:
        """检查语言是否可以作为源语言"""
        lang_info = self.get_language_info(code)
        return lang_info.get('is_source', False) if lang_info else False
    
    def can_be_target(self, code: str) -> bool:
        """检查语言是否可以作为目标语言"""
        lang_info = self.get_language_info(code)
        return lang_info.get('is_target', False) if lang_info else False
    
    def get_language_name(self, code: str) -> Optional[str]:
        """获取语言名称"""
        lang_info = self.get_language_info(code)
        return lang_info.get('name') if lang_info else None
    
    def validate_language_pair(self, from_lang: str, to_lang: str) -> bool:
        """验证语言对是否有效"""
        if from_lang == to_lang:
            return False
        
        if not self.can_be_source(from_lang):
            return False
        
        if not self.can_be_target(to_lang):
            return False
        
        return True
    
    def reload_config(self):
        """重新加载配置文件"""
        self._load_config()


# 全局语言配置实例
@lru_cache()
def get_language_config() -> LanguageConfig:
    """获取语言配置单例"""
    return LanguageConfig()


# 便捷函数
def get_supported_languages() -> Dict[str, str]:
    """获取支持的语言列表"""
    return get_language_config().get_supported_languages()


def get_target_languages() -> Dict[str, str]:
    """获取目标语言列表"""
    return get_language_config().get_target_languages()


def get_source_languages() -> Dict[str, str]:
    """获取源语言列表"""
    return get_language_config().get_source_languages()


def validate_language_pair(from_lang: str, to_lang: str) -> bool:
    """验证语言对是否有效"""
    return get_language_config().validate_language_pair(from_lang, to_lang)


def get_language_name(code: str) -> Optional[str]:
    """获取语言名称"""
    return get_language_config().get_language_name(code)
