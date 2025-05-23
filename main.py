from fastapi import FastAPI, HTTPException, Request, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import requests
import hashlib
import random
import json
import time
import os
from pydantic import BaseModel
import shutil
import redis
import aiohttp
import asyncio

# Load environment variables
load_dotenv()

# Initialize the Redis client using environment variables
REDIS_HOST = os.getenv('REDIS_HOST', '8.138.177.105')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', '123456')

# 处理可能包含注释的REDIS_TTL值
redis_ttl_value = os.getenv('REDIS_TTL', '86400')
if redis_ttl_value and '#' in redis_ttl_value:
    # 如果包含井号，只取井号前的部分并去除空白
    redis_ttl_value = redis_ttl_value.split('#')[0].strip()
REDIS_TTL = int(redis_ttl_value)

# Initialize Redis client
redis_client = None
try:
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        password=REDIS_PASSWORD,
        decode_responses=True,  # Return string values instead of bytes
        socket_timeout=5,  # Timeout for Redis operations
    )
    # Test Redis connection
    redis_client.ping()
    print("Redis connection successful")
except redis.exceptions.ConnectionError as e:
    print(f"⚠️ Redis connection failed: {e}")
    print("⚠️ Caching will be disabled")
    redis_client = None
except Exception as e:
    print(f"⚠️ Redis initialization error: {e}")
    print("⚠️ Caching will be disabled")
    redis_client = None

app = FastAPI(title="TranslationAPI")

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

class TranslationRequest(BaseModel):
    text: str
    from_lang: str = "auto"
    to_lang: str = "zh"
    font_size: str = None  # 新增，可选

class BatchTranslationRequest(BaseModel):
    texts: list[str]
    from_lang: str = "auto"
    to_lang: str = "zh"
    font_size: str = None

@app.post("/api/translate")
async def translate(request: TranslationRequest):
    """使用百度翻译API翻译文本，并支持Redis缓存"""
    
    # 检查是否启用了缓存
    if redis_client is not None:
        # 生成缓存键
        cache_key = f"trans:{request.from_lang}:{request.to_lang}:{hashlib.md5(request.text.encode()).hexdigest()}"
        
        # 尝试从缓存获取
        cached_result = redis_client.get(cache_key)
        if cached_result:
            try:
                result = json.loads(cached_result)
                # 添加字体大小（如果请求中有指定）
                if request.font_size:
                    result['font_size'] = request.font_size
                return result
            except json.JSONDecodeError:
                # 如果缓存数据损坏，继续执行翻译
                pass
    
    # 构建百度翻译API请求参数
    salt = str(random.randint(32768, 65536))
    sign = BAIDU_APP_ID + request.text + salt + BAIDU_SECRET_KEY
    sign = hashlib.md5(sign.encode()).hexdigest()
    
    payload = {
        'appid': BAIDU_APP_ID,
        'q': request.text,
        'from': request.from_lang,
        'to': request.to_lang,
        'salt': salt,
        'sign': sign
    }
    
    try:
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        response = requests.post('https://api.fanyi.baidu.com/api/trans/vip/translate', 
                               params=payload, 
                               headers=headers)
        
        # 检查响应状态
        if response.status_code != 200:
            return JSONResponse(
                status_code=response.status_code,
                content={"error": f"Baidu API request failed with status {response.status_code}"}
            )
        
        result = response.json()
        
        # 检查是否有错误
        if 'error_code' in result:
            return JSONResponse(
                status_code=400,
                content={"error_code": result['error_code'], "error_msg": result['error_msg']}
            )
            
        # 返回时带上 font_size 字段（如果有）
        if request.font_size:
            result['font_size'] = request.font_size
            
        # 如果Redis可用，缓存结果
        if redis_client is not None:
            try:
                # 不保存font_size到缓存中，因为它是请求特定的
                cache_result = result.copy()
                if 'font_size' in cache_result:
                    del cache_result['font_size']
                    
                redis_client.setex(
                    cache_key,
                    REDIS_TTL,
                    json.dumps(cache_result)
                )
            except Exception as e:
                print(f"⚠️ Redis caching error: {e}")
                
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 异步版本的翻译接口，使用aiohttp代替requests
@app.post("/api/translate_async")
async def translate_async(request: TranslationRequest):
    """异步版本的翻译接口，使用aiohttp代替requests，支持Redis缓存"""
    
    # 检查是否启用了缓存
    if redis_client is not None:
        # 生成缓存键
        cache_key = f"trans:{request.from_lang}:{request.to_lang}:{hashlib.md5(request.text.encode()).hexdigest()}"
        
        # 尝试从缓存获取
        cached_result = redis_client.get(cache_key)
        if cached_result:
            try:
                result = json.loads(cached_result)
                # 添加字体大小（如果请求中有指定）
                if request.font_size:
                    result['font_size'] = request.font_size
                return result
            except json.JSONDecodeError:
                # 如果缓存数据损坏，继续执行翻译
                pass
    
    # 构建百度翻译API请求参数
    salt = str(random.randint(32768, 65536))
    sign = BAIDU_APP_ID + request.text + salt + BAIDU_SECRET_KEY
    sign = hashlib.md5(sign.encode()).hexdigest()
    
    payload = {
        'appid': BAIDU_APP_ID,
        'q': request.text,
        'from': request.from_lang,
        'to': request.to_lang,
        'salt': salt,
        'sign': sign
    }
    
    try:
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        
        async with aiohttp.ClientSession() as session:
            async with session.post('https://api.fanyi.baidu.com/api/trans/vip/translate', 
                                params=payload, 
                                headers=headers) as response:
                
                # 检查响应状态
                if response.status != 200:
                    return JSONResponse(
                        status_code=response.status,
                        content={"error": f"Baidu API request failed with status {response.status}"}
                    )
                
                result = await response.json()
                
                # 检查是否有错误
                if 'error_code' in result:
                    return JSONResponse(
                        status_code=400,
                        content={"error_code": result['error_code'], "error_msg": result['error_msg']}
                    )
                    
                # 返回时带上 font_size 字段（如果有）
                if request.font_size:
                    result['font_size'] = request.font_size
                    
                # 如果Redis可用，缓存结果
                if redis_client is not None:
                    try:
                        # 不保存font_size到缓存中，因为它是请求特定的
                        cache_result = result.copy()
                        if 'font_size' in cache_result:
                            del cache_result['font_size']
                            
                        redis_client.setex(
                            cache_key,
                            REDIS_TTL,
                            json.dumps(cache_result)
                        )
                    except Exception as e:
                        print(f"⚠️ Redis caching error: {e}")
                        
                return result
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/languages")
async def get_supported_languages():
    """仅返回东盟十国官方语言列表"""
    languages = {
        "auto": "自动检测",
        "id": "印尼语",         # 印度尼西亚
        "ms": "马来语",         # 马来西亚、文莱、新加坡
        "fil": "菲律宾语",      # 菲律宾
        "my": "缅甸语",         # 缅甸
        "km": "高棉语",         # 柬埔寨
        "lo": "老挝语",         # 老挝
        "th": "泰语",           # 泰国
        "vie": "越南语",        # 越南
        "en": "英语",           # 新加坡、文莱、菲律宾官方语言
        "zh": "中文",           # 新加坡、马来西亚官方语言
        "ta": "泰米尔语"        # 新加坡官方语言
    }
    return languages

# 创建静态文件目录
os.makedirs("static", exist_ok=True)

# 挂载静态文件
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    """重定向到演示页面"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/static/index.html")

# 东盟十国语言代码与接口名映射
aSEAN_langs = {
    "indonesian": "id",      # 印尼语
    "malay": "ms",           # 马来语
    "filipino": "fil",       # 菲律宾语
    "burmese": "my",         # 缅甸语
    "khmer": "km",           # 高棉语
    "lao": "lo",             # 老挝语
    "thai": "th",            # 泰语
    "vietnamese": "vie",     # 越南语
    "english": "en",         # 英语
    "tamil": "ta"            # 泰米尔语
}

def make_translate_endpoint(lang_code):
    async def endpoint(data: dict = Body(...)):
        text = data.get("text", "")
        font_size = data.get("font_size")
        if not text.strip():
            return {"error": "文本不能为空"}
        from pydantic import BaseModel
        class Req(BaseModel):
            text: str
            from_lang: str = "zh"
            to_lang: str = lang_code
            font_size: str = None
        req = Req(text=text, font_size=font_size)
        result = await translate(req)
        # 保证 font_size 字段在返回中
        if font_size:
            if isinstance(result, JSONResponse):
                # 错误时直接返回
                return result
            result['font_size'] = font_size
        return result
    return endpoint

# 使用异步版本的翻译接口
def make_translate_endpoint_async(lang_code):
    async def endpoint(data: dict = Body(...)):
        text = data.get("text", "")
        font_size = data.get("font_size")
        if not text.strip():
            return {"error": "文本不能为空"}
        from pydantic import BaseModel
        class Req(BaseModel):
            text: str
            from_lang: str = "zh"
            to_lang: str = lang_code
            font_size: str = None
        req = Req(text=text, font_size=font_size)
        result = await translate_async(req)
        # 保证 font_size 字段在返回中
        if font_size:
            if isinstance(result, JSONResponse):
                # 错误时直接返回
                return result
            result['font_size'] = font_size
        return result
    return endpoint

# 动态注册十个接口
for name, code in aSEAN_langs.items():
    route = f"/api/translate_to_{name}"
    app.post(route)(make_translate_endpoint(code))
    # 注册异步接口
    route_async = f"/api/async/translate_to_{name}"
    app.post(route_async)(make_translate_endpoint_async(code))

# 健康检查端点
@app.get("/health")
async def health_check():
    """健康检查端点，适用于负载均衡和监控"""
    health = {"status": "ok", "timestamp": time.time()}
    
    # 检查Redis连接
    if redis_client is not None:
        try:
            redis_client.ping()
            health["cache"] = "connected"
        except:
            health["cache"] = "disconnected"
    else:
        health["cache"] = "disabled"
        
    return health

@app.get("/api/redis/keys")
async def get_redis_keys():
    """返回Redis中所有的键值对"""
    if redis_client is not None:
        try:
            keys = redis_client.keys('*')
            result = {}
            for key in keys:
                value = redis_client.get(key)
                try:
                    # 尝试将JSON字符串转换为字典
                    result[key] = json.loads(value) if value else None
                except (json.JSONDecodeError, TypeError):
                    # 如果不是JSON格式，保留原始值
                    result[key] = value
            return {"keys_count": len(keys), "data": result}
        except Exception as e:
            return {"error": f"获取Redis数据出错: {str(e)}"}
    return {"error": "Redis连接不可用"}

@app.post("/api/batch_translate_async")
async def batch_translate_async(request: BatchTranslationRequest):
    """批量异步翻译接口，支持同时翻译多个文本"""
    if not request.texts:
        return {"error": "文本列表不能为空"}
    
    # 限制最大并发请求数 - 提高并发
    MAX_CONCURRENT = 100  
    # 每组最大文本数量 - 提高并发
    MAX_GROUP_SIZE = 200  
    
    results = []
    all_tasks = []
    
    # 创建多个异步任务，并按组分配
    async with aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=60),  # 增加总超时时间
        connector=aiohttp.TCPConnector(
            limit=0, # 取消连接数限制
            ttl_dns_cache=300,  # DNS缓存时间
            use_dns_cache=True,  # 使用DNS缓存
            force_close=False  # 允许连接复用
        )
    ) as session:
        # 将文本分组，每组最多MAX_GROUP_SIZE个文本
        text_groups = [request.texts[i:i+MAX_GROUP_SIZE] for i in range(0, len(request.texts), MAX_GROUP_SIZE)]
        
        # 使用信号量限制并发数
        sem = asyncio.Semaphore(MAX_CONCURRENT)
        
        # 优先检查缓存
        cached_results = {}
        
        # 预先检查所有文本的缓存状态 - 使用Redis管道批量处理
        if redis_client is not None:
            try:
                # 创建所有缓存键
                cache_keys = [
                    f"trans:{request.from_lang}:{request.to_lang}:{hashlib.md5(text.encode()).hexdigest()}"
                    for text in request.texts
                ]
                
                # 使用管道批量获取缓存
                pipe = redis_client.pipeline()
                for key in cache_keys:
                    pipe.get(key)
                
                # 执行管道操作并处理结果
                cached_data = pipe.execute()
                
                for idx, data in enumerate(cached_data):
                    if data:
                        try:
                            result = json.loads(data)
                            if request.font_size:
                                result['font_size'] = request.font_size
                            cached_results[idx] = result
                        except json.JSONDecodeError:
                            pass
            except Exception as e:
                print(f"Redis批量缓存读取出错: {e}")
        
        async def process_text_with_limit(text, idx):
            # 如果已经在缓存中找到，就跳过API调用
            if idx in cached_results:
                return cached_results[idx]
                
            async with sem:  # 使用信号量控制并发
                single_req = TranslationRequest(
                    text=text,
                    from_lang=request.from_lang,
                    to_lang=request.to_lang,
                    font_size=request.font_size or "16px" # 确保有默认值
                )
                return await _translate_single_async(single_req, session)
        
        # 为每个文本创建异步任务，但跳过已缓存的
        for idx, text in enumerate(request.texts):
            if idx not in cached_results:  # 只为未缓存的创建任务
                task = asyncio.create_task(process_text_with_limit(text, idx))
                all_tasks.append((idx, task))
        
        # 处理未缓存的任务 - 使用gather提高效率
        if all_tasks:
            # 提取索引和任务
            indices, tasks = zip(*all_tasks) if all_tasks else ([], [])
            # 并行等待所有任务
            task_results = await asyncio.gather(*tasks, return_exceptions=True)
            # 组合结果
            for idx, result in zip(indices, task_results):
                if isinstance(result, Exception):
                    results.append((idx, {"error": str(result), "text": request.texts[idx]}))
                else:
                    results.append((idx, result))
        
        # 合并缓存结果和新翻译结果
        final_results = [None] * len(request.texts)
        
        # 先填入已缓存的结果
        for idx, result in cached_results.items():
            final_results[idx] = result
            
        # 再填入新翻译的结果
        for idx, result in results:
            final_results[idx] = result
    
    return {
        "total": len(final_results),
        "translations": final_results
    }

async def _translate_single_async(request: TranslationRequest, session: aiohttp.ClientSession):
    """单个文本异步翻译的内部实现，供批量翻译使用"""
    
    # 检查是否启用了缓存
    if redis_client is not None:
        # 生成缓存键
        cache_key = f"trans:{request.from_lang}:{request.to_lang}:{hashlib.md5(request.text.encode()).hexdigest()}"
        
        # 尝试从缓存获取
        cached_result = redis_client.get(cache_key)
        if cached_result:
            try:
                result = json.loads(cached_result)
                # 添加字体大小（如果请求中有指定）
                if request.font_size:
                    result['font_size'] = request.font_size
                return result
            except json.JSONDecodeError:
                # 如果缓存数据损坏，继续执行翻译
                pass
    
    # 构建百度翻译API请求参数
    salt = str(random.randint(32768, 65536))
    sign = BAIDU_APP_ID + request.text + salt + BAIDU_SECRET_KEY
    sign = hashlib.md5(sign.encode()).hexdigest()
    
    payload = {
        'appid': BAIDU_APP_ID,
        'q': request.text,
        'from': request.from_lang,
        'to': request.to_lang,
        'salt': salt,
        'sign': sign
    }
    
    try:
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        
        # 添加重试逻辑
        max_retries = 3
        retry_delay = 0.2  # 初始重试延迟
        
        for retry in range(max_retries):
            try:
                async with session.post(
                    'https://api.fanyi.baidu.com/api/trans/vip/translate', 
                    params=payload, 
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=5)  # 设置每个请求的超时为5秒
                ) as response:
                    
                    # 检查响应状态
                    if response.status != 200:
                        if retry < max_retries - 1:
                            # 指数退避重试
                            await asyncio.sleep(retry_delay * (2 ** retry))
                            continue
                        return {
                            "error": f"Baidu API request failed with status {response.status}",
                            "text": request.text
                        }
                    
                    result = await response.json()
                    break  # 成功获取响应，跳出重试循环
                    
            except asyncio.TimeoutError:
                if retry < max_retries - 1:
                    # 指数退避重试
                    await asyncio.sleep(retry_delay * (2 ** retry))
                    continue
                return {
                    "error": "Baidu API request timed out",
                    "text": request.text
                }
        
        # 检查是否有错误
        if 'error_code' in result:
            return {
                "error_code": result['error_code'], 
                "error_msg": result['error_msg'],
                "text": request.text
            }
            
        # 返回时带上 font_size 字段（如果有）
        if request.font_size:
            result['font_size'] = request.font_size
            
        # 如果Redis可用，缓存结果
        if redis_client is not None:
            try:
                # 不保存font_size到缓存中，因为它是请求特定的
                cache_result = result.copy()
                if 'font_size' in cache_result:
                    del cache_result['font_size']
                    
                redis_client.setex(
                    cache_key,
                    REDIS_TTL,
                    json.dumps(cache_result)
                )
            except Exception as e:
                print(f"⚠️ Redis caching error: {e}")
                
        return result
            
    except Exception as e:
        return {"error": str(e), "text": request.text}

# 启动服务器命令: uvicorn main:app --reload
if __name__ == "__main__":
    # CORS(app, resources={r"/api/*": {"origins": "*"}})
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

if os.path.exists('api.md') and not os.path.exists('static/api.md'):
    shutil.move('api.md', 'static/api.md')

