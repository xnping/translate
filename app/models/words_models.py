"""
敏感词数据模型
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class WordBase(BaseModel):
    """敏感词基础模型"""
    words: str = Field(..., min_length=1, max_length=255, description="敏感词内容")


class WordCreate(WordBase):
    """创建敏感词请求模型"""
    pass


class WordUpdate(BaseModel):
    """更新敏感词请求模型"""
    words: Optional[str] = Field(None, min_length=1, max_length=255, description="敏感词内容")


class WordResponse(WordBase):
    """敏感词响应模型"""
    id: int = Field(..., description="敏感词ID")
    
    class Config:
        from_attributes = True


class WordListResponse(BaseModel):
    """敏感词列表响应模型"""
    success: bool = Field(True, description="请求是否成功")
    message: str = Field("操作成功", description="响应消息")
    data: List[WordResponse] = Field([], description="敏感词列表")
    total: int = Field(0, description="总数量")
    page: int = Field(1, description="当前页码")
    page_size: int = Field(10, description="每页数量")


class WordSingleResponse(BaseModel):
    """单个敏感词响应模型"""
    success: bool = Field(True, description="请求是否成功")
    message: str = Field("操作成功", description="响应消息")
    data: Optional[WordResponse] = Field(None, description="敏感词数据")


class WordBatchCreate(BaseModel):
    """批量创建敏感词请求模型"""
    words_list: List[str] = Field(..., min_items=1, description="敏感词列表")


class WordBatchDelete(BaseModel):
    """批量删除敏感词请求模型"""
    word_ids: List[int] = Field(..., min_items=1, description="敏感词ID列表")


class WordBatchResponse(BaseModel):
    """批量操作响应模型"""
    success: bool = Field(True, description="请求是否成功")
    message: str = Field("操作成功", description="响应消息")
    data: dict = Field({}, description="操作结果")


class WordSearchRequest(BaseModel):
    """敏感词搜索请求模型"""
    keyword: Optional[str] = Field(None, description="搜索关键词")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(10, ge=1, le=100, description="每页数量")


class WordCheckRequest(BaseModel):
    """敏感词检测请求模型"""
    text: str = Field(..., min_length=1, description="待检测文本")


class WordCheckResponse(BaseModel):
    """敏感词检测响应模型"""
    success: bool = Field(True, description="请求是否成功")
    message: str = Field("检测完成", description="响应消息")
    data: dict = Field({}, description="检测结果")
