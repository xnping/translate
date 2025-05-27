"""
系统相关的API路由
"""

import asyncio
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

from app.models.translation import PerformanceStats
from app.core.dependencies import (
    get_cache_dependency,
    get_merger_dependency,
    get_config_dependency
)
from app.services.cache_service import CacheService
from app.services.request_merger import RequestMerger
from app.services.config_manager import ConfigManager

router = APIRouter()


@router.get("/performance_stats", response_model=PerformanceStats)
async def get_performance_stats(
    cache: CacheService = Depends(get_cache_dependency),
    merger: RequestMerger = Depends(get_merger_dependency)
):
    """获取性能统计信息"""
    try:
        cache_stats = await cache.get_stats()
        merger_stats = merger.get_stats()
        
        return {
            "cache_stats": cache_stats,
            "merger_stats": merger_stats,
            "status": "healthy",
            "timestamp": asyncio.get_event_loop().time()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取性能统计失败: {str(e)}")


@router.get("/cache_info")
async def get_cache_info(
    cache: CacheService = Depends(get_cache_dependency)
):
    """获取缓存信息"""
    try:
        cache_stats = await cache.get_stats()
        return {
            "cache_info": cache_stats,
            "status": "active",
            "timestamp": asyncio.get_event_loop().time()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取缓存信息失败: {str(e)}")


@router.get("/config/current")
async def get_current_config(
    config_manager: ConfigManager = Depends(get_config_dependency)
):
    """获取当前配置"""
    try:
        config = config_manager.get_config()
        # 隐藏敏感信息
        safe_config = config.copy()
        for key in ["BAIDU_SECRET_KEY", "REDIS_PASSWORD"]:
            if key in safe_config:
                safe_config[key] = "***"
        
        return {
            "config": safe_config,
            "stats": config_manager.get_stats()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取配置失败: {str(e)}")


@router.get("/config/versions")
async def get_config_versions(
    config_manager: ConfigManager = Depends(get_config_dependency)
):
    """获取配置版本历史"""
    try:
        return {
            "versions": config_manager.get_version_history(),
            "current_stats": config_manager.get_stats()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取配置版本失败: {str(e)}")


@router.post("/config/update")
async def update_config(
    updates: Dict[str, Any],
    config_manager: ConfigManager = Depends(get_config_dependency)
):
    """更新配置"""
    try:
        # 验证更新内容
        if not updates:
            raise HTTPException(status_code=400, detail="更新内容不能为空")
        
        # 禁止更新敏感配置
        forbidden_keys = ["BAIDU_SECRET_KEY", "BAIDU_APP_ID"]
        for key in forbidden_keys:
            if key in updates:
                raise HTTPException(status_code=403, detail=f"禁止更新敏感配置: {key}")
        
        success = config_manager.update_config(updates, "API更新")
        if success:
            return {
                "success": True,
                "message": "配置更新成功",
                "updated_keys": list(updates.keys())
            }
        else:
            raise HTTPException(status_code=500, detail="配置更新失败")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新配置失败: {str(e)}")


@router.post("/config/rollback/{version}")
async def rollback_config(
    version: str,
    config_manager: ConfigManager = Depends(get_config_dependency)
):
    """回滚配置到指定版本"""
    try:
        success = config_manager.rollback_to_version(version)
        if success:
            return {
                "success": True,
                "message": f"配置已回滚到版本: {version}",
                "version": version
            }
        else:
            raise HTTPException(status_code=404, detail=f"版本不存在: {version}")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"回滚配置失败: {str(e)}")


@router.get("/system/status")
async def get_system_status(
    cache: CacheService = Depends(get_cache_dependency),
    merger: RequestMerger = Depends(get_merger_dependency),
    config_manager: ConfigManager = Depends(get_config_dependency)
):
    """获取系统整体状态"""
    try:
        # 获取各组件状态
        cache_stats = await cache.get_stats()
        merger_stats = merger.get_stats()
        config_stats = config_manager.get_stats()
        
        # 系统健康检查
        health_checks = {
            "cache": "healthy" if cache_stats else "unhealthy",
            "merger": "healthy" if merger_stats else "unhealthy",
            "config": "healthy" if config_stats else "unhealthy"
        }
        
        overall_status = "healthy" if all(
            status == "healthy" for status in health_checks.values()
        ) else "degraded"
        
        return {
            "status": overall_status,
            "components": health_checks,
            "stats": {
                "cache": cache_stats,
                "merger": merger_stats,
                "config": config_stats
            },
            "timestamp": asyncio.get_event_loop().time()
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": asyncio.get_event_loop().time()
        }
