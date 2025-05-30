"""
Label表的基础CRUD接口
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config.config import get_db
from app.models.models import LabelModel, LabelCreate, LabelUpdate, LabelResponse, MessageResponse

router = APIRouter(prefix="/api/labels", tags=["Label管理"])


@router.post("/", response_model=LabelResponse, summary="创建Label")
async def create_label(
    label_data: LabelCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建新的Label记录"""
    try:
        db_label = LabelModel(
            label=label_data.label,
            type=label_data.type
        )
        
        db.add(db_label)
        await db.commit()
        await db.refresh(db_label)
        
        return LabelResponse.from_orm(db_label)
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"创建失败: {str(e)}")


@router.get("/", response_model=List[LabelResponse], summary="获取Label列表")
async def get_labels(db: AsyncSession = Depends(get_db)):
    """获取所有Label记录"""
    try:
        query = select(LabelModel)
        result = await db.execute(query)
        labels = result.scalars().all()
        
        return [LabelResponse.from_orm(label) for label in labels]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.put("/{label_id}", response_model=LabelResponse, summary="更新Label")
async def update_label(
    label_id: int,
    label_data: LabelUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新Label记录"""
    try:
        query = select(LabelModel).where(LabelModel.id == label_id)
        result = await db.execute(query)
        label = result.scalar_one_or_none()
        
        if not label:
            raise HTTPException(status_code=404, detail="Label不存在")
        
        if label_data.label is not None:
            label.label = label_data.label
        if label_data.type is not None:
            label.type = label_data.type
        
        await db.commit()
        await db.refresh(label)
        
        return LabelResponse.from_orm(label)
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")


@router.delete("/{label_id}", response_model=MessageResponse, summary="删除Label")
async def delete_label(
    label_id: int,
    db: AsyncSession = Depends(get_db)
):
    """删除Label记录"""
    try:
        query = select(LabelModel).where(LabelModel.id == label_id)
        result = await db.execute(query)
        label = result.scalar_one_or_none()
        
        if not label:
            raise HTTPException(status_code=404, detail="Label不存在")
        
        await db.delete(label)
        await db.commit()
        
        return MessageResponse(message=f"Label ID {label_id} 删除成功")
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")
