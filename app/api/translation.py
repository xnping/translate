"""
翻译相关的API路由
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


# 单一目标语言翻译接口
@router.post("/translate_to_english", response_model=TranslationResponse)
async def translate_to_english(
    request: SingleTargetRequest,
    merger: RequestMerger = Depends(get_merger_dependency)
):
    """翻译到英语"""
    try:
        result = await merger.submit_request(
            text=request.text,
            from_lang="zh",
            to_lang="en",
            font_size=request.font_size
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"翻译失败: {str(e)}")


@router.post("/translate_to_thai", response_model=TranslationResponse)
async def translate_to_thai(
    request: SingleTargetRequest,
    merger: RequestMerger = Depends(get_merger_dependency)
):
    """翻译到泰语"""
    try:
        result = await merger.submit_request(
            text=request.text,
            from_lang="zh",
            to_lang="th",
            font_size=request.font_size
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"翻译失败: {str(e)}")


@router.post("/translate_to_vietnamese", response_model=TranslationResponse)
async def translate_to_vietnamese(
    request: SingleTargetRequest,
    merger: RequestMerger = Depends(get_merger_dependency)
):
    """翻译到越南语"""
    try:
        result = await merger.submit_request(
            text=request.text,
            from_lang="zh",
            to_lang="vie",
            font_size=request.font_size
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"翻译失败: {str(e)}")


@router.post("/translate_to_indonesian", response_model=TranslationResponse)
async def translate_to_indonesian(
    request: SingleTargetRequest,
    merger: RequestMerger = Depends(get_merger_dependency)
):
    """翻译到印尼语"""
    try:
        result = await merger.submit_request(
            text=request.text,
            from_lang="zh",
            to_lang="id",
            font_size=request.font_size
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"翻译失败: {str(e)}")


@router.post("/translate_to_malay", response_model=TranslationResponse)
async def translate_to_malay(
    request: SingleTargetRequest,
    merger: RequestMerger = Depends(get_merger_dependency)
):
    """翻译到马来语"""
    try:
        result = await merger.submit_request(
            text=request.text,
            from_lang="zh",
            to_lang="may",
            font_size=request.font_size
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"翻译失败: {str(e)}")


@router.post("/translate_to_filipino", response_model=TranslationResponse)
async def translate_to_filipino(
    request: SingleTargetRequest,
    merger: RequestMerger = Depends(get_merger_dependency)
):
    """翻译到菲律宾语"""
    try:
        result = await merger.submit_request(
            text=request.text,
            from_lang="zh",
            to_lang="fil",
            font_size=request.font_size
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"翻译失败: {str(e)}")


@router.post("/translate_to_burmese", response_model=TranslationResponse)
async def translate_to_burmese(
    request: SingleTargetRequest,
    merger: RequestMerger = Depends(get_merger_dependency)
):
    """翻译到缅甸语"""
    try:
        result = await merger.submit_request(
            text=request.text,
            from_lang="zh",
            to_lang="bur",
            font_size=request.font_size
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"翻译失败: {str(e)}")


@router.post("/translate_to_khmer", response_model=TranslationResponse)
async def translate_to_khmer(
    request: SingleTargetRequest,
    merger: RequestMerger = Depends(get_merger_dependency)
):
    """翻译到高棉语"""
    try:
        result = await merger.submit_request(
            text=request.text,
            from_lang="zh",
            to_lang="hkm",
            font_size=request.font_size
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"翻译失败: {str(e)}")


@router.post("/translate_to_lao", response_model=TranslationResponse)
async def translate_to_lao(
    request: SingleTargetRequest,
    merger: RequestMerger = Depends(get_merger_dependency)
):
    """翻译到老挝语"""
    try:
        result = await merger.submit_request(
            text=request.text,
            from_lang="zh",
            to_lang="lao",
            font_size=request.font_size
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"翻译失败: {str(e)}")


@router.post("/translate_to_tamil", response_model=TranslationResponse)
async def translate_to_tamil(
    request: SingleTargetRequest,
    merger: RequestMerger = Depends(get_merger_dependency)
):
    """翻译到泰米尔语"""
    try:
        result = await merger.submit_request(
            text=request.text,
            from_lang="zh",
            to_lang="tam",
            font_size=request.font_size
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"翻译失败: {str(e)}")
