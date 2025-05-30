"""
百度翻译API服务
"""

import hashlib
import random
import time
import requests
import os
from typing import List, Dict
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class BaiduTranslationService:
    """百度翻译服务类"""
    
    def __init__(self):
        """初始化百度翻译服务"""
        self.app_id = os.getenv("BAIDU_APP_ID", "")
        self.secret_key = os.getenv("BAIDU_SECRET_KEY", "")
        self.api_url = "https://fanyi-api.baidu.com/api/trans/vip/translate"
        self.timeout = float(os.getenv("BAIDU_API_TIMEOUT", "2.0"))
        
        # 验证配置
        if not self.app_id or not self.secret_key:
            raise ValueError("百度翻译配置缺失！请检查.env文件中的BAIDU_APP_ID和BAIDU_SECRET_KEY")
    
    def _generate_sign(self, query: str, salt: str) -> str:
        """生成百度翻译API签名"""
        sign_str = self.app_id + query + salt + self.secret_key
        return hashlib.md5(sign_str.encode('utf-8')).hexdigest()
    
    def translate_text(self, text: str, from_lang: str, to_lang: str) -> Dict:
        """
        翻译单个文本
        
        Args:
            text: 要翻译的文本
            from_lang: 源语言代码
            to_lang: 目标语言代码
            
        Returns:
            翻译结果字典
        """
        if not text.strip():
            return {"success": False, "error": "文本为空"}
        
        # 生成随机数
        salt = str(random.randint(32768, 65536))
        
        # 生成签名
        sign = self._generate_sign(text, salt)
        
        # 构建请求参数
        params = {
            'q': text,
            'from': from_lang,
            'to': to_lang,
            'appid': self.app_id,
            'salt': salt,
            'sign': sign
        }
        
        try:
            # 发送请求
            response = requests.get(self.api_url, params=params, timeout=self.timeout)
            result = response.json()
            
            if 'trans_result' in result:
                # 翻译成功
                translated_text = result['trans_result'][0]['dst']
                return {
                    "success": True,
                    "original": text,
                    "translated": translated_text,
                    "from_lang": from_lang,
                    "to_lang": to_lang
                }
            else:
                # 翻译失败
                error_code = result.get('error_code', 'unknown')
                error_msg = result.get('error_msg', '未知错误')
                return {
                    "success": False,
                    "error": f"百度翻译API错误: {error_code} - {error_msg}",
                    "original": text
                }
                
        except requests.RequestException as e:
            return {
                "success": False,
                "error": f"网络请求错误: {str(e)}",
                "original": text
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"翻译过程错误: {str(e)}",
                "original": text
            }
    
    def batch_translate(self, texts: List[str], from_lang: str, to_lang: str) -> Dict:
        """
        批量翻译文本
        
        Args:
            texts: 要翻译的文本列表
            from_lang: 源语言代码
            to_lang: 目标语言代码
            
        Returns:
            批量翻译结果
        """
        results = {
            "translations": [],
            "success_count": 0,
            "failed_count": 0,
            "total_count": len(texts)
        }
        
        print(f"🔄 开始批量翻译 {len(texts)} 个文本...")
        
        for i, text in enumerate(texts):
            print(f"  翻译进度: {i+1}/{len(texts)} - {text[:20]}...")
            
            # 调用单个文本翻译
            translation_result = self.translate_text(text, from_lang, to_lang)
            results["translations"].append(translation_result)
            
            if translation_result["success"]:
                results["success_count"] += 1
                print(f"    ✅ 成功: {translation_result['translated']}")
            else:
                results["failed_count"] += 1
                print(f"    ❌ 失败: {translation_result['error']}")
            
            # 添加延迟避免API限制
            time.sleep(0.1)
        
        print(f"✅ 批量翻译完成! 成功: {results['success_count']}, 失败: {results['failed_count']}")
        return results
    
    def get_config_info(self) -> Dict:
        """获取配置信息"""
        return {
            "app_id": self.app_id,
            "secret_key_preview": self.secret_key[:8] + "..." if self.secret_key else "",
            "api_url": self.api_url,
            "timeout": self.timeout
        }


# 创建全局实例
try:
    baidu_translation_service = BaiduTranslationService()
except ValueError as e:
    print(f"❌ 百度翻译服务初始化失败: {e}")
    baidu_translation_service = None
