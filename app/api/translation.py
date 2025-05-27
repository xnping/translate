"""
翻译相关的API路由
重构后使用配置驱动的动态路由生成
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

from app.models.translation import (
    TranslationRequest,
    TranslationResponse,
    SingleTargetRequest
)
from app.core.dependencies import (
    get_translator_dependency,
    get_merger_dependency,
    get_cache_dependency
)
from app.services.translation_service import TranslationService
from app.services.request_merger import RequestMerger
from app.services.cache_service import CacheService
from app.core.config import get_settings
from app.api.dynamic_routes import register_single_target_routes

router = APIRouter()


@router.get("/languages")
async def get_supported_languages():
    """获取支持的语言列表"""
    settings = get_settings()
    return {
        "languages": settings.get_supported_languages(),
        "total": len(settings.get_supported_languages())
    }


@router.post("/translate", response_model=TranslationResponse)
async def translate_text(
    request: TranslationRequest,
    merger: RequestMerger = Depends(get_merger_dependency)
):
    """通用翻译接口"""
    try:
        # 使用请求合并器处理翻译
        result = await merger.submit_request(
            text=request.text,
            from_lang=request.from_lang,
            to_lang=request.to_lang,
            font_size=request.font_size
        )

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"翻译失败: {str(e)}")


@router.post("/translate_optimized", response_model=TranslationResponse)
async def translate_optimized(
    request: TranslationRequest,
    translator: TranslationService = Depends(get_translator_dependency)
):
    """优化翻译接口（直接调用，不使用请求合并）"""
    try:
        result = await translator.translate_single(
            text=request.text,
            from_lang=request.from_lang,
            to_lang=request.to_lang,
            use_cache=True,
            font_size=request.font_size
        )

        if result.success:
            return result.data
        else:
            raise HTTPException(status_code=400, detail=result.error)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"翻译失败: {str(e)}")


# 动态注册单一目标语言翻译接口
# 所有接口都通过配置文件自动生成，避免重复代码
register_single_target_routes(router)
