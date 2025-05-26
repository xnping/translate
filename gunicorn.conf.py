# gunicorn.conf.py
workers = 4  # 根据 CPU 核心数调整
worker_class = "uvicorn.workers.UvicornWorker"  # 异步处理
bind = "0.0.0.0:9000"
timeout = 30
reload = False  # 生产环境关闭热重载
keepalive = 2
max_requests = 1000
max_requests_jitter = 100
preload_app = True
accesslog = "/var/log/translation-service/access.log"
errorlog = "/var/log/translation-service/error.log"
loglevel = "info"
capture_output = True
enable_stdio_inheritance = True