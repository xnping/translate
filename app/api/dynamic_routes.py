"""
动态路由生成器
根据配置文件自动生成单一目标语言翻译接口，避免重复代码
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Callable, Dict, Any

from app.models.translation import SingleTargetRequest, TranslationResponse
from app.core.dependencies import get_merger_dependency
from app.services.request_merger import RequestMerger
from app.core.language_config import get_language_config


def create_single_target_endpoint(target_lang: str, from_lang: str = "zh", description: str = None) -> Callable:
    """
    创建单一目标语言翻译接口的工厂函数
    
    Args:
        target_lang: 目标语言代码
        from_lang: 源语言代码，默认为中文
        description: 接口描述
    
    Returns:
        FastAPI路由处理函数
    """
    
    async def translate_endpoint(
        request: SingleTargetRequest,
        merger: RequestMerger = Depends(get_merger_dependency)
    ):
        """动态生成的翻译接口"""
        try:
            result = await merger.submit_request(
                text=request.text,
                from_lang=from_lang,
                to_lang=target_lang,
                font_size=request.font_size
            )
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"翻译失败: {str(e)}")
    
    # 设置函数名和文档字符串
    translate_endpoint.__name__ = f"translate_to_{target_lang}"
    translate_endpoint.__doc__ = description or f"翻译到{target_lang}"
    
    return translate_endpoint


def register_single_target_routes(router: APIRouter) -> None:
    """
    根据配置文件注册所有单一目标语言翻译路由
    
    Args:
        router: FastAPI路由器实例
    """
    language_config = get_language_config()
    endpoints = language_config.get_single_target_endpoints()
    
    for endpoint_config in endpoints:
        code = endpoint_config['code']
        endpoint_path = endpoint_config['endpoint']
        description = endpoint_config['description']
        from_lang = endpoint_config.get('from_lang', 'zh')
        
        # 创建路由处理函数
        handler = create_single_target_endpoint(
            target_lang=code,
            from_lang=from_lang,
            description=description
        )
        
        # 注册路由
        router.add_api_route(
            path=f"/{endpoint_path}",
            endpoint=handler,
            methods=["POST"],
            response_model=TranslationResponse,
            summary=description,
            description=f"将{language_config.get_language_name(from_lang)}翻译为{language_config.get_language_name(code)}",
            tags=["单一目标语言翻译"]
        )


def get_registered_endpoints() -> Dict[str, Dict[str, Any]]:
    """
    获取已注册的端点信息
    
    Returns:
        端点信息字典
    """
    language_config = get_language_config()
    endpoints = language_config.get_single_target_endpoints()
    
    result = {}
    for endpoint_config in endpoints:
        code = endpoint_config['code']
        endpoint_path = endpoint_config['endpoint']
        
        result[code] = {
            'endpoint': f"/{endpoint_path}",
            'method': 'POST',
            'description': endpoint_config['description'],
            'target_language': language_config.get_language_name(code),
            'source_language': language_config.get_language_name(endpoint_config.get('from_lang', 'zh'))
        }
    
    return result


def validate_endpoint_config() -> Dict[str, Any]:
    """
    验证端点配置的有效性
    
    Returns:
        验证结果
    """
    language_config = get_language_config()
    endpoints = language_config.get_single_target_endpoints()
    
    validation_result = {
        'valid': True,
        'errors': [],
        'warnings': [],
        'total_endpoints': len(endpoints)
    }
    
    for endpoint_config in endpoints:
        code = endpoint_config.get('code')
        endpoint_path = endpoint_config.get('endpoint')
        from_lang = endpoint_config.get('from_lang', 'zh')
        
        # 检查必需字段
        if not code:
            validation_result['errors'].append("端点配置缺少语言代码")
            validation_result['valid'] = False
            continue
            
        if not endpoint_path:
            validation_result['errors'].append(f"语言 {code} 缺少端点路径")
            validation_result['valid'] = False
            continue
        
        # 检查语言是否存在
        if not language_config.get_language_info(code):
            validation_result['errors'].append(f"未知的目标语言代码: {code}")
            validation_result['valid'] = False
        
        if not language_config.get_language_info(from_lang):
            validation_result['errors'].append(f"未知的源语言代码: {from_lang}")
            validation_result['valid'] = False
        
        # 检查语言对是否有效
        if not language_config.validate_language_pair(from_lang, code):
            validation_result['warnings'].append(f"语言对 {from_lang} -> {code} 可能无效")
    
    return validation_result
