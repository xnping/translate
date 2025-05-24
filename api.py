from fastapi import FastAPI, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import hashlib
import random
import json
import time
import redis
import aiohttp
import asyncio
from typing import List

# 导入配置
from config import (
    REDIS_CONFIG, 
    REDIS_TTL, 
    BAIDU_TRANSLATE_CONFIG, 
    TRANSLATION_CONFIG, 
    HTTP_CLIENT_CONFIG
)

# 百度翻译API密钥
BAIDU_APP_ID = BAIDU_TRANSLATE_CONFIG['APP_ID']
BAIDU_SECRET_KEY = BAIDU_TRANSLATE_CONFIG['SECRET_KEY']

# 初始化Redis客户端
redis_client = None
try:
    redis_client = redis.Redis(
        host=REDIS_CONFIG['HOST'],
        port=REDIS_CONFIG['PORT'],
        db=REDIS_CONFIG['DB'],
        password=REDIS_CONFIG['PASSWORD'],
        decode_responses=REDIS_CONFIG['DECODE_RESPONSES'],
        socket_timeout=REDIS_CONFIG['SOCKET_TIMEOUT'],
    )
    # 测试Redis连接
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

class TranslationRequest(BaseModel):
    text: str
    from_lang: str = "auto"
    to_lang: str = "zh"
    font_size: str = None

class BatchTranslationRequest(BaseModel):
    texts: List[str]
    from_lang: str = "auto"
    to_lang: str = "zh"
    font_size: str = None

# API路由函数，将在main.py中注册
async def batch_translate_async(request: BatchTranslationRequest):
    """批量异步翻译接口，支持同时翻译多个文本"""
    if not request.texts:
        return {"error": "文本列表不能为空"}
    
    # 限制最大并发请求数和每组最大文本数量
    MAX_CONCURRENT = TRANSLATION_CONFIG['MAX_CONCURRENT']
    MAX_GROUP_SIZE = TRANSLATION_CONFIG['MAX_GROUP_SIZE']
    
    results = []
    all_tasks = []
    
    # 创建多个异步任务，并按组分配
    async with aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=TRANSLATION_CONFIG['TOTAL_TIMEOUT']),
        connector=aiohttp.TCPConnector(
            limit=0,  # 取消连接数限制
            ttl_dns_cache=HTTP_CLIENT_CONFIG['TTL_DNS_CACHE'],
            use_dns_cache=HTTP_CLIENT_CONFIG['USE_DNS_CACHE'],
            force_close=HTTP_CLIENT_CONFIG['FORCE_CLOSE']
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
        max_retries = TRANSLATION_CONFIG['RETRY_COUNT']
        retry_delay = TRANSLATION_CONFIG['RETRY_DELAY']
        
        for retry in range(max_retries):
            try:
                async with session.post(
                    TRANSLATION_CONFIG['BASE_URL'], 
                    params=payload, 
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=TRANSLATION_CONFIG['REQUEST_TIMEOUT'])
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

# 添加Redis缓存查看功能
async def get_redis_cache(prefix: str = None):
    """获取Redis缓存内容"""
    if redis_client is None:
        return {"status": "error", "message": "Redis未连接"}

    try:
        if prefix:
            # 获取指定前缀的缓存键
            keys = redis_client.keys(f"{prefix}*")
        else:
            # 获取所有缓存键
            keys = redis_client.keys("*")
            
        # 限制返回数量以避免过大的响应
        MAX_KEYS = 100
        keys = keys[:MAX_KEYS]
        
        cache_data = {}
        for key in keys:
            value = redis_client.get(key)
            ttl = redis_client.ttl(key)
            try:
                # 尝试解析JSON
                cache_data[key] = {
                    "value": json.loads(value),
                    "ttl": ttl
                }
            except:
                # 非JSON值
                cache_data[key] = {
                    "value": value,
                    "ttl": ttl
                }
                
        return {
            "status": "success",
            "count": len(keys),
            "total_keys": len(redis_client.keys("*")),
            "max_shown": MAX_KEYS,
            "data": cache_data
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

# 定义从main.py导入需要的路由函数
def register_routes(app: FastAPI):
    """向FastAPI应用注册API路由"""
    app.post("/api/batch_translate_async")(batch_translate_async)
    app.post("/api/extreme_batch_translate")(extreme_batch_translate)
    app.get("/api/redis_cache")(get_redis_cache)
    app.get("/api/server_status")(get_server_status)

async def extreme_batch_translate(request: BatchTranslationRequest):
    """极限批量翻译接口，使用更大的批次和更高的并发"""
    if not request.texts:
        return {"error": "文本列表不能为空"}
    
    # 极限配置 - 更高的并发和更大的批量
    EXTREME_MAX_CONCURRENT = 100  # 设置为更高的并发数
    EXTREME_MAX_GROUP_SIZE = 500  # 每组最多500个文本
    
    results = []
    all_tasks = []
    
    # 记录开始时间以计算耗时
    start_time = time.time()
    
    # 创建多个异步任务，并按组分配
    async with aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=120),  # 更长的总超时时间
        connector=aiohttp.TCPConnector(
            limit=0,  # 取消连接数限制
            ttl_dns_cache=HTTP_CLIENT_CONFIG['TTL_DNS_CACHE'],
            use_dns_cache=HTTP_CLIENT_CONFIG['USE_DNS_CACHE'],
            force_close=HTTP_CLIENT_CONFIG['FORCE_CLOSE']
        )
    ) as session:
        # 将文本分组，每组最多EXTREME_MAX_GROUP_SIZE个文本
        text_groups = [request.texts[i:i+EXTREME_MAX_GROUP_SIZE] for i in range(0, len(request.texts), EXTREME_MAX_GROUP_SIZE)]
        
        # 使用信号量限制并发数
        sem = asyncio.Semaphore(EXTREME_MAX_CONCURRENT)
        
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
                
                # 添加重试逻辑，确保获取到结果
                max_retries = 5  # 极限模式下增加重试次数
                for retry in range(max_retries):
                    try:
                        result = await _translate_single_async(single_req, session)
                        # 检查是否有错误
                        if 'error' in result or 'error_code' in result:
                            if retry < max_retries - 1:
                                await asyncio.sleep(0.5 * (retry + 1))  # 指数退避
                                continue
                        return result
                    except Exception as e:
                        if retry < max_retries - 1:
                            await asyncio.sleep(0.5 * (retry + 1))  # 指数退避
                            continue
                        return {"error": str(e), "text": text}
                
                # 如果所有重试都失败
                return {"error": "所有重试失败", "text": text}
        
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
    
    # 计算总耗时
    execution_time = time.time() - start_time
    
    # 检查是否所有结果都成功
    error_count = 0
    for result in final_results:
        if result and ('error' in result or 'error_code' in result):
            error_count += 1
    
    success_rate = ((len(final_results) - error_count) / len(final_results) * 100) if final_results else 0
    
    return {
        "total": len(final_results),
        "translations": final_results,
        "execution_time": round(execution_time, 2),
        "texts_per_second": round(len(request.texts) / execution_time, 2) if execution_time > 0 else 0,
        "success_rate": round(success_rate, 2),
        "error_count": error_count
    }

async def get_server_status():
    """获取服务器状态信息"""
    import platform
    import psutil
    
    try:
        # 系统信息
        system_info = {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "processor": platform.processor()
        }
        
        # CPU使用率
        cpu_info = {
            "cpu_count": psutil.cpu_count(),
            "cpu_percent": psutil.cpu_percent(interval=0.5, percpu=True),
            "cpu_avg_percent": psutil.cpu_percent(interval=0.5)
        }
        
        # 内存使用情况
        memory = psutil.virtual_memory()
        memory_info = {
            "total": memory.total / (1024**3),  # GB
            "available": memory.available / (1024**3),  # GB
            "used": memory.used / (1024**3),  # GB
            "percent": memory.percent
        }
        
        # Redis状态
        redis_status = "unavailable"
        redis_used_memory = None
        redis_total_keys = 0
        
        if redis_client is not None:
            try:
                redis_info = redis_client.info()
                redis_status = "connected"
                redis_used_memory = redis_info.get('used_memory_human', 'unknown')
                redis_total_keys = len(redis_client.keys("*"))
            except:
                redis_status = "error"
        
        return {
            "status": "ok",
            "timestamp": time.time(),
            "system": system_info,
            "cpu": cpu_info,
            "memory": memory_info,
            "redis": {
                "status": redis_status,
                "used_memory": redis_used_memory,
                "total_keys": redis_total_keys
            }
        }
    except Exception as e:
        return {"status": "error", "message": str(e)} 