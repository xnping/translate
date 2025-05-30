"""
敏感词管理API接口
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List
from app.models.words_models import (
    WordCreate, WordUpdate, WordResponse, WordListResponse,
    WordSingleResponse, WordBatchCreate, WordBatchDelete, WordBatchResponse,
    WordSearchRequest, WordCheckRequest, WordCheckResponse
)
from app.services.words_service import words_service

router = APIRouter(prefix="/api/words", tags=["敏感词管理"])


@router.post("/", response_model=WordSingleResponse, summary="创建敏感词")
async def create_word(word_data: WordCreate):
    """
    创建新的敏感词

    - **words**: 敏感词内容 (必填，1-255字符)
    """
    try:
        print(f"🔍 接收到创建敏感词请求: {word_data.words}")
        result = await words_service.create_word(word_data)
        print(f"✅ 敏感词创建结果: {result}")

        if result:
            return WordSingleResponse(
                success=True,
                message="敏感词创建成功",
                data=result
            )
        else:
            print("❌ 敏感词创建失败: result为None")
            raise HTTPException(status_code=400, detail="敏感词创建失败")

    except ValueError as e:
        print(f"⚠️ 敏感词创建验证错误: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"❌ 敏感词创建异常: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")


@router.get("/", response_model=WordListResponse, summary="获取敏感词列表")
async def get_words_list(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    keyword: str = Query(None, description="搜索关键词")
):
    """
    获取敏感词列表（支持分页和搜索）
    
    - **page**: 页码 (默认1)
    - **page_size**: 每页数量 (默认10，最大100)
    - **keyword**: 搜索关键词 (可选)
    """
    try:
        words_list, total = await words_service.get_words_list(page, page_size, keyword)
        
        return WordListResponse(
            success=True,
            message="获取敏感词列表成功",
            data=words_list,
            total=total,
            page=page,
            page_size=page_size
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")


@router.get("/{word_id}", response_model=WordSingleResponse, summary="获取单个敏感词")
async def get_word(word_id: int):
    """
    根据ID获取单个敏感词
    
    - **word_id**: 敏感词ID
    """
    try:
        result = await words_service.get_word_by_id(word_id)
        
        if result:
            return WordSingleResponse(
                success=True,
                message="获取敏感词成功",
                data=result
            )
        else:
            raise HTTPException(status_code=404, detail="敏感词不存在")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")


@router.put("/{word_id}", response_model=WordSingleResponse, summary="更新敏感词")
async def update_word(word_id: int, word_data: WordUpdate):
    """
    更新敏感词
    
    - **word_id**: 敏感词ID
    - **words**: 新的敏感词内容 (可选)
    """
    try:
        result = await words_service.update_word(word_id, word_data)
        
        if result:
            return WordSingleResponse(
                success=True,
                message="敏感词更新成功",
                data=result
            )
        else:
            raise HTTPException(status_code=400, detail="敏感词更新失败")
            
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")


@router.delete("/{word_id}", response_model=WordSingleResponse, summary="删除敏感词")
async def delete_word(word_id: int):
    """
    删除敏感词
    
    - **word_id**: 敏感词ID
    """
    try:
        result = await words_service.delete_word(word_id)
        
        if result:
            return WordSingleResponse(
                success=True,
                message="敏感词删除成功",
                data=None
            )
        else:
            raise HTTPException(status_code=400, detail="敏感词删除失败")
            
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")


@router.post("/batch", response_model=WordBatchResponse, summary="批量创建敏感词")
async def batch_create_words(batch_data: WordBatchCreate):
    """
    批量创建敏感词
    
    - **words_list**: 敏感词列表 (必填，至少1个)
    """
    try:
        result = await words_service.batch_create_words(batch_data.words_list)
        
        return WordBatchResponse(
            success=True,
            message=f"批量创建完成: 成功{result['success_count']}个，失败{result['failed_count']}个",
            data=result
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")


@router.post("/batch/delete", response_model=WordBatchResponse, summary="批量删除敏感词")
async def batch_delete_words(batch_data: WordBatchDelete):
    """
    批量删除敏感词

    - **word_ids**: 敏感词ID列表
    """
    try:
        print(f"🔍 批量删除请求: {batch_data.word_ids}")

        if not batch_data.word_ids:
            raise HTTPException(status_code=400, detail="请提供要删除的敏感词ID列表")

        result = await words_service.batch_delete_words(batch_data.word_ids)

        return WordBatchResponse(
            success=True,
            message=f"批量删除完成: 成功{result['success_count']}个，失败{result['failed_count']}个",
            data=result
        )

    except Exception as e:
        print(f"❌ 批量删除失败: {e}")
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")


@router.post("/check", response_model=WordCheckResponse, summary="检测敏感词")
async def check_sensitive_words(check_data: WordCheckRequest):
    """
    检测文本中的敏感词
    
    - **text**: 待检测的文本内容
    """
    try:
        result = await words_service.check_sensitive_words(check_data.text)
        
        return WordCheckResponse(
            success=True,
            message="敏感词检测完成",
            data=result
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")


@router.get("/stats/summary", summary="获取敏感词统计信息")
async def get_words_stats():
    """
    获取敏感词统计信息
    """
    try:
        # 获取总数
        _, total = await words_service.get_words_list(page=1, page_size=1)
        
        return {
            "success": True,
            "message": "获取统计信息成功",
            "data": {
                "total_words": total,
                "database_table": "words",
                "last_updated": "实时数据"
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")
