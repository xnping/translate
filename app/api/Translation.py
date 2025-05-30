"""
翻译API接口 - 重构版
"""

from fastapi import APIRouter, HTTPException
from app.models.translation_models import TranslationRequest, TranslationResponse
from app.services.baidu_translation_service import baidu_translation_service
from app.services.dom_replacement_service import dom_replacement_service

router = APIRouter(prefix="/api", tags=["翻译"])


@router.post("/translate", response_model=TranslationResponse, summary="终极翻译接口 - 100%替换率")
async def translate_ultimate(request: TranslationRequest):
    """
    终极翻译接口 - 追求100%替换率

    使用DOM解析 + 多重替换策略，确保最高的替换成功率
    """

    # 1. 验证百度翻译服务
    if baidu_translation_service is None:
        raise HTTPException(
            status_code=500,
            detail="百度翻译服务初始化失败，请检查.env配置"
        )

    # 2. 接收并打印所有参数
    print("=" * 80)
    print("🚀 终极翻译接口收到请求！")
    print("=" * 80)
    print(f"📍 路径: {request.path}")
    print(f"📝 HTML Body 长度: {len(request.html_body)} 字符")
    print(f"🌐 源语言: {request.source_language}")
    print(f"🎯 目标语言: {request.target_language}")

    # 3. 使用DOM解析提取中文文本
    print("-" * 40)
    print("🔍 使用DOM解析提取中文文本...")

    dom_data = dom_replacement_service.extract_all_chinese_with_dom(request.html_body)

    # 4. 打印DOM提取结果
    print("✅ DOM提取完成！")
    print(f"📊 文本节点数量: {dom_data['statistics']['total_text_nodes']}")
    print(f"📝 中文文本片段数量: {dom_data['statistics']['total_chinese_segments']}")
    print(f"🔤 唯一中文文本数量: {dom_data['statistics']['unique_chinese_texts']}")

    # 5. 批量翻译所有中文文本
    print("-" * 40)
    print("🌐 开始调用百度翻译API...")

    all_chinese_texts = dom_data['chinese_texts']
    print(f"📊 需要翻译的文本数量: {len(all_chinese_texts)}")

    # 批量翻译
    translation_results = baidu_translation_service.batch_translate(
        all_chinese_texts,
        request.source_language,
        request.target_language
    )

    # 6. 创建翻译映射表
    print("-" * 40)
    print("📋 创建翻译映射表...")
    translation_map = dom_replacement_service.create_translation_map(translation_results)

    # 7. 使用终极替换方案
    print("-" * 40)
    print("🚀 启动终极替换方案...")

    translated_html_body, ultimate_stats = dom_replacement_service.ultimate_replace_chinese(
        request.html_body,
        translation_map
    )

    # 8. 打印最终统计
    print("-" * 40)
    print("🎉 终极翻译结果统计:")
    print(f"  原始中文字符数: {ultimate_stats['original_chinese_count']}")
    print(f"  剩余中文字符数: {ultimate_stats['remaining_chinese_count']}")
    print(f"  已替换字符数: {ultimate_stats['replaced_count']}")
    print(f"  替换率: {ultimate_stats['replacement_rate']:.2f}%")

    if ultimate_stats['remaining_texts']:
        print(f"  剩余文本: {ultimate_stats['remaining_texts'][:5]}")

    print("=" * 80)

    return TranslationResponse(
        success=True,
        message=f"🎉 终极翻译完成！替换率: {ultimate_stats['replacement_rate']:.2f}%",
        data={
            "request_info": {
                "path": request.path,
                "html_length": len(request.html_body),
                "source_language": request.source_language,
                "target_language": request.target_language,
                "untranslatable_tags": request.untranslatable_tags,
                "no_translate_tags": request.no_translate_tags
            },
            "dom_extraction_results": dom_data['statistics'],
            "translation_results": translation_results,
            "ultimate_replacement_results": {
                "original_html_body": request.html_body,
                "translated_html_body": translated_html_body,
                "replacement_statistics": ultimate_stats,
                "translation_map": translation_map
            }
        }
    )
