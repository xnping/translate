"""
配置管理服务
重构自原有的config_manager.py，保持所有功能
"""

import os
import json
import time
import asyncio
import hashlib
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path

from app.core.config import Settings


@dataclass
class ConfigVersion:
    """配置版本信息"""
    version: str
    timestamp: float
    description: str
    config_data: Dict[str, Any]
    checksum: str


class ConfigManager:
    """配置热更新管理器，支持版本控制和回滚"""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.config_file = ".env"
        self.backup_dir = Path("config_backups")
        self.backup_dir.mkdir(exist_ok=True)

        # 当前配置
        self.current_config: Dict[str, Any] = {}
        self.current_version: str = "1.0.0"

        # 配置版本历史
        self.version_history: List[ConfigVersion] = []
        self.max_versions = 10  # 最多保留10个版本

        # 配置变更监听器
        self.change_listeners: List[Callable[[Dict[str, Any]], None]] = []

        # 文件监控
        self.last_modified = 0
        self.watch_task = None

        # 统计信息
        self.stats = {
            "config_reloads": 0,
            "version_rollbacks": 0,
            "hot_updates": 0,
            "last_update_time": 0
        }

        # 初始化标志
        self._initialized = False

        # 初始化
        self._load_initial_config()
        self._load_version_history()

    async def initialize(self):
        """初始化配置管理器（在有事件循环时调用）"""
        if not self._initialized:
            self._start_file_watcher()
            self._initialized = True

    def _load_initial_config(self):
        """加载初始配置"""
        try:
            if os.path.exists(self.config_file):
                self.last_modified = os.path.getmtime(self.config_file)
                self.current_config = self._parse_env_file(self.config_file)
                print(f"已加载配置文件: {self.config_file}")
            else:
                print(f"配置文件不存在: {self.config_file}")
                self.current_config = {}
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            self.current_config = {}

    def _parse_env_file(self, file_path: str) -> Dict[str, Any]:
        """解析.env文件"""
        config = {}
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")

                        # 尝试转换数据类型
                        if value.lower() in ('true', 'false'):
                            config[key] = value.lower() == 'true'
                        elif value.isdigit():
                            config[key] = int(value)
                        elif value.replace('.', '').isdigit():
                            config[key] = float(value)
                        else:
                            config[key] = value
        except Exception as e:
            print(f"解析配置文件失败: {e}")

        return config

    def _calculate_checksum(self, config: Dict[str, Any]) -> str:
        """计算配置的校验和"""
        config_str = json.dumps(config, sort_keys=True)
        return hashlib.md5(config_str.encode()).hexdigest()

    def _save_version(self, description: str = "自动保存"):
        """保存当前配置版本"""
        version = ConfigVersion(
            version=self._generate_version(),
            timestamp=time.time(),
            description=description,
            config_data=self.current_config.copy(),
            checksum=self._calculate_checksum(self.current_config)
        )

        self.version_history.append(version)

        # 限制版本数量
        if len(self.version_history) > self.max_versions:
            self.version_history = self.version_history[-self.max_versions:]

        # 保存到文件
        self._save_version_to_file(version)
        self._save_version_history()

    def _generate_version(self) -> str:
        """生成版本号"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"v{timestamp}"

    def _save_version_to_file(self, version: ConfigVersion):
        """保存版本到文件"""
        try:
            version_file = self.backup_dir / f"config_{version.version}.json"
            with open(version_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(version), f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存配置版本失败: {e}")

    def _save_version_history(self):
        """保存版本历史"""
        try:
            history_file = self.backup_dir / "version_history.json"
            history_data = [asdict(v) for v in self.version_history]
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(history_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存版本历史失败: {e}")

    def _load_version_history(self):
        """加载版本历史"""
        try:
            history_file = self.backup_dir / "version_history.json"
            if history_file.exists():
                with open(history_file, 'r', encoding='utf-8') as f:
                    history_data = json.load(f)
                    self.version_history = [
                        ConfigVersion(**data) for data in history_data
                    ]
        except Exception as e:
            print(f"加载版本历史失败: {e}")

    def _start_file_watcher(self):
        """启动文件监控"""
        try:
            if self.watch_task is None or self.watch_task.done():
                self.watch_task = asyncio.create_task(self._watch_config_file())
        except RuntimeError:
            # 没有运行的事件循环，稍后再启动
            pass

    async def _watch_config_file(self):
        """监控配置文件变化"""
        while True:
            try:
                await asyncio.sleep(1)  # 每秒检查一次

                if os.path.exists(self.config_file):
                    current_modified = os.path.getmtime(self.config_file)
                    if current_modified > self.last_modified:
                        print("检测到配置文件变化，正在重新加载...")
                        await self._reload_config()
                        self.last_modified = current_modified

            except Exception as e:
                print(f"文件监控异常: {e}")
                await asyncio.sleep(5)  # 出错时等待5秒

    async def _reload_config(self):
        """重新加载配置"""
        try:
            # 保存当前版本
            self._save_version("文件变化自动保存")

            # 加载新配置
            new_config = self._parse_env_file(self.config_file)
            old_config = self.current_config.copy()

            # 检查是否有实际变化
            if self._calculate_checksum(new_config) != self._calculate_checksum(old_config):
                self.current_config = new_config
                self.stats["config_reloads"] += 1
                self.stats["hot_updates"] += 1
                self.stats["last_update_time"] = time.time()

                print("配置已热更新")

                # 通知监听器
                await self._notify_listeners(new_config)
            else:
                print("配置文件无实际变化")

        except Exception as e:
            print(f"重新加载配置失败: {e}")

    async def _notify_listeners(self, new_config: Dict[str, Any]):
        """通知配置变更监听器"""
        for listener in self.change_listeners:
            try:
                if asyncio.iscoroutinefunction(listener):
                    await listener(new_config)
                else:
                    listener(new_config)
            except Exception as e:
                print(f"通知监听器失败: {e}")

    def add_change_listener(self, listener: Callable[[Dict[str, Any]], None]):
        """添加配置变更监听器"""
        self.change_listeners.append(listener)

    def get_config(self, key: Optional[str] = None, default: Any = None) -> Any:
        """获取配置值"""
        if key is None:
            return self.current_config.copy()
        return self.current_config.get(key, default)

    def update_config(self, updates: Dict[str, Any], description: str = "手动更新") -> bool:
        """更新配置"""
        try:
            # 保存当前版本
            self._save_version(f"更新前备份: {description}")

            # 更新配置
            self.current_config.update(updates)

            # 写入文件
            self._write_env_file()

            self.stats["hot_updates"] += 1
            self.stats["last_update_time"] = time.time()

            print(f"配置已更新: {description}")
            return True

        except Exception as e:
            print(f"更新配置失败: {e}")
            return False

    def _write_env_file(self):
        """写入.env文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                for key, value in self.current_config.items():
                    f.write(f"{key}={value}\n")
        except Exception as e:
            print(f"写入配置文件失败: {e}")
            raise

    def rollback_to_version(self, version: str) -> bool:
        """回滚到指定版本"""
        try:
            # 查找版本
            target_version = None
            for v in self.version_history:
                if v.version == version:
                    target_version = v
                    break

            if target_version is None:
                print(f"未找到版本: {version}")
                return False

            # 保存当前版本
            self._save_version(f"回滚前备份: 回滚到{version}")

            # 恢复配置
            self.current_config = target_version.config_data.copy()

            # 写入文件
            self._write_env_file()

            self.stats["version_rollbacks"] += 1
            self.stats["last_update_time"] = time.time()

            print(f"已回滚到版本: {version}")
            return True

        except Exception as e:
            print(f"回滚失败: {e}")
            return False

    def get_version_history(self) -> List[Dict[str, Any]]:
        """获取版本历史"""
        return [
            {
                "version": v.version,
                "timestamp": v.timestamp,
                "description": v.description,
                "checksum": v.checksum,
                "datetime": datetime.fromtimestamp(v.timestamp).strftime("%Y-%m-%d %H:%M:%S")
            }
            for v in self.version_history
        ]

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        stats = self.stats.copy()
        stats.update({
            "current_version": self.current_version,
            "total_versions": len(self.version_history),
            "config_keys": len(self.current_config),
            "last_update_datetime": (
                datetime.fromtimestamp(self.stats["last_update_time"]).strftime("%Y-%m-%d %H:%M:%S")
                if self.stats["last_update_time"] > 0 else "从未更新"
            )
        })
        return stats

    async def close(self):
        """关闭配置管理器"""
        if self.watch_task and not self.watch_task.done():
            self.watch_task.cancel()
            try:
                await self.watch_task
            except asyncio.CancelledError:
                pass
