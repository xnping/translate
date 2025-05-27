"""
翻译API主启动文件
重构后的清晰版本，保持所有原有功能
"""

if __name__ == "__main__":
    from app.main import app
    import uvicorn
    from app.core.config import get_settings

    settings = get_settings()

    print(f"启动 {settings.app_name} v{settings.version}")
    print(f"服务地址: http://{settings.host}:{settings.port}")
    print(f"API文档: http://{settings.host}:{settings.port}/docs")

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        workers=1 if settings.debug else 4
    )
