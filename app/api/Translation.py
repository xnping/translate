"""
翻译API接口 - 重构版
"""

from fastapi import APIRouter, HTTPException
from app.models.translation_models import TranslationRequest, TranslationResponse
from app.services.baidu_translation_service import baidu_translation_service
from app.services.dom_replacement_service import dom_replacement_service
from app.services.large_html_processor import large_html_processor

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

    # 3. 检测是否为大型HTML（超过10万字符）
    html_length = len(request.html_body)
    is_large_html = html_length > 100000

    if is_large_html:
        print("🔥 检测到大型HTML，启用专用处理模式...")

        # 使用大型HTML终极DOM处理器 - 100%提取和100%替换
        translated_html_body, large_stats = await large_html_processor.process_large_html_with_ultimate_dom(
            request.html_body,
            dom_replacement_service,  # 传入DOM服务
            baidu_translation_service,
            request.source_language,
            request.target_language
        )

        # 打印大型HTML终极DOM处理统计
        print("-" * 40)
        print("🎉 大型HTML终极DOM处理结果:")
        print(f"  处理模式: {large_stats['processing_mode']}")
        print(f"  总耗时: {large_stats['processing_time']}秒")
        print(f"  翻译耗时: {large_stats['translation_duration']}秒")
        print(f"  翻译速度: {large_stats['unique_texts']/large_stats['translation_duration']:.1f} 文本/秒")
        print(f"  处理块数: {large_stats['chunks_processed']}")
        print(f"  文本总数: {large_stats['total_texts']}")
        print(f"  唯一文本: {large_stats['unique_texts']}")
        print(f"  翻译成功: {large_stats['translation_success']}")
        print(f"  翻译失败: {large_stats['translation_failed']}")
        print(f"  终极替换率: {large_stats['replacement_rate']:.2f}%")
        print(f"  内存峰值: {large_stats['memory_peak_mb']}MB")
        if large_stats['remaining_texts']:
            print(f"  剩余文本: {large_stats['remaining_texts'][:3]}")
        print("=" * 80)

        return TranslationResponse(
            success=True,
            message=f"🎉 大型HTML翻译完成！耗时: {large_stats['processing_time']}秒，替换率: {large_stats['replacement_rate']:.2f}%",
            data={
                "request_info": {
                    "path": request.path,
                    "html_length": len(request.html_body),
                    "source_language": request.source_language,
                    "target_language": request.target_language,
                    "processing_mode": "large_html",
                    "untranslatable_tags": request.untranslatable_tags,
                    "no_translate_tags": request.no_translate_tags
                },
                "large_html_results": {
                    "translated_html_body": translated_html_body,
                    "processing_statistics": large_stats
                }
            }
        )

    else:
        print("📝 标准HTML大小，使用常规处理模式...")

        # 4. 使用DOM解析提取中文文本
        print("-" * 40)
        print("🔍 使用DOM解析提取中文文本...")

        dom_data = dom_replacement_service.extract_all_chinese_with_dom(request.html_body)

        # 5. 打印DOM提取结果
        print("✅ DOM提取完成！")
        print(f"📊 文本节点数量: {dom_data['statistics']['total_text_nodes']}")
        print(f"📝 中文文本片段数量: {dom_data['statistics']['total_chinese_segments']}")
        print(f"🔤 唯一中文文本数量: {dom_data['statistics']['unique_chinese_texts']}")

        # 6. 高速并发翻译所有中文文本
        print("-" * 40)
        print("⚡ 开始高速并发翻译...")

        all_chinese_texts = dom_data['chinese_texts']
        print(f"📊 需要翻译的文本数量: {len(all_chinese_texts)}")

        # 使用高速并发翻译
        import asyncio
        translation_results = await baidu_translation_service.concurrent_batch_translate(
            all_chinese_texts,
            request.source_language,
            request.target_language,
            max_concurrent=15  # 并发数，可以根据需要调整
        )

        # 7. 创建翻译映射表
        print("-" * 40)
        print("📋 创建翻译映射表...")
        translation_map = dom_replacement_service.create_translation_map(translation_results)

        # 8. 使用终极替换方案
        print("-" * 40)
        print("🚀 启动终极替换方案...")

        translated_html_body, ultimate_stats = dom_replacement_service.ultimate_replace_chinese(
            request.html_body,
            translation_map
        )

        # 9. 打印最终统计
        print("-" * 40)
        print("🎉 高速翻译结果统计:")
        print(f"  翻译耗时: {translation_results['duration']}秒")
        print(f"  翻译速度: {translation_results['unique_count']/translation_results['duration']:.1f} 文本/秒")
        print(f"  翻译成功: {translation_results['success_count']}/{translation_results['unique_count']}")
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
                    "processing_mode": "standard",
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
