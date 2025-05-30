"""
翻译API接口 - 重构版
"""

from fastapi import APIRouter, HTTPException
from app.models.translation_models import TranslationRequest, TranslationResponse
from app.services.html_parser_service import html_parser_service
from app.services.baidu_translation_service import baidu_translation_service

router = APIRouter(prefix="/api", tags=["翻译"])


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
    
    # 1. 验证百度翻译服务
    if baidu_translation_service is None:
        raise HTTPException(
            status_code=500, 
            detail="百度翻译服务初始化失败，请检查.env配置"
        )
    
    # 2. 接收并打印所有参数
    print("=" * 80)
    print("🔥 翻译接口收到请求！")
    print("=" * 80)
    print(f"📍 路径: {request.path}")
    print(f"📝 HTML Body 长度: {len(request.html_body)} 字符")
    print(f"🌐 源语言: {request.source_language}")
    print(f"🎯 目标语言: {request.target_language}")
    print(f"❌ 翻译不到的标签: {request.untranslatable_tags}")
    print(f"🚫 不需要翻译的标签: {request.no_translate_tags}")
    
    # 3. 提取HTML标签和中文文本
    print("-" * 40)
    print("🔍 开始提取HTML标签和中文文本...")
    
    extracted_data = html_parser_service.extract_tags_and_chinese(request.html_body)
    
    # 4. 打印提取结果
    print("✅ 提取完成！")
    print(f"📊 包含中文的标签数量: {extracted_data['statistics']['total_tags_with_chinese']}")
    print(f"📝 中文文本片段数量: {extracted_data['statistics']['total_chinese_segments']}")
    print(f"🔤 页面总中文字符数: {extracted_data['statistics']['total_chinese_in_page']}")
    print(f"🏷️ 标签类型: {extracted_data['statistics']['tag_types']}")
    
    # 5. 打印前5个包含中文的标签示例
    print("-" * 40)
    print("📋 包含中文的标签示例（前5个）:")
    for i, tag in enumerate(extracted_data['all_tags'][:5]):
        print(f"  {i+1}. <{tag['tag_name']}> 中文: {tag['chinese_texts'][:3]}...")
    
    # 6. 打印前10个中文文本
    print("-" * 40)
    print("📝 提取的中文文本（前10个）:")
    for i, text in enumerate(extracted_data['chinese_texts'][:10]):
        print(f"  {i+1}. {text}")
    
    # 7. 使用百度翻译API翻译中文文本
    print("-" * 40)
    print("🌐 开始调用百度翻译API...")
    
    # 打印百度翻译配置
    config_info = baidu_translation_service.get_config_info()
    print(f"📋 百度翻译配置:")
    print(f"  APP_ID: {config_info['app_id']}")
    print(f"  SECRET_KEY: {config_info['secret_key_preview']}")
    print(f"  TIMEOUT: {config_info['timeout']}秒")
    
    # 去重中文文本，避免重复翻译
    unique_chinese_texts = html_parser_service.get_unique_chinese_texts(extracted_data['chinese_texts'])
    print(f"📊 去重后需要翻译的文本数量: {len(unique_chinese_texts)}")
    
    # 批量翻译
    translation_results = baidu_translation_service.batch_translate(
        unique_chinese_texts,
        request.source_language,
        request.target_language
    )
    
    # 8. 打印翻译结果统计
    print("-" * 40)
    print("📊 翻译结果统计:")
    print(f"  总数: {translation_results['total_count']}")
    print(f"  成功: {translation_results['success_count']}")
    print(f"  失败: {translation_results['failed_count']}")
    if translation_results['total_count'] > 0:
        print(f"  成功率: {translation_results['success_count']/translation_results['total_count']*100:.1f}%")
    
    # 9. 打印前5个翻译示例
    print("-" * 40)
    print("📝 翻译示例（前5个成功的）:")
    success_translations = [t for t in translation_results['translations'] if t['success']]
    for i, trans in enumerate(success_translations[:5]):
        print(f"  {i+1}. {trans['original']} → {trans['translated']}")
    
    print("=" * 80)

    return TranslationResponse(
        success=True,
        message="✅ HTML标签提取和百度翻译完成！",
        data={
            "request_info": {
                "path": request.path,
                "html_length": len(request.html_body),
                "source_language": request.source_language,
                "target_language": request.target_language,
                "untranslatable_tags": request.untranslatable_tags,
                "no_translate_tags": request.no_translate_tags
            },
            "extraction_results": extracted_data,
            "translation_results": translation_results
        }
    )
