"""
FastAPI应用主文件
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.config.config import init_database, close_database, get_settings
from app.api import type_api, label_api
from app.api.translation import router as translation_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化数据库
    await init_database()
    print("✅ 数据库初始化完成")

    yield

    # 关闭时清理数据库连接
    await close_database()
    print("✅ 数据库连接已关闭")


# 创建FastAPI应用
app = FastAPI(
    title="Label & Type 管理API",
    description="提供Label和Type表的完整CRUD操作",
    version="1.0.0",
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
app.include_router(type_api.router)
app.include_router(label_api.router)
app.include_router(translation_router)


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "Label & Type 管理API + 翻译API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "types": "/api/types",
            "labels": "/api/labels",
            "translate": "/api/translate"
        },
        "pages": {
            "news": "/news"
        }
    }

@app.get("/news")
async def news_page():
    """新闻页面"""
    return FileResponse("static/news-page.html")


