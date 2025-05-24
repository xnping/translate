# 翻译服务 API

一个基于FastAPI和百度翻译API的翻译服务，支持多语言翻译、高性能缓存和批量处理。

## 项目特点

- **模块化设计**: 使用依赖注入模式和模块化架构
- **高性能缓存**: Redis缓存层支持内容压缩，减少内存占用
- **批量翻译**: 支持单次请求批量翻译多个文本
- **并发控制**: 可调整并行请求数量，优化性能
- **完全异步**: 全部API使用异步实现，提高并发处理能力
- **灵活配置**: 集中化配置管理，支持动态刷新

## 项目结构

```
├── main.py          # FastAPI主应用入口
├── config.py        # 配置管理模块
├── cache.py         # Redis缓存管理模块
├── translator.py    # 翻译服务模块
├── dependencies.py  # 依赖注入管理模块
├── requirements.txt # 项目依赖
└── static/          # 静态文件目录
```

## 环境变量配置

创建`.env`文件并设置以下环境变量:

```
# Redis配置
REDIS_HOST=localhost          # Redis服务器地址
REDIS_PORT=6379               # Redis端口
REDIS_DB=0                    # Redis数据库编号
REDIS_PASSWORD=               # Redis密码
REDIS_TTL=86400               # 缓存有效期（秒）
REDIS_SOCKET_TIMEOUT=0.5      # 连接超时时间
REDIS_MAX_CONNECTIONS=50      # 最大连接数
REDIS_USE_COMPRESSION=true    # 是否启用压缩
REDIS_COMPRESSION_MIN_SIZE=1024 # 压缩的最小大小（字节）
REDIS_COMPRESSION_LEVEL=6     # 压缩等级(1-9)

# 百度翻译API配置
BAIDU_APP_ID=your_app_id      # 百度翻译API的APP ID
BAIDU_SECRET_KEY=your_secret  # 百度翻译API的密钥
BAIDU_API_URL=https://api.fanyi.baidu.com/api/trans/vip/translate
BAIDU_API_TIMEOUT=2.0         # API请求超时时间

# 批处理配置
MAX_CONCURRENT_REQUESTS=5     # 最大并发请求数
DEFAULT_BATCH_SIZE=10         # 默认批处理大小

# 应用配置
DEBUG=false                   # 是否开启调试模式
LOG_LEVEL=INFO                # 日志级别
```

## 安装依赖

```bash
pip install -r requirements.txt
```

## 启动服务

```bash
uvicorn main:app --reload
```

服务默认在 http://localhost:8000 启动，API文档在 http://localhost:8000/docs

## API使用示例

### 单文本翻译

```bash
curl -X POST "http://localhost:8000/api/translate" \
  -H "Content-Type: application/json" \
  -d '{"text":"Hello world","from_lang":"en","to_lang":"zh"}'
```

### 批量翻译

```bash
curl -X POST "http://localhost:8000/api/batch/translate" \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {"text": "Hello", "id": "1"},
      {"text": "World", "id": "2"}
    ],
    "from_lang": "en",
    "to_lang": "zh",
    "max_concurrent": 2
  }'
```

### 获取支持的语言

```bash
curl "http://localhost:8000/api/languages"
```

### 健康检查

```bash
curl "http://localhost:8000/health"
``` 