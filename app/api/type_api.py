"""
Type表的基础CRUD接口
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config.config import get_db
from app.models.models import TypeModel, TypeCreate, TypeUpdate, TypeResponse, MessageResponse

router = APIRouter(prefix="/api/types", tags=["Type管理"])


@router.post("/", response_model=TypeResponse, summary="创建Type")
async def create_type(
    type_data: TypeCreate,
    db: AsyncSession = Depends(get_db)
):
    """创建新的Type记录"""
    try:
        db_type = TypeModel(
            type=type_data.type,
            class_=type_data.class_
        )
        
        db.add(db_type)
        await db.commit()
        await db.refresh(db_type)
        
        return TypeResponse.from_orm(db_type)
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"创建失败: {str(e)}")


@router.get("/", response_model=List[TypeResponse], summary="获取Type列表")
async def get_types(db: AsyncSession = Depends(get_db)):
    """获取所有Type记录"""
    try:
        query = select(TypeModel)
        result = await db.execute(query)
        types = result.scalars().all()
        
        return [TypeResponse.from_orm(type_obj) for type_obj in types]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.put("/{type_id}", response_model=TypeResponse, summary="更新Type")
async def update_type(
    type_id: int,
    type_data: TypeUpdate,
    db: AsyncSession = Depends(get_db)
):
    """更新Type记录"""
    try:
        query = select(TypeModel).where(TypeModel.id == type_id)
        result = await db.execute(query)
        type_obj = result.scalar_one_or_none()
        
        if not type_obj:
            raise HTTPException(status_code=404, detail="Type不存在")
        
        if type_data.type is not None:
            type_obj.type = type_data.type
        if type_data.class_ is not None:
            type_obj.class_ = type_data.class_
        
        await db.commit()
        await db.refresh(type_obj)
        
        return TypeResponse.from_orm(type_obj)
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")


@router.delete("/{type_id}", response_model=MessageResponse, summary="删除Type")
async def delete_type(
    type_id: int,
    db: AsyncSession = Depends(get_db)
):
    """删除Type记录"""
    try:
        query = select(TypeModel).where(TypeModel.id == type_id)
        result = await db.execute(query)
        type_obj = result.scalar_one_or_none()
        
        if not type_obj:
            raise HTTPException(status_code=404, detail="Type不存在")
        
        await db.delete(type_obj)
        await db.commit()
        
        return MessageResponse(message=f"Type ID {type_id} 删除成功")
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")
