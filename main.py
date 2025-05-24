from fastapi import FastAPI, HTTPException, Request, Body, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from flask_cors  import CORS
import aiohttp
import hashlib
import random
import json
import time
import os
from pydantic import BaseModel, Field
import shutil
import redis
from redis import ConnectionPool
from redis import asyncio as redis_asyncio
import asyncio
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager

# Load environment variables
load_dotenv()

# Initialize the Redis client using environment variables
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)
REDIS_TTL = int(os.getenv('REDIS_TTL', 86400))  # Default: 24 hours

# 优化1: 使用连接池管理Redis连接
redis_pool = None
redis_client = None
async_redis_client = None  # 优化2: 异步Redis客户端

try:
    # 创建连接池
    redis_pool = ConnectionPool(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        password=REDIS_PASSWORD,
        decode_responses=True,
        socket_timeout=1.0,  # 增加超时时间到1秒
        socket_connect_timeout=1.0,  # 增加连接超时时间
        retry_on_timeout=True,  # 启用超时重试
        max_connections=50   # 控制最大连接数
    )
    
    # 使用连接池初始化同步Redis客户端（用于非异步上下文）
    redis_client = redis.Redis(connection_pool=redis_pool)
    
    # 测试连接
    redis_client.ping()
    print("Redis connection pool created successfully")
except redis.exceptions.ConnectionError as e:
    print(f"⚠️ Redis connection failed: {e}")
    print("⚠️ Caching will be disabled")
    redis_client = None
except Exception as e:
    print(f"⚠️ Redis initialization error: {e}")
    print("⚠️ Caching will be disabled")
    redis_client = None

# 导入模块化组件
from config import config
from cache import cache_manager
from translator import translation_service

# 使用FastAPI lifespan模式管理应用的生命周期事件
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 应用启动时执行
    global async_redis_client
    
    # 设置异步Redis客户端
    try:
        # 创建异步Redis客户端
        redis_url = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
        if REDIS_PASSWORD:
            redis_url = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
            
        # 使用redis.asyncio代替aioredis
        async_redis_client = redis_asyncio.from_url(
            redis_url,
            decode_responses=True,
            socket_timeout=1.0,  # 增加超时时间到1秒
            socket_connect_timeout=1.0,  # 增加连接超时
            retry_on_timeout=True  # 启用超时重试
        )
        await async_redis_client.ping()
        print("Async Redis client initialized successfully")
    except Exception as e:
        print(f"⚠️ Async Redis initialization error: {e}")
        print("⚠️ Async Redis caching will be disabled")
        async_redis_client = None
    
    # 初始化缓存管理器
    try:
        await cache_manager.init_async_client()
        print("缓存管理器初始化完成")
    except Exception as e:
        print(f"⚠️ 缓存管理器初始化失败: {e}")
    
    # 将控制权交给应用
    yield
    
    # 应用关闭时执行 
    # 关闭Redis连接
    if async_redis_client is not None:
        await async_redis_client.close()
        print("Async Redis connection closed")
    
    # 关闭缓存管理器
    try:
        await cache_manager.close()
        print("缓存连接已关闭")
    except Exception as e:
        print(f"⚠️ 关闭缓存连接失败: {e}")

# 使用上面定义的lifespan初始化FastAPI应用
app = FastAPI(title="TranslationAPI", lifespan=lifespan)

# 添加CORS支持
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源，生产环境中应限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 您的百度翻译API密钥
BAIDU_APP_ID =os.getenv('BAIDU_APP_ID')  # 替换为您的APP ID
BAIDU_SECRET_KEY = os.getenv('BAIDU_SECRET_KEY')  # 替换为您的密钥

# 请求模型
class TranslationRequest(BaseModel):
    text: str
    from_lang: str = "auto"
    to_lang: str = "zh"
    font_size: str = None

class BatchTranslationItem(BaseModel):
    text: str
    id: Optional[str] = None

class BatchTranslationRequest(BaseModel):
    items: List[BatchTranslationItem]
    from_lang: str = "auto"
    to_lang: str = "zh"
    font_size: str = None
    max_concurrent: Optional[int] = None  # 新增并发控制参数

# 依赖注入函数
async def get_translation_service():
    """依赖注入：获取翻译服务实例"""
    return translation_service

async def get_cache_manager():
    """依赖注入：获取缓存管理器实例"""
    return cache_manager

# API端点
@app.post("/api/translate")
async def translate_async(
    request: TranslationRequest,
    translator = Depends(get_translation_service)
):
    """单文本翻译API"""
    result = await translator.translate_single(
        text=request.text,
        from_lang=request.from_lang,
        to_lang=request.to_lang,
        font_size=request.font_size
    )
    
    if result.success:
        return result.data
    else:
        return JSONResponse(
            status_code=400,
            content={"error": result.error}
        )

@app.post("/api/batch/translate")
async def batch_translate_async(
    request: BatchTranslationRequest,
    translator = Depends(get_translation_service)
):
    """批量翻译API，支持并发控制"""
    # 准备批量翻译项
    items = []
    for item in request.items:
        items.append({
            "text": item.text,
            "id": item.id
        })
    
    # 执行批量翻译
    result = await translator.translate_batch(
        items=items,
        from_lang=request.from_lang,
        to_lang=request.to_lang,
        font_size=request.font_size,
        max_concurrent=request.max_concurrent
    )
    
    return result

@app.get("/api/languages")
async def get_supported_languages():
    """获取支持的语言列表"""
    languages = {
        "auto": "自动检测",
        "zh": "中文",
        "en": "英语",
        "yue": "粤语",
        "wyw": "文言文",
        "jp": "日语",
        "kor": "韩语",
        "fra": "法语",
        "spa": "西班牙语",
        "th": "泰语",
        "ara": "阿拉伯语",
        "ru": "俄语",
        "pt": "葡萄牙语",
        "de": "德语",
        "it": "意大利语",
        "el": "希腊语",
        "nl": "荷兰语",
        "pl": "波兰语",
        "bul": "保加利亚语",
        "est": "爱沙尼亚语",
        "dan": "丹麦语",
        "fin": "芬兰语",
        "cs": "捷克语",
        "rom": "罗马尼亚语",
        "slo": "斯洛文尼亚语",
        "swe": "瑞典语",
        "hu": "匈牙利语",
        "vie": "越南语",
    }
    return languages

@app.get("/")
async def root():
    """根路径处理"""
    return FileResponse("static/index.html")

# 简化创建特定语言翻译端点的工厂函数
def make_translate_endpoint_async(lang_code):
    async def endpoint(
        data: dict = Body(...),
        translator = Depends(get_translation_service)
    ):
        request = TranslationRequest(
            text=data.get("text", ""),
            from_lang=data.get("from_lang", "zh"),
            to_lang=lang_code,
            font_size=data.get("font_size")
        )
        
        result = await translator.translate_single(
            text=request.text,
            from_lang=request.from_lang,
            to_lang=request.to_lang,
            font_size=request.font_size
        )
        
        if result.success:
            return result.data
        else:
            return JSONResponse(
                status_code=400,
                content={"error": result.error}
            )
            
    return endpoint

# 简化创建特定语言批量翻译端点的工厂函数
def make_batch_translate_endpoint_async(lang_code):
    async def endpoint(
        data: dict = Body(...),
        translator = Depends(get_translation_service)
    ):
        # 准备请求参数
        items = []
        for item in data.get("items", []):
            if isinstance(item, dict):
                items.append({
                    "text": item.get("text", ""),
                    "id": item.get("id")
                })
            else:
                items.append({
                    "text": item,
                    "id": None
                })
        
        # 执行批量翻译
        result = await translator.translate_batch(
            items=items,
            from_lang=data.get("from_lang", "zh"),
            to_lang=lang_code,
            font_size=data.get("font_size"),
            max_concurrent=data.get("max_concurrent")
        )
        
        return result
            
    return endpoint

# 为每种语言创建快捷端点
for lang_code in ["en", "jp", "kor", "fra", "spa", "th", "ara", "ru", "pt", "de", "it"]:
    # 单文本翻译
    app.post(f"/api/{lang_code}")(make_translate_endpoint_async(lang_code))
    # 批量翻译
    app.post(f"/api/batch/{lang_code}")(make_batch_translate_endpoint_async(lang_code))

# 健康检查端点
@app.get("/health")
async def health_check(cache = Depends(get_cache_manager)):
    """健康检查API"""
    # 获取缓存状态
    cache_stats = await cache.get_stats()
    
    return {
        "status": "healthy",
        "version": "2.0.0",
        "cache": cache_stats
    }

# 创建静态文件目录
os.makedirs("static", exist_ok=True)

# 挂载静态文件
app.mount("/static", StaticFiles(directory="static"), name="static")
# 为了兼容性，也挂载在/translate/static/路径下
app.mount("/translate/static", StaticFiles(directory="static"), name="translate_static")

# 启动服务器命令: uvicorn main:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

if os.path.exists('api.md') and not os.path.exists('static/api.md'):
    shutil.move('api.md', 'static/api.md')

