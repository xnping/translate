# 🌐 翻译API服务

基于FastAPI的现代化翻译服务，支持中文与东盟十国官方语言的双向翻译。

## ✨ 功能特性

- 🚀 **高性能异步架构** - 基于FastAPI和asyncio
- 🗂️ **多级缓存系统** - Redis + 内存缓存，支持数据压缩
- 📦 **批量翻译支持** - 高效处理大量翻译请求
- 🔄 **智能请求合并** - 防止重复请求，提升性能
- ⚙️ **配置热更新** - 支持版本控制和回滚
- 📊 **完整监控统计** - 性能指标和健康检查
- 🎯 **类型安全** - 完整的Pydantic数据验证

## 🏗️ 项目架构

```
translation-api/
├── app/                    # 应用核心
│   ├── api/               # API路由层
│   ├── core/              # 核心配置
│   ├── services/          # 业务服务层
│   └── models/            # 数据模型
├── static/                # 静态文件
├── scripts/               # 部署脚本
└── docs/                  # 文档
```

## 🚀 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 配置环境
```bash
# 编辑.env文件，配置百度翻译API
BAIDU_APP_ID=your_app_id
BAIDU_SECRET_KEY=your_secret_key
```

### 3. 启动服务
```bash
python main.py
```

### 4. 访问服务
- **API文档**: http://localhost:9000/docs
- **主页**: http://localhost:9000
- **健康检查**: http://localhost:9000/health

## 🌍 支持的语言

| 语言 | 代码 | 语言 | 代码 |
|------|------|------|------|
| 中文 | zh | 英语 | en |
| 泰语 | th | 越南语 | vie |
| 印尼语 | id | 马来语 | ms |
| 菲律宾语 | fil | 缅甸语 | my |
| 高棉语 | km | 老挝语 | lo |
| 泰米尔语 | ta | 自动检测 | auto |

## 📖 API接口

### 基础翻译
```bash
POST /api/translate
{
  "text": "你好世界",
  "from_lang": "zh",
  "to_lang": "en"
}
```

### 批量翻译
```bash
POST /api/batch/translate
{
  "items": ["你好", "世界"],
  "from_lang": "zh",
  "to_lang": "en"
}
```

### 单一目标语言
```bash
POST /api/translate_to_english
{
  "text": "你好世界"
}
```

## 🔧 部署

### 开发环境
```bash
python main.py
```

### 生产环境
```bash
uvicorn app.main:app --host 0.0.0.0 --port 9000 --workers 4
```

## 📊 监控

- **性能统计**: GET /api/performance_stats
- **缓存信息**: GET /api/cache_info
- **系统状态**: GET /api/system/status

## 🔄 重构说明

项目已完成现代化重构：
- ✅ 清晰的模块化架构
- ✅ 标准的依赖注入
- ✅ 完整的类型提示
- ✅ 统一的错误处理
- ✅ 自动API文档生成

详细说明请查看 [项目结构文档](docs/PROJECT_STRUCTURE.md)

## 📄 许可证

MIT License
