"""
FastAPI翻译服务启动文件 - 已清空
"""

import uvicorn
from app.main import app

if __name__ == "__main__":
    print("🧹 翻译服务已清空，等待重新配置")
    
    uvicorn.run(
        "app.main:app",
        host="localhost",
        port=9000,
        reload=True
    )
