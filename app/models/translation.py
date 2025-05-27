"""
翻译相关的数据模型
"""

from typing import List, Optional, Union, Any
from pydantic import BaseModel, Field
try:
    from pydantic import validator
except ImportError:
    from pydantic import field_validator as validator


class TranslationRequest(BaseModel):
    """翻译请求模型"""
    text: str = Field(..., min_length=1, max_length=5000, description="要翻译的文本")
    from_lang: str = Field(default="auto", description="源语言代码")
    to_lang: str = Field(default="zh", description="目标语言代码")
    font_size: Optional[str] = Field(None, description="建议字体大小")

    @validator('text')
    def validate_text(cls, v):
        if not v or not v.strip():
            raise ValueError('翻译文本不能为空')
        return v.strip()


class BatchItem(BaseModel):
    """批量翻译项目模型"""
    text: str = Field(..., min_length=1, description="要翻译的文本")
    id: Optional[str] = Field(None, description="项目ID")


class BatchTranslationRequest(BaseModel):
    """批量翻译请求模型"""
    items: List[Union[BatchItem, str]] = Field(..., min_items=1, max_items=50, description="翻译项目列表")
    from_lang: str = Field(default="auto", description="源语言代码")
    to_lang: str = Field(default="zh", description="目标语言代码")
    font_size: Optional[str] = Field(None, description="建议字体大小")


class SingleTargetRequest(BaseModel):
    """单一目标语言翻译请求模型"""
    text: str = Field(..., min_length=1, max_length=5000, description="要翻译的中文文本")
    font_size: Optional[str] = Field(None, description="建议字体大小")


class TranslationResult(BaseModel):
    """翻译结果模型"""
    src: str = Field(..., description="原文")
    dst: str = Field(..., description="译文")


class TranslationResponse(BaseModel):
    """翻译响应模型"""
    trans_result: List[TranslationResult] = Field(..., description="翻译结果列表")
    font_size: Optional[str] = Field(None, description="建议字体大小")
    from_lang: Optional[str] = Field(None, description="检测到的源语言", alias="from")
    to_lang: Optional[str] = Field(None, description="目标语言", alias="to")

    class Config:
        populate_by_name = True


class BatchTranslationResponse(BaseModel):
    """批量翻译响应模型"""
    results: List[dict] = Field(..., description="翻译结果列表")
    total: int = Field(..., description="总数量")
    success: int = Field(..., description="成功数量")
    font_size: Optional[str] = Field(None, description="建议字体大小")


class HealthResponse(BaseModel):
    """健康检查响应模型"""
    status: str = Field(..., description="服务状态")
    version: str = Field(..., description="版本号")
    cache: dict = Field(..., description="缓存统计")
    timestamp: float = Field(..., description="时间戳")


class PerformanceStats(BaseModel):
    """性能统计模型"""
    cache_stats: dict = Field(..., description="缓存统计")
    status: str = Field(..., description="状态")
    timestamp: float = Field(..., description="时间戳")


class ErrorResponse(BaseModel):
    """错误响应模型"""
    error: str = Field(..., description="错误信息")
    code: Optional[str] = Field(None, description="错误代码")
    details: Optional[Any] = Field(None, description="详细信息")
