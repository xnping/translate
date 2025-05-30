"""
翻译API接口
"""

import re
from typing import List, Dict
from fastapi import APIRouter
from app.models.translation_models import TranslationRequest, TranslationResponse

router = APIRouter(prefix="/api", tags=["翻译"])


def extract_html_tags_and_chinese(html_body: str) -> Dict:
    """
    从HTML body中提取所有标签和中文文本
    """
    result = {
        "all_tags": [],           # 所有标签信息
        "chinese_texts": [],      # 所有中文文本
        "tag_chinese_map": {},    # 标签与中文的映射关系
        "statistics": {}          # 统计信息
    }

    # 1. 提取所有HTML标签及其内容
    # 匹配开始标签到结束标签的完整内容
    tag_pattern = r'<([a-zA-Z][a-zA-Z0-9]*)\b[^>]*>(.*?)</\1>'
    tag_matches = re.findall(tag_pattern, html_body, re.DOTALL)

    # 2. 中文字符正则表达式
    chinese_pattern = r'[\u4e00-\u9fff]+'

    tag_index = 0
    for tag_name, tag_content in tag_matches:
        tag_index += 1

        # 清理标签内容，移除嵌套的HTML标签
        clean_content = re.sub(r'<[^>]+>', '', tag_content)
        clean_content = clean_content.strip()

        # 提取中文文本
        chinese_texts = re.findall(chinese_pattern, clean_content)

        if chinese_texts:  # 只保存包含中文的标签
            tag_info = {
                "index": tag_index,
                "tag_name": tag_name,
                "original_content": tag_content[:200] + "..." if len(tag_content) > 200 else tag_content,
                "clean_content": clean_content,
                "chinese_texts": chinese_texts,
                "chinese_count": len(chinese_texts)
            }

            result["all_tags"].append(tag_info)
            result["chinese_texts"].extend(chinese_texts)
            result["tag_chinese_map"][f"{tag_name}_{tag_index}"] = chinese_texts

    # 3. 额外提取所有文本节点中的中文（不在标签内的）
    # 移除所有HTML标签，只保留文本
    text_only = re.sub(r'<[^>]+>', ' ', html_body)
    # 清理多余空白
    text_only = re.sub(r'\s+', ' ', text_only).strip()
    # 提取所有中文
    all_chinese_in_text = re.findall(chinese_pattern, text_only)

    # 4. 统计信息
    result["statistics"] = {
        "total_tags_with_chinese": len(result["all_tags"]),
        "total_chinese_segments": len(result["chinese_texts"]),
        "total_chinese_in_page": len(all_chinese_in_text),
        "unique_chinese_texts": len(set(result["chinese_texts"])),
        "tag_types": list(set([tag["tag_name"] for tag in result["all_tags"]]))
    }

    return result


@router.post("/translate", response_model=TranslationResponse, summary="翻译接口")
async def translate(request: TranslationRequest):
    """
    翻译接口

    参数说明：
    - path: 路径（域名+后缀）
    - html_body: HTML整个页面的body
    - source_language: 源语言
    - target_language: 目标语言
    - untranslatable_tags: 翻译不到的标签（可选）
    - no_translate_tags: 不需要翻译的标签（可选）
    """

    # 接收并打印所有参数
    print("=" * 80)
    print("🔥 翻译接口收到请求！")
    print("=" * 80)
    print(f"📍 路径: {request.path}")
    print(f"📝 HTML Body 长度: {len(request.html_body)} 字符")
    print(f"🌐 源语言: {request.source_language}")
    print(f"🎯 目标语言: {request.target_language}")
    print(f"❌ 翻译不到的标签: {request.untranslatable_tags}")
    print(f"🚫 不需要翻译的标签: {request.no_translate_tags}")
    print("=" * 80)

    return TranslationResponse(
        success=True,
        message="接口参数接收成功！",
        data={
            "path": request.path,
            "html_length": len(request.html_body),
            "source_language": request.source_language,
            "target_language": request.target_language,
            "untranslatable_tags": request.untranslatable_tags,
            "no_translate_tags": request.no_translate_tags
        }
    )
