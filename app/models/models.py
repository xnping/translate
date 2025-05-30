"""
数据库模型和API模型
"""

from typing import Optional
from pydantic import BaseModel, Field
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.config.config import Base


# ==================== 数据库模型 ====================

class TypeModel(Base):
    """Type表模型"""
    __tablename__ = "type"

    id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(String(255), nullable=True)
    class_ = Column("class", String(255), nullable=True)

    # 关联关系
    labels = relationship("LabelModel", back_populates="type_rel")


class LabelModel(Base):
    """Label表模型"""
    __tablename__ = "label"

    id = Column(Integer, primary_key=True, autoincrement=True)
    label = Column(String(255), nullable=True)
    type = Column(Integer, ForeignKey("type.id"), nullable=True)

    # 关联关系
    type_rel = relationship("TypeModel", back_populates="labels")


# ==================== API请求模型 ====================

class TypeCreate(BaseModel):
    """创建Type的请求模型"""
    type: Optional[str] = Field(None, description="类型名称")
    class_: Optional[str] = Field(None, alias="class", description="类别")


class TypeUpdate(BaseModel):
    """更新Type的请求模型"""
    type: Optional[str] = Field(None, description="类型名称")
    class_: Optional[str] = Field(None, alias="class", description="类别")


class LabelCreate(BaseModel):
    """创建Label的请求模型"""
    label: Optional[str] = Field(None, description="标签名称")
    type: Optional[int] = Field(None, description="类型ID")


class LabelUpdate(BaseModel):
    """更新Label的请求模型"""
    label: Optional[str] = Field(None, description="标签名称")
    type: Optional[int] = Field(None, description="类型ID")


# ==================== API响应模型 ====================

class TypeResponse(BaseModel):
    """Type响应模型"""
    id: int
    type: Optional[str] = None
    class_: Optional[str] = Field(None, alias="class")

    class Config:
        from_attributes = True
        populate_by_name = True


class LabelResponse(BaseModel):
    """Label响应模型"""
    id: int
    label: Optional[str] = None
    type: Optional[int] = None

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    """通用消息响应"""
    message: str
    success: bool = True
