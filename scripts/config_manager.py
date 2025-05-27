#!/usr/bin/env python3
"""
配置管理脚本
用于验证、更新和管理语言配置文件
"""

import sys
import os
import yaml
import json
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

from app.core.language_config import get_language_config
from app.api.dynamic_routes import validate_endpoint_config, get_registered_endpoints


def print_header(title: str):
    """打印标题"""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")


def print_section(title: str):
    """打印小节标题"""
    print(f"\n{'-'*40}")
    print(f" {title}")
    print(f"{'-'*40}")


def validate_config():
    """验证配置文件"""
    print_header("配置文件验证")
    
    try:
        # 加载语言配置
        language_config = get_language_config()
        print("✅ 语言配置文件加载成功")
        
        # 验证端点配置
        validation_result = validate_endpoint_config()
        
        print_section("验证结果")
        print(f"总端点数: {validation_result['total_endpoints']}")
        print(f"配置有效: {'✅ 是' if validation_result['valid'] else '❌ 否'}")
        
        if validation_result['errors']:
            print(f"\n❌ 错误 ({len(validation_result['errors'])}):")
            for error in validation_result['errors']:
                print(f"  - {error}")
        
        if validation_result['warnings']:
            print(f"\n⚠️ 警告 ({len(validation_result['warnings'])}):")
            for warning in validation_result['warnings']:
                print(f"  - {warning}")
        
        if not validation_result['errors'] and not validation_result['warnings']:
            print("✅ 配置完全正确，无错误或警告")
        
        return validation_result['valid']
        
    except Exception as e:
        print(f"❌ 配置验证失败: {e}")
        return False


def show_languages():
    """显示语言配置"""
    print_header("语言配置信息")
    
    try:
        language_config = get_language_config()
        
        print_section("支持的语言")
        languages = language_config.get_supported_languages()
        for code, name in languages.items():
            lang_info = language_config.get_language_info(code)
            source = "✅" if lang_info.get('is_source', False) else "❌"
            target = "✅" if lang_info.get('is_target', False) else "❌"
            enabled = "✅" if lang_info.get('enabled', False) else "❌"
            print(f"  {code:6} | {name:10} | 源:{source} | 目标:{target} | 启用:{enabled}")
        
        print_section("前端配置")
        source_langs = language_config.get_frontend_source_languages()
        target_langs = language_config.get_frontend_target_languages()
        
        print(f"源语言选项: {len(source_langs)} 个")
        for lang in source_langs:
            print(f"  - {lang['code']}: {lang['name']}")
        
        print(f"\n目标语言选项: {len(target_langs)} 个")
        for lang in target_langs:
            print(f"  - {lang['code']}: {lang['name']}")
        
    except Exception as e:
        print(f"❌ 获取语言配置失败: {e}")


def show_endpoints():
    """显示端点配置"""
    print_header("端点配置信息")
    
    try:
        endpoints = get_registered_endpoints()
        
        print(f"总端点数: {len(endpoints)}")
        print_section("单一目标语言端点")
        
        for code, info in endpoints.items():
            print(f"  {code:6} | {info['endpoint']:25} | {info['description']}")
            print(f"         | {info['source_language']} -> {info['target_language']}")
            print()
        
    except Exception as e:
        print(f"❌ 获取端点配置失败: {e}")


def export_config(format_type: str = "json"):
    """导出配置"""
    print_header(f"导出配置 ({format_type.upper()})")
    
    try:
        language_config = get_language_config()
        endpoints = get_registered_endpoints()
        
        export_data = {
            "languages": language_config.get_supported_languages(),
            "source_languages": language_config.get_frontend_source_languages(),
            "target_languages": language_config.get_frontend_target_languages(),
            "endpoints": endpoints,
            "testing_languages": language_config.get_testing_languages(),
            "test_texts": language_config.get_test_texts()
        }
        
        if format_type.lower() == "json":
            output = json.dumps(export_data, ensure_ascii=False, indent=2)
            filename = "language_config_export.json"
        else:
            output = yaml.dump(export_data, allow_unicode=True, default_flow_style=False)
            filename = "language_config_export.yaml"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(output)
        
        print(f"✅ 配置已导出到: {filename}")
        
    except Exception as e:
        print(f"❌ 导出配置失败: {e}")


def show_statistics():
    """显示统计信息"""
    print_header("配置统计信息")
    
    try:
        language_config = get_language_config()
        endpoints = get_registered_endpoints()
        
        all_languages = language_config._config['languages']
        enabled_languages = [code for code, config in all_languages.items() if config.get('enabled', True)]
        source_languages = [code for code, config in all_languages.items() if config.get('is_source', False)]
        target_languages = [code for code, config in all_languages.items() if config.get('is_target', False)]
        
        print(f"📊 语言统计:")
        print(f"  总语言数: {len(all_languages)}")
        print(f"  启用语言: {len(enabled_languages)}")
        print(f"  源语言数: {len(source_languages)}")
        print(f"  目标语言: {len(target_languages)}")
        
        print(f"\n📊 接口统计:")
        print(f"  单一目标语言接口: {len(endpoints)}")
        
        print(f"\n📊 前端配置:")
        frontend_source = language_config.get_frontend_source_languages()
        frontend_target = language_config.get_frontend_target_languages()
        print(f"  前端源语言选项: {len(frontend_source)}")
        print(f"  前端目标语言选项: {len(frontend_target)}")
        
        print(f"\n📊 测试配置:")
        testing_languages = language_config.get_testing_languages()
        test_texts = language_config.get_test_texts()
        print(f"  测试语言数: {len(testing_languages)}")
        print(f"  测试文本组: {len(test_texts)}")
        
    except Exception as e:
        print(f"❌ 获取统计信息失败: {e}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="语言配置管理工具")
    parser.add_argument("action", choices=["validate", "languages", "endpoints", "export", "stats"], 
                       help="要执行的操作")
    parser.add_argument("--format", choices=["json", "yaml"], default="json",
                       help="导出格式 (仅用于export)")
    
    args = parser.parse_args()
    
    if args.action == "validate":
        success = validate_config()
        sys.exit(0 if success else 1)
    elif args.action == "languages":
        show_languages()
    elif args.action == "endpoints":
        show_endpoints()
    elif args.action == "export":
        export_config(args.format)
    elif args.action == "stats":
        show_statistics()


if __name__ == "__main__":
    main()
