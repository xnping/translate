#!/usr/bin/env python3
"""
配置验证脚本
检查配置是否正确加载和使用
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import get_settings

def main():
    print("🔍 验证配置...")
    
    try:
        settings = get_settings()
        
        print("\n✅ 配置加载成功！")
        print(f"📍 应用名称: {settings.app_name}")
        print(f"📍 版本: {settings.version}")
        print(f"📍 调试模式: {settings.debug}")
        
        print(f"\n🌐 服务器配置:")
        print(f"   主机: {settings.host}")
        print(f"   端口: {settings.port}")
        
        print(f"\n🗄️ Redis配置:")
        print(f"   主机: {settings.redis_host}")
        print(f"   端口: {settings.redis_port}")
        print(f"   数据库: {settings.redis_db}")
        print(f"   密码: {'***' if settings.redis_password else '无'}")
        print(f"   最大连接数: {settings.redis_max_connections}")
        print(f"   连接超时: {settings.redis_connect_timeout}s")
        print(f"   Socket超时: {settings.redis_socket_timeout}s")
        print(f"   启用压缩: {settings.redis_use_compression}")
        print(f"   压缩最小大小: {settings.redis_compression_min_size} bytes")
        print(f"   压缩等级: {settings.redis_compression_level}")
        print(f"   Redis URL: {settings.redis_url}")
        
        print(f"\n💾 缓存配置:")
        print(f"   缓存TTL: {settings.cache_ttl}s ({settings.cache_ttl/3600:.1f}小时)")
        print(f"   内存缓存大小: {settings.memory_cache_size}")
        print(f"   内存缓存TTL: {settings.memory_cache_ttl}s")
        
        print(f"\n🔄 请求处理配置:")
        print(f"   合并窗口: {settings.merge_window}s")
        print(f"   最大批量大小: {settings.max_batch_size}")
        print(f"   最大并发请求: {settings.max_concurrent_requests}")
        
        print(f"\n🌍 百度API配置:")
        print(f"   APP ID: {settings.baidu_app_id}")
        print(f"   密钥: {'***' if settings.baidu_secret_key else '未设置'}")
        print(f"   超时时间: {settings.baidu_api_timeout}s")
        
        print(f"\n📝 日志配置:")
        print(f"   日志级别: {settings.log_level}")
        print(f"   日志文件: {settings.log_file or '控制台'}")
        
        print(f"\n🌐 支持的语言:")
        languages = settings.get_supported_languages()
        for code, name in languages.items():
            print(f"   {code}: {name}")
        
        # 验证必要配置
        print(f"\n🔍 配置验证:")
        issues = []
        
        if not settings.baidu_app_id or settings.baidu_app_id == "your_app_id_here":
            issues.append("❌ 百度APP ID未配置")
        else:
            print("✅ 百度APP ID已配置")
            
        if not settings.baidu_secret_key or settings.baidu_secret_key == "your_secret_key_here":
            issues.append("❌ 百度密钥未配置")
        else:
            print("✅ 百度密钥已配置")
            
        if settings.redis_host and settings.redis_port:
            print("✅ Redis连接配置正常")
        else:
            issues.append("❌ Redis连接配置异常")
            
        if issues:
            print(f"\n⚠️ 发现配置问题:")
            for issue in issues:
                print(f"   {issue}")
            return False
        else:
            print(f"\n🎉 所有配置验证通过！")
            return True
            
    except Exception as e:
        print(f"❌ 配置验证失败: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
