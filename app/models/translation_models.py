"""
翻译相关的数据模型
"""

from typing import Optional
from pydantic import BaseModel, Field


class TranslationRequest(BaseModel):
    """翻译请求模型"""
    path: str = Field(..., description="路径（域名+后缀）")
    html_body: str = Field(..., description="HTML整个页面的body")
    source_language: str = Field(..., description="源语言")
    target_language: str = Field(..., description="目标语言")
    untranslatable_tags: Optional[str] = Field(None, description="翻译不到的标签")
    no_translate_tags: Optional[str] = Field(None, description="不需要翻译的标签")


class TranslationResponse(BaseModel):
    """翻译响应模型"""
    success: bool = Field(True, description="处理是否成功")
    message: str = Field("处理完成", description="处理消息")
    data: Optional[dict] = Field(None, description="处理结果数据")
