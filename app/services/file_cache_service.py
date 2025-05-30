"""
文件缓存服务 - 分片文件系统缓存
"""

import os
import json
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from app.config.config import get_settings


class FileCacheService:
    """文件缓存服务类"""
    
    def __init__(self):
        """初始化文件缓存服务"""
        # 从配置文件读取设置
        self.settings = get_settings()

        self.cache_dir = "cache/translations"
        self.index_file = "cache/index/cache_index.json"
        self.cache_ttl_days = self.settings.file_cache_ttl_days
        self.max_size_mb = self.settings.file_cache_max_size_mb
        self.cleanup_interval_hours = self.settings.file_cache_cleanup_interval_hours

        # 中文转其他9种语言映射
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

        # 确保目录存在
        os.makedirs(self.cache_dir, exist_ok=True)
        os.makedirs(os.path.dirname(self.index_file), exist_ok=True)

        # 创建语言对目录
        self.create_language_directories()

        # 加载索引
        self.cache_index = self.load_index()

        print(f"📁 文件缓存服务初始化完成")
        print(f"  缓存目录: {self.cache_dir}")
        print(f"  索引文件: {self.index_file}")
        print(f"  缓存TTL: {self.cache_ttl_days}天 (来自配置)")
        print(f"  最大缓存大小: {self.max_size_mb}MB (来自配置)")
        print(f"  清理间隔: {self.cleanup_interval_hours}小时 (来自配置)")
        print(f"  源语言: 中文 (zh)")
        print(f"  目标语言: {len(self.target_languages)}种")
        print(f"  目标语言列表: {', '.join(self.target_languages.values())}")

    def create_language_directories(self):
        """创建中文转其他语言的缓存目录结构"""
        print("📂 创建中文转其他语言缓存目录...")

        # 只创建中文转其他语言的目录
        for target_code, target_name in self.target_languages.items():
            # 创建语言目录：chinese-english, chinese-malay 等
            lang_dir = os.path.join(
                self.cache_dir,
                f"chinese-{target_name}"
            )
            os.makedirs(lang_dir, exist_ok=True)

            # 在语言目录下创建哈希分片目录
            for i in range(16):  # 00-0f
                for j in range(16):  # 00-0f
                    hash_dir = os.path.join(lang_dir, f"{i:02x}", f"{j:02x}")
                    os.makedirs(hash_dir, exist_ok=True)

        print(f"✅ 已创建 {len(self.target_languages)} 个中文转其他语言目录")

    def get_language_pair_name(self, source_lang: str, target_lang: str) -> str:
        """获取语言对名称 - 只支持中文转其他语言"""
        if source_lang != "zh":
            raise ValueError(f"只支持中文(zh)作为源语言，当前源语言: {source_lang}")

        target_name = self.target_languages.get(target_lang)
        if not target_name:
            raise ValueError(f"不支持的目标语言: {target_lang}，支持的语言: {list(self.target_languages.keys())}")

        return f"chinese-{target_name}"

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
        """生成基于路径的MD5缓存键"""
        # 标准化路径
        normalized_path = self.normalize_path(path)

        # 组合路径和语言对
        content = f"{normalized_path}|{source_lang}|{target_lang}"

        # 生成MD5哈希并截取12位
        return hashlib.md5(content.encode('utf-8')).hexdigest()[:12]
    
    def get_cache_file_path(self, cache_key: str, source_lang: str, target_lang: str) -> str:
        """获取缓存文件路径 - 按语言对和哈希分片"""
        # 获取语言对名称
        lang_pair = self.get_language_pair_name(source_lang, target_lang)

        # 分片策略：语言对/前2位/第3-4位/完整哈希.json
        return os.path.join(
            self.cache_dir,
            lang_pair,
            cache_key[:2],
            cache_key[2:4],
            f"{cache_key}.json"
        )
    
    def load_index(self) -> Dict:
        """加载缓存索引"""
        if os.path.exists(self.index_file):
            try:
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save_index(self):
        """保存缓存索引"""
        try:
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache_index, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"❌ 保存索引失败: {e}")
    
    def is_cache_expired(self, cache_data: Dict) -> bool:
        """检查缓存是否过期"""
        try:
            expires_at = datetime.fromisoformat(cache_data["metadata"]["expires_at"])
            return datetime.now() > expires_at
        except:
            return True
    
    async def get_cache(self, path: str, source_lang: str, target_lang: str) -> Optional[Dict]:
        """获取缓存"""
        try:
            # 1. 生成基于路径的缓存键
            cache_key = self.generate_cache_key(path, source_lang, target_lang)
            
            # 2. 检查索引
            if cache_key in self.cache_index:
                cache_info = self.cache_index[cache_key]
                file_path = cache_info["file_path"]
                
                # 3. 检查文件是否存在
                if os.path.exists(file_path):
                    # 4. 加载缓存数据
                    with open(file_path, 'r', encoding='utf-8') as f:
                        cache_data = json.load(f)
                    
                    # 5. 检查是否过期
                    if not self.is_cache_expired(cache_data):
                        print(f"✅ 文件缓存命中: {cache_key[:8]}...")
                        return cache_data["content"]
                    else:
                        print(f"⏰ 文件缓存已过期: {cache_key[:8]}...")
                        # 删除过期缓存
                        await self.delete_cache_file(cache_key, file_path)
                else:
                    print(f"📁 缓存文件不存在: {cache_key[:8]}...")
                    # 从索引中删除无效条目
                    del self.cache_index[cache_key]
                    self.save_index()
            
            print(f"❌ 文件缓存未命中: {cache_key[:8]}...")
            return None
            
        except Exception as e:
            print(f"❌ 获取文件缓存失败: {e}")
            return None
    
    async def set_cache(self, path: str, source_lang: str, target_lang: str, translation_result: Dict) -> bool:
        """设置缓存"""
        try:
            # 1. 生成基于路径的缓存键
            cache_key = self.generate_cache_key(path, source_lang, target_lang)
            
            # 2. 获取文件路径
            file_path = self.get_cache_file_path(cache_key, source_lang, target_lang)
            
            # 3. 创建目录
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # 4. 准备缓存数据
            cache_data = {
                "metadata": {
                    "cache_key": cache_key,
                    "created_at": datetime.now().isoformat(),
                    "expires_at": (datetime.now() + timedelta(days=self.cache_ttl_days)).isoformat(),
                    "source_lang": source_lang,
                    "target_lang": target_lang,
                    "path": path,
                    "file_path": file_path,
                    "cache_method": "path_hash_md5"
                },
                "content": translation_result
            }
            
            # 5. 保存缓存文件
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False)
            
            # 6. 更新索引
            self.cache_index[cache_key] = {
                "file_path": file_path,
                "created_at": cache_data["metadata"]["created_at"],
                "expires_at": cache_data["metadata"]["expires_at"],
                "path": path,
                "source_lang": source_lang,
                "target_lang": target_lang,
                "cache_method": "path_hash_md5"
            }
            self.save_index()
            
            print(f"💾 文件缓存已保存: {cache_key[:8]}...")
            return True
            
        except Exception as e:
            print(f"❌ 保存文件缓存失败: {e}")
            return False
    
    async def delete_cache_file(self, cache_key: str, file_path: str):
        """删除缓存文件"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
            
            if cache_key in self.cache_index:
                del self.cache_index[cache_key]
                self.save_index()
                
            print(f"🗑️ 已删除过期缓存: {cache_key[:8]}...")
        except Exception as e:
            print(f"❌ 删除缓存文件失败: {e}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        try:
            total_files = len(self.cache_index)
            total_size = 0
            language_pairs = {}

            for cache_info in self.cache_index.values():
                file_path = cache_info["file_path"]
                if os.path.exists(file_path):
                    total_size += os.path.getsize(file_path)

                    # 统计语言对
                    source_lang = cache_info.get("source_lang", "unknown")
                    target_lang = cache_info.get("target_lang", "unknown")
                    lang_pair = self.get_language_pair_name(source_lang, target_lang)
                    language_pairs[lang_pair] = language_pairs.get(lang_pair, 0) + 1

            return {
                "status": "active",
                "total_files": total_files,
                "total_size_mb": round(total_size / 1024 / 1024, 2),
                "cache_dir": self.cache_dir,
                "config": {
                    "ttl_days": self.cache_ttl_days,
                    "max_size_mb": self.max_size_mb,
                    "cleanup_interval_hours": self.cleanup_interval_hours,
                    "config_source": ".env文件"
                },
                "source_language": "chinese (zh)",
                "supported_target_languages": len(self.target_languages),
                "language_directories": language_pairs,
                "target_languages": self.target_languages
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }


# 创建全局实例
file_cache_service = FileCacheService()
