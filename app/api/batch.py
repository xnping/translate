"""
批量翻译相关的API路由
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Union

from app.models.translation import (
    BatchTranslationRequest,
    BatchTranslationResponse,
    BatchItem
)
from app.core.dependencies import get_translator_dependency
from app.services.translation_service import TranslationService

router = APIRouter()


def _prepare_batch_items(items: List[Union[BatchItem, str]]) -> List[dict]:
    """准备批量翻译项目"""
    prepared_items = []
    for i, item in enumerate(items):
        if isinstance(item, str):
            prepared_items.append({
                "text": item,
                "id": str(i)
            })
        else:
            prepared_items.append({
                "text": item.text,
                "id": item.id if item.id else str(i)
            })
    return prepared_items


@router.post("/batch/translate", response_model=BatchTranslationResponse)
async def batch_translate(
    request: BatchTranslationRequest,
    translator: TranslationService = Depends(get_translator_dependency)
):
    """批量翻译接口"""
    try:
        # 准备批量翻译项目
        prepared_items = _prepare_batch_items(request.items)
        
        # 执行批量翻译
        result = await translator.translate_batch(
            items=prepared_items,
            from_lang=request.from_lang,
            to_lang=request.to_lang,
            use_cache=True,
            font_size=request.font_size
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量翻译失败: {str(e)}")


# 批量单一目标语言翻译接口
@router.post("/batch/translate_to_english", response_model=BatchTranslationResponse)
async def batch_translate_to_english(
    request: BatchTranslationRequest,
    translator: TranslationService = Depends(get_translator_dependency)
):
    """批量翻译到英语"""
    try:
        prepared_items = _prepare_batch_items(request.items)
        result = await translator.translate_batch(
            items=prepared_items,
            from_lang="zh",
            to_lang="en",
            use_cache=True,
            font_size=request.font_size
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量翻译失败: {str(e)}")


@router.post("/batch/translate_to_thai", response_model=BatchTranslationResponse)
async def batch_translate_to_thai(
    request: BatchTranslationRequest,
    translator: TranslationService = Depends(get_translator_dependency)
):
    """批量翻译到泰语"""
    try:
        prepared_items = _prepare_batch_items(request.items)
        result = await translator.translate_batch(
            items=prepared_items,
            from_lang="zh",
            to_lang="th",
            use_cache=True,
            font_size=request.font_size
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量翻译失败: {str(e)}")


@router.post("/batch/translate_to_vietnamese", response_model=BatchTranslationResponse)
async def batch_translate_to_vietnamese(
    request: BatchTranslationRequest,
    translator: TranslationService = Depends(get_translator_dependency)
):
    """批量翻译到越南语"""
    try:
        prepared_items = _prepare_batch_items(request.items)
        result = await translator.translate_batch(
            items=prepared_items,
            from_lang="zh",
            to_lang="vie",
            use_cache=True,
            font_size=request.font_size
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量翻译失败: {str(e)}")


@router.post("/batch/translate_to_indonesian", response_model=BatchTranslationResponse)
async def batch_translate_to_indonesian(
    request: BatchTranslationRequest,
    translator: TranslationService = Depends(get_translator_dependency)
):
    """批量翻译到印尼语"""
    try:
        prepared_items = _prepare_batch_items(request.items)
        result = await translator.translate_batch(
            items=prepared_items,
            from_lang="zh",
            to_lang="id",
            use_cache=True,
            font_size=request.font_size
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量翻译失败: {str(e)}")


@router.post("/batch/translate_to_malay", response_model=BatchTranslationResponse)
async def batch_translate_to_malay(
    request: BatchTranslationRequest,
    translator: TranslationService = Depends(get_translator_dependency)
):
    """批量翻译到马来语"""
    try:
        prepared_items = _prepare_batch_items(request.items)
        result = await translator.translate_batch(
            items=prepared_items,
            from_lang="zh",
            to_lang="ms",
            use_cache=True,
            font_size=request.font_size
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量翻译失败: {str(e)}")


@router.post("/batch/translate_to_filipino", response_model=BatchTranslationResponse)
async def batch_translate_to_filipino(
    request: BatchTranslationRequest,
    translator: TranslationService = Depends(get_translator_dependency)
):
    """批量翻译到菲律宾语"""
    try:
        prepared_items = _prepare_batch_items(request.items)
        result = await translator.translate_batch(
            items=prepared_items,
            from_lang="zh",
            to_lang="fil",
            use_cache=True,
            font_size=request.font_size
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量翻译失败: {str(e)}")


@router.post("/batch/translate_to_burmese", response_model=BatchTranslationResponse)
async def batch_translate_to_burmese(
    request: BatchTranslationRequest,
    translator: TranslationService = Depends(get_translator_dependency)
):
    """批量翻译到缅甸语"""
    try:
        prepared_items = _prepare_batch_items(request.items)
        result = await translator.translate_batch(
            items=prepared_items,
            from_lang="zh",
            to_lang="my",
            use_cache=True,
            font_size=request.font_size
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量翻译失败: {str(e)}")


@router.post("/batch/translate_to_khmer", response_model=BatchTranslationResponse)
async def batch_translate_to_khmer(
    request: BatchTranslationRequest,
    translator: TranslationService = Depends(get_translator_dependency)
):
    """批量翻译到高棉语"""
    try:
        prepared_items = _prepare_batch_items(request.items)
        result = await translator.translate_batch(
            items=prepared_items,
            from_lang="zh",
            to_lang="km",
            use_cache=True,
            font_size=request.font_size
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量翻译失败: {str(e)}")


@router.post("/batch/translate_to_lao", response_model=BatchTranslationResponse)
async def batch_translate_to_lao(
    request: BatchTranslationRequest,
    translator: TranslationService = Depends(get_translator_dependency)
):
    """批量翻译到老挝语"""
    try:
        prepared_items = _prepare_batch_items(request.items)
        result = await translator.translate_batch(
            items=prepared_items,
            from_lang="zh",
            to_lang="lao",
            use_cache=True,
            font_size=request.font_size
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量翻译失败: {str(e)}")


@router.post("/batch/translate_to_tamil", response_model=BatchTranslationResponse)
async def batch_translate_to_tamil(
    request: BatchTranslationRequest,
    translator: TranslationService = Depends(get_translator_dependency)
):
    """批量翻译到泰米尔语"""
    try:
        prepared_items = _prepare_batch_items(request.items)
        result = await translator.translate_batch(
            items=prepared_items,
            from_lang="zh",
            to_lang="ta",
            use_cache=True,
            font_size=request.font_size
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量翻译失败: {str(e)}")
