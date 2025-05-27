"""
翻译API主应用文件
重构后的清晰版本，保持所有原有功能
"""

import asyncio
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager

from app.core.config import get_settings
from app.core.dependencies import get_cache, get_translator, get_request_merger, get_config_manager
from app.api.translation import router as translation_router
from app.api.batch import router as batch_router
from app.api.system import router as system_router
from app.api.frontend_config import router as frontend_config_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    settings = get_settings()
    cache = get_cache()

    # 初始化缓存连接
    await cache.initialize()

    print(f"{settings.app_name} v{settings.version} 启动成功")
    if cache.async_client:
        print("Redis缓存已连接")
    else:
        print("使用内存缓存模式")

    yield

    # 关闭时清理
    await cache.close()
    print("应用已关闭")


# 创建FastAPI应用
app = FastAPI(
    title="翻译API服务",
    description="支持中文与东盟十国官方语言的双向翻译",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# 注册路由
app.include_router(translation_router, prefix="/api", tags=["翻译"])
app.include_router(batch_router, prefix="/api", tags=["批量翻译"])
app.include_router(system_router, prefix="/api", tags=["系统"])
app.include_router(frontend_config_router, prefix="/api", tags=["前端配置"])

# 静态文件服务
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=FileResponse)
async def read_index():
    """主页 - 显示API文档"""
    return FileResponse("static/index.html")


@app.get("/health")
async def health_check():
    """健康检查接口"""
    try:
        cache = get_cache()
        cache_stats = await cache.get_stats()

        return {
            "status": "healthy",
            "version": "2.0.0",
            "cache": cache_stats,
            "timestamp": asyncio.get_event_loop().time()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"健康检查失败: {str(e)}")


if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        workers=1 if settings.debug else 4
    )
