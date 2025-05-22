# gunicorn.conf.py
workers = 4  # 根据 CPU 核心数调整
worker_class = "gevent"  # 异步处理
bind = "0.0.0.0:8000"
timeout = 30
reload = True  # 开发时可开，生产建议关闭，改用信号控制
accesslog = "/var/log/gunicorn/access.log"
errorlog = "/var/log/gunicorn/error.log"