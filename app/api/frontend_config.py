"""
前端配置API
提供前端所需的语言配置和接口信息
"""

from fastapi import APIRouter
from typing import Dict, List, Any

from app.core.language_config import get_language_config
from app.api.dynamic_routes import get_registered_endpoints

router = APIRouter()


@router.get("/frontend/languages")
async def get_frontend_languages():
    """获取前端语言选择器配置"""
    language_config = get_language_config()
    
    return {
        "source_languages": language_config.get_frontend_source_languages(),
        "target_languages": language_config.get_frontend_target_languages()
    }


@router.get("/frontend/endpoints")
async def get_frontend_endpoints():
    """获取前端可用的翻译接口列表"""
    endpoints = get_registered_endpoints()
    
    # 转换为前端友好的格式
    frontend_endpoints = []
    for code, info in endpoints.items():
        frontend_endpoints.append({
            "code": code,
            "name": info["target_language"],
            "endpoint": info["endpoint"],
            "description": info["description"]
        })
    
    return {
        "single_target_endpoints": frontend_endpoints,
        "total": len(frontend_endpoints)
    }


@router.get("/frontend/test-config")
async def get_test_config():
    """获取前端测试配置"""
    language_config = get_language_config()
    
    # 生成API测试配置
    api_sections = []
    
    # 基础接口
    api_sections.extend([
        {
            "title": "健康检查测试",
            "endpoint": "/health",
            "method": "GET",
            "fields": []
        },
        {
            "title": "语言列表测试",
            "endpoint": "/api/languages",
            "method": "GET",
            "fields": []
        }
    ])
    
    # 通用翻译接口
    source_languages = language_config.get_frontend_source_languages()
    target_languages = language_config.get_frontend_target_languages()
    
    api_sections.append({
        "title": "通用翻译测试",
        "endpoint": "/api/translate",
        "method": "POST",
        "fields": [
            {
                "name": "text",
                "label": "要翻译的文本",
                "type": "textarea",
                "required": True,
                "placeholder": "请输入要翻译的文本"
            },
            {
                "name": "from_lang",
                "label": "源语言",
                "type": "select",
                "options": [{"value": lang["code"], "text": lang["name"]} for lang in source_languages],
                "default": "zh"
            },
            {
                "name": "to_lang",
                "label": "目标语言",
                "type": "select",
                "options": [{"value": lang["code"], "text": lang["name"]} for lang in target_languages],
                "default": "en"
            },
            {
                "name": "font_size",
                "label": "字体大小(可选)",
                "type": "text",
                "placeholder": "如: 24px"
            }
        ]
    })
    
    # 单一目标语言接口
    endpoints = get_registered_endpoints()
    for code, info in endpoints.items():
        api_sections.append({
            "title": f"{info['description']}测试",
            "endpoint": info["endpoint"],
            "method": "POST",
            "fields": [
                {
                    "name": "text",
                    "label": "要翻译的中文文本",
                    "type": "textarea",
                    "required": True,
                    "placeholder": "请输入中文文本"
                },
                {
                    "name": "font_size",
                    "label": "字体大小(可选)",
                    "type": "text",
                    "placeholder": "如: 24px"
                }
            ]
        })
    
    # 批量翻译接口
    api_sections.append({
        "title": "批量翻译测试",
        "endpoint": "/api/batch/translate",
        "method": "POST",
        "fields": [
            {
                "name": "items",
                "label": "翻译项目(JSON数组)",
                "type": "textarea",
                "required": True,
                "placeholder": '["你好", "世界"] 或 [{"text":"你好","id":"1"}]'
            },
            {
                "name": "from_lang",
                "label": "源语言",
                "type": "select",
                "options": [{"value": lang["code"], "text": lang["name"]} for lang in source_languages],
                "default": "zh"
            },
            {
                "name": "to_lang",
                "label": "目标语言",
                "type": "select",
                "options": [{"value": lang["code"], "text": lang["name"]} for lang in target_languages],
                "default": "en"
            },
            {
                "name": "font_size",
                "label": "字体大小(可选)",
                "type": "text",
                "placeholder": "如: 24px"
            }
        ]
    })
    
    return {
        "api_sections": api_sections,
        "total": len(api_sections)
    }


@router.get("/config/validation")
async def validate_config():
    """验证配置文件的有效性"""
    from app.api.dynamic_routes import validate_endpoint_config
    
    validation_result = validate_endpoint_config()
    
    return {
        "config_validation": validation_result,
        "timestamp": __import__("time").time()
    }
