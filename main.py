from fastapi import FastAPI, HTTPException, Request, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from flask_cors  import CORS
import requests
import hashlib
import random
import json
import time
import os
from pydantic import BaseModel
import shutil

app = FastAPI(title="TranslationAPI")

# 添加CORS支持
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源，生产环境中应限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
load_dotenv()
# 您的百度翻译API密钥
BAIDU_APP_ID =os.getenv('BAIDU_APP_ID')  # 替换为您的APP ID
BAIDU_SECRET_KEY = os.getenv('BAIDU_SECRET_KEY')  # 替换为您的密钥

class TranslationRequest(BaseModel):
    text: str
    from_lang: str = "auto"
    to_lang: str = "zh"
    font_size: str = None  # 新增，可选

@app.post("/api/translate")
async def translate(request: TranslationRequest):
    """使用百度翻译API翻译文本"""
    
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

# 动态注册十个接口
for name, code in aSEAN_langs.items():
    route = f"/api/translate_to_{name}"
    app.post(route)(make_translate_endpoint(code))

# 启动服务器命令: uvicorn main:app --reload
if __name__ == "__main__":
    # CORS(app, resources={r"/api/*": {"origins": "*"}})
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

if os.path.exists('api.md') and not os.path.exists('static/api.md'):
    shutil.move('api.md', 'static/api.md')

