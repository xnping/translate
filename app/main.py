"""
FastAPI应用主文件
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.config.config import init_database, close_database, get_settings
from app.api.translation import router as translation_router
from app.api.words import router as words_router
from app.services.redis_path_cache_service import redis_path_cache_service
from app.services.mysql_service import mysql_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    print(" 启动翻译API服务...")

    # 启动时初始化MySQL数据库
    try:
        await init_database()
        print("MySQL数据库连接成功")
        print(f"   数据库主机: {get_settings().db_host}:{get_settings().db_port}")
        print(f"   数据库名称: {get_settings().db_name}")
    except Exception as e:
        print(f" MySQL数据库连接失败: {e}")
        print(" 将继续启动服务，但数据库功能可能不可用")

    # 初始化Redis路径缓存服务
    try:
        redis_success = await redis_path_cache_service.initialize()
        if redis_success:
            print("✅ Redis路径缓存服务初始化成功")
            # 获取Redis连接信息
            redis_info = await redis_path_cache_service.get_cache_info()
            print(f"   Redis主机: {redis_path_cache_service.host}:{redis_path_cache_service.port}")
            print(f"   Redis版本: {redis_info.get('redis_version', 'unknown')}")
            print(f"   连接客户端: {redis_info.get('connected_clients', 0)}")
            print(f"   内存使用: {redis_info.get('used_memory_human', 'unknown')}")
            print(f"   路径缓存键数量: {redis_info.get('path_cache_keys', 0)}")
        else:
            print("❌ Redis路径缓存服务初始化失败")
    except Exception as e:
        print(f"❌ Redis路径缓存初始化异常: {e}")

    # 初始化MySQL连接池
    try:
        mysql_success = await mysql_service.create_pool()
        if mysql_success:
            print("✅ MySQL连接池初始化成功")
        else:
            print("❌ MySQL连接池初始化失败")
    except Exception as e:
        print(f"❌ MySQL连接池初始化异常: {e}")

    print("服务启动完成！")

    yield

    # 关闭时清理连接
    print("正在关闭服务...")

    try:
        await close_database()
        print("MySQL数据库连接已关闭")
    except Exception as e:
        print(f"MySQL数据库关闭失败: {e}")

    try:
        await redis_path_cache_service.close()
        print("✅ Redis路径缓存连接已关闭")
    except Exception as e:
        print(f"⚠️ Redis路径缓存连接关闭失败: {e}")

    try:
        await mysql_service.close_pool()
        print("✅ MySQL连接池已关闭")
    except Exception as e:
        print(f"⚠️ MySQL连接池关闭失败: {e}")

    print("服务已关闭")


# 创建FastAPI应用
app = FastAPI(
    title="高速并发翻译API",
    description="基于百度翻译API的高速并发翻译服务，支持大型HTML处理",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件
app.mount("/static", StaticFiles(directory="static"), name="static")

# 注册路由
app.include_router(translation_router)
app.include_router(words_router)


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "高速并发翻译API",
        "version": "2.0.0",
        "docs": "/docs",
        "admin": "/admin",
        "endpoints": {
            "translate": "/api/translate",
            "words": "/api/words",
            "redis_status": "/redis/status"
        }
    }


@app.get("/admin")
async def admin_page():
    """管理页面"""
    return FileResponse("static/admin/index.html")



@app.get("/redis/status")
async def redis_status():
    """Redis路径缓存状态"""
    cache_info = await redis_path_cache_service.get_cache_info()
    return {
        "redis_path_cache": cache_info,
        "config": {
            "host": redis_path_cache_service.host,
            "port": redis_path_cache_service.port,
            "db": redis_path_cache_service.db,
            "cache_ttl": redis_path_cache_service.cache_ttl,
            "use_compression": redis_path_cache_service.use_compression
        }
    }

