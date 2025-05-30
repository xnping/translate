"""
百度翻译服务 - 简化版（只保留并发异步方法）
"""

import hashlib
import random
import time
import asyncio
import aiohttp
from typing import List, Dict
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class BaiduTranslationService:
    """百度翻译服务类 - 只提供高速并发翻译"""
    
    def __init__(self):
        """初始化百度翻译服务"""
        self.app_id = os.getenv('BAIDU_APP_ID')
        self.secret_key = os.getenv('BAIDU_SECRET_KEY')
        self.api_url = "https://fanyi-api.baidu.com/api/trans/vip/translate"
        self.timeout = float(os.getenv('BAIDU_API_TIMEOUT', '2.0'))
        
        # 验证配置
        if not self.app_id or not self.secret_key:
            raise ValueError("百度翻译配置不完整，请检查.env文件中的BAIDU_APP_ID和BAIDU_SECRET_KEY")
        
        print(f"✅ 百度翻译服务初始化成功")
        print(f"  APP_ID: {self.app_id}")
        print(f"  SECRET_KEY: {self.secret_key[:8]}...")
        print(f"  TIMEOUT: {self.timeout}秒")
    
    def _generate_sign(self, query: str, salt: str) -> str:
        sign_str = f"{self.app_id}{query}{salt}{self.secret_key}"
        return hashlib.md5(sign_str.encode('utf-8')).hexdigest()
    async def async_translate_text(self, session: aiohttp.ClientSession, text: str, from_lang: str, to_lang: str) -> Dict:
        if not text.strip():
            return {"success": False, "error": "文本为空", "original": text}
        salt = str(random.randint(32768, 65536))
        sign = self._generate_sign(text, salt)
        params = {
            'q': text,
            'from': from_lang,
            'to': to_lang,
            'appid': self.app_id,
            'salt': salt,
            'sign': sign
        }
        
        try:
            async with session.get(self.api_url, params=params, timeout=self.timeout) as response:
                result = await response.json()
                if 'trans_result' in result:
                    translated_text = result['trans_result'][0]['dst']
                    return {
                        "success": True,
                        "original": text,
                        "translated": translated_text,
                        "from_lang": from_lang,
                        "to_lang": to_lang
                    }
                else:
                    error_code = result.get('error_code', 'unknown')
                    error_msg = result.get('error_msg', '未知错误')
                    return {
                        "success": False,
                        "error": f"百度翻译API错误: {error_code} - {error_msg}",
                        "original": text
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": f"异步翻译错误: {str(e)}",
                "original": text
            }
    
    async def concurrent_batch_translate(self, texts: List[str], from_lang: str, to_lang: str, max_concurrent: int = 15) -> Dict:
        """
        并发批量翻译 - 翻译方法
        Args:
            texts: 要翻译的文本列表
            from_lang: 源语言代码
            to_lang: 目标语言代码
            max_concurrent: 最大并发数
        Returns:
            批量翻译结果
        """
        print(f"⚡ 开始高速并发翻译 {len(texts)} 个文本 (并发数: {max_concurrent})...")
        start_time = time.time()
        # 去重并保持顺序
        unique_texts = []
        text_index_map = {}
        for i, text in enumerate(texts):
            if text not in text_index_map:
                text_index_map[text] = len(unique_texts)
                unique_texts.append(text)
        print(f"📊 去重后需要翻译: {len(unique_texts)} 个唯一文本")
        results = {
            "translations": [],
            "success_count": 0,
            "failed_count": 0,
            "total_count": len(texts),
            "unique_count": len(unique_texts),
            "duration": 0
        }
        if not unique_texts:
            results["duration"] = 0
            return results
        # 创建异步会话
        connector = aiohttp.TCPConnector(limit=max_concurrent)
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            # 创建并发任务
            semaphore = asyncio.Semaphore(max_concurrent)
            
            async def translate_with_semaphore(text):
                async with semaphore:
                    return await self.async_translate_text(session, text, from_lang, to_lang)
            # 执行并发翻译
            unique_results = await asyncio.gather(
                *[translate_with_semaphore(text) for text in unique_texts],
                return_exceptions=True
            )
        # 处理结果
        translation_map = {}
        for i, result in enumerate(unique_results):
            if isinstance(result, Exception):
                result = {
                    "success": False,
                    "error": f"并发执行错误: {str(result)}",
                    "original": unique_texts[i]
                }
            translation_map[unique_texts[i]] = result
            
            if result["success"]:
                results["success_count"] += 1
            else:
                results["failed_count"] += 1
        # 根据原始顺序重建结果
        for text in texts:
            results["translations"].append(translation_map[text])
        
        end_time = time.time()
        results["duration"] = round(end_time - start_time, 2)
        
        print(f"⚡ 高速翻译完成! 耗时: {results['duration']}秒")
        print(f"📊 成功: {results['success_count']}, 失败: {results['failed_count']}")
        if results['duration'] > 0:
            print(f"🚀 平均速度: {len(unique_texts)/results['duration']:.1f} 文本/秒")
        
        return results
    
    def get_config_info(self) -> Dict:
        """获取配置信息"""
        return {
            "app_id": self.app_id,
            "secret_key_preview": self.secret_key[:8] + "..." if self.secret_key else "",
            "api_url": self.api_url,
            "timeout": self.timeout
        }
try:
    baidu_translation_service = BaiduTranslationService()
except ValueError as e:
    print(f" 百度翻译服务初始化失败: {e}")
    baidu_translation_service = None
