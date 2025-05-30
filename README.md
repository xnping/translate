# 🚀 高速并发翻译API

基于百度翻译API的高速并发翻译服务，支持大型HTML处理，具备100%替换率的DOM翻译能力。

## ✨ 特性

- 🚀 **高速并发翻译**: 15个并发请求，3秒内完成翻译
- 🎯 **100%替换率**: DOM级别的精确翻译替换
- 📦 **大型HTML支持**: 自动处理20万+字符的HTML文件
- 🌐 **智能模式切换**: 自动检测HTML大小，选择最佳处理方式
- 💾 **数据库支持**: MySQL数据存储 + Redis缓存
- 🔧 **RESTful API**: 标准REST接口，支持CORS跨域

## 🛠️ 技术栈

- **后端**: FastAPI + Python 3.8+
- **翻译**: 百度翻译API
- **数据库**: MySQL 8.0
- **缓存**: Redis 6.0+
- **HTML处理**: BeautifulSoup4 + DOM解析
- **并发**: aiohttp + asyncio

## 📋 环境要求

- Python 3.8+
- MySQL 8.0+
- Redis 6.0+
- 百度翻译API账号

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

创建 `.env` 文件：

```env
# 百度翻译API配置
BAIDU_APP_ID=your_app_id
BAIDU_SECRET_KEY=your_secret_key
BAIDU_API_TIMEOUT=2.0

# MySQL数据库配置
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=123456
DB_NAME=baidu

# Redis配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=123456
REDIS_DB=0
REDIS_MAX_CONNECTIONS=50
CACHE_TTL=86400
```

### 3. 启动服务

```bash
python main.py
```

服务将在 `http://localhost:9000` 启动

## 📚 API文档

### 翻译接口

**POST** `/api/translate`

#### 请求参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| `path` | string | ✅ | 页面路径（域名+路径） |
| `html_body` | string | ✅ | 完整的HTML内容 |
| `source_language` | string | ✅ | 源语言代码（如：zh） |
| `target_language` | string | ✅ | 目标语言代码（如：en） |
| `untranslatable_tags` | string | ❌ | 不可翻译的标签 |
| `no_translate_tags` | string | ❌ | 不需要翻译的标签 |

#### 语言代码

| 语言 | 代码 |
|------|------|
| 中文 | zh |
| 英文 | en |
| 日文 | jp |
| 韩文 | kor |
| 法文 | fra |
| 德文 | de |
| 俄文 | ru |
| 西班牙文 | spa |

#### 响应格式

```json
{
  "success": true,
  "message": "🎉 翻译完成！替换率: 98.5%",
  "data": {
    "request_info": {
      "path": "https://example.com/page",
      "html_length": 274396,
      "source_language": "zh",
      "target_language": "en",
      "processing_mode": "ULTIMATE_DOM_100%"
    },
    "translation_results": {
      "success_count": 1150,
      "failed_count": 84,
      "total_count": 1234,
      "duration": 2.8
    },
    "ultimate_replacement_results": {
      "translated_html_body": "<html>...</html>",
      "replacement_statistics": {
        "original_chinese_count": 2856,
        "remaining_chinese_count": 43,
        "replaced_count": 2813,
        "replacement_rate": 98.5
      }
    }
  }
}
```

## 💻 使用示例

### cURL

```bash
curl -X POST "http://localhost:9000/api/translate" \
  -H "Content-Type: application/json" \
  -d '{
    "path": "https://example.com/news",
    "html_body": "<html><body><h1>你好世界</h1><p>这是一个测试页面</p></body></html>",
    "source_language": "zh",
    "target_language": "en",
    "untranslatable_tags": null,
    "no_translate_tags": null
  }'
```

### JavaScript (Fetch)

```javascript
const translatePage = async () => {
  const response = await fetch('http://localhost:9000/api/translate', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      path: window.location.href,
      html_body: document.body.outerHTML,
      source_language: 'zh',
      target_language: 'en',
      untranslatable_tags: null,
      no_translate_tags: null
    })
  });

  const result = await response.json();
  
  if (result.success) {
    // 应用翻译结果
    const translatedHtml = result.data.ultimate_replacement_results.translated_html_body;
    document.body.innerHTML = translatedHtml;
    
    console.log(`翻译完成！替换率: ${result.data.ultimate_replacement_results.replacement_statistics.replacement_rate}%`);
  }
};

// 调用翻译
translatePage();
```

### TypeScript

```typescript
interface TranslationRequest {
  path: string;
  html_body: string;
  source_language: string;
  target_language: string;
  untranslatable_tags?: string | null;
  no_translate_tags?: string | null;
}

interface TranslationResponse {
  success: boolean;
  message: string;
  data: {
    request_info: {
      path: string;
      html_length: number;
      source_language: string;
      target_language: string;
      processing_mode: string;
    };
    translation_results: {
      success_count: number;
      failed_count: number;
      total_count: number;
      duration: number;
    };
    ultimate_replacement_results: {
      translated_html_body: string;
      replacement_statistics: {
        original_chinese_count: number;
        remaining_chinese_count: number;
        replaced_count: number;
        replacement_rate: number;
      };
    };
  };
}

class TranslationService {
  private apiUrl: string;

  constructor(apiUrl: string = 'http://localhost:9000') {
    this.apiUrl = apiUrl;
  }

  async translatePage(request: TranslationRequest): Promise<TranslationResponse> {
    const response = await fetch(`${this.apiUrl}/api/translate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request)
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    return await response.json();
  }

  async translateCurrentPage(
    sourceLanguage: string = 'zh',
    targetLanguage: string = 'en'
  ): Promise<void> {
    try {
      const request: TranslationRequest = {
        path: window.location.href,
        html_body: document.body.outerHTML,
        source_language: sourceLanguage,
        target_language: targetLanguage
      };

      const result = await this.translatePage(request);

      if (result.success && result.data.ultimate_replacement_results) {
        const translatedHtml = result.data.ultimate_replacement_results.translated_html_body;
        const stats = result.data.ultimate_replacement_results.replacement_statistics;

        // 应用翻译
        document.body.innerHTML = translatedHtml;

        console.log(`✅ 翻译完成！替换率: ${stats.replacement_rate.toFixed(2)}%`);
        console.log(`📊 统计: ${stats.replaced_count}/${stats.original_chinese_count} 字符已翻译`);
      }
    } catch (error) {
      console.error('❌ 翻译失败:', error);
    }
  }
}

// 使用示例
const translationService = new TranslationService();

// 翻译当前页面
translationService.translateCurrentPage('zh', 'en');
```

### Python

```python
import requests
import json

def translate_html(html_content, source_lang='zh', target_lang='en', api_url='http://localhost:9000'):
    """
    翻译HTML内容

    Args:
        html_content: HTML内容
        source_lang: 源语言代码
        target_lang: 目标语言代码
        api_url: API服务地址

    Returns:
        翻译结果
    """
    url = f"{api_url}/api/translate"

    payload = {
        "path": "https://example.com/page",
        "html_body": html_content,
        "source_language": source_lang,
        "target_language": target_lang,
        "untranslatable_tags": None,
        "no_translate_tags": None
    }

    headers = {
        'Content-Type': 'application/json'
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()

        result = response.json()

        if result['success']:
            translated_html = result['data']['ultimate_replacement_results']['translated_html_body']
            stats = result['data']['ultimate_replacement_results']['replacement_statistics']

            print(f"✅ 翻译完成！替换率: {stats['replacement_rate']:.2f}%")
            print(f"📊 统计: {stats['replaced_count']}/{stats['original_chinese_count']} 字符已翻译")

            return translated_html
        else:
            print(f"❌ 翻译失败: {result['message']}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"❌ 请求失败: {e}")
        return None

# 使用示例
html_content = """
<html>
<head><title>测试页面</title></head>
<body>
    <h1>欢迎来到我们的网站</h1>
    <p>这是一个中文测试页面，包含多种内容。</p>
    <div>我们提供优质的服务和产品。</div>
</body>
</html>
"""

translated_html = translate_html(html_content, 'zh', 'en')
if translated_html:
    print("翻译后的HTML:")
    print(translated_html)
```

### Node.js

```javascript
const axios = require('axios');

class TranslationAPI {
  constructor(apiUrl = 'http://localhost:9000') {
    this.apiUrl = apiUrl;
  }

  async translateHTML(htmlContent, sourceLang = 'zh', targetLang = 'en') {
    try {
      const response = await axios.post(`${this.apiUrl}/api/translate`, {
        path: 'https://example.com/page',
        html_body: htmlContent,
        source_language: sourceLang,
        target_language: targetLang,
        untranslatable_tags: null,
        no_translate_tags: null
      }, {
        headers: {
          'Content-Type': 'application/json'
        }
      });

      const result = response.data;

      if (result.success) {
        const translatedHtml = result.data.ultimate_replacement_results.translated_html_body;
        const stats = result.data.ultimate_replacement_results.replacement_statistics;

        console.log(`✅ 翻译完成！替换率: ${stats.replacement_rate.toFixed(2)}%`);
        console.log(`📊 统计: ${stats.replaced_count}/${stats.original_chinese_count} 字符已翻译`);

        return {
          success: true,
          translatedHtml,
          stats
        };
      } else {
        console.error(`❌ 翻译失败: ${result.message}`);
        return { success: false, error: result.message };
      }

    } catch (error) {
      console.error('❌ 请求失败:', error.message);
      return { success: false, error: error.message };
    }
  }
}

// 使用示例
const translationAPI = new TranslationAPI();

const htmlContent = `
<html>
<head><title>测试页面</title></head>
<body>
    <h1>欢迎来到我们的网站</h1>
    <p>这是一个中文测试页面，包含多种内容。</p>
    <div>我们提供优质的服务和产品。</div>
</body>
</html>
`;

(async () => {
  const result = await translationAPI.translateHTML(htmlContent, 'zh', 'en');

  if (result.success) {
    console.log('翻译后的HTML:');
    console.log(result.translatedHtml);
  }
})();
```

## 🔧 其他API接口

### Redis状态检查

**GET** `/redis/status`

```bash
curl http://localhost:9000/redis/status
```

响应：
```json
{
  "redis_cache": {
    "status": "connected",
    "redis_version": "6.2.6",
    "connected_clients": 1,
    "used_memory_human": "1.2M"
  },
  "config": {
    "host": "localhost",
    "port": 6379,
    "db": 0,
    "cache_ttl": 86400
  }
}
```

### 服务信息

**GET** `/`

```bash
curl http://localhost:9000/
```

## 📊 性能指标

### 翻译速度

- **小型HTML** (< 10万字符): 2-3秒
- **大型HTML** (10-50万字符): 8-15秒
- **超大HTML** (> 50万字符): 按比例线性增长

### 替换率

- **标准模式**: 85-95%
- **终极模式**: 95-100%
- **DOM模式**: 98-100%

### 并发性能

- **最大并发**: 15个请求
- **翻译速度**: 40-70 文本/秒
- **内存使用**: 每10万字符约30MB

## 🚨 错误处理

### 常见错误码

| 错误码 | 描述 | 解决方案 |
|--------|------|----------|
| 400 | 请求参数错误 | 检查请求参数格式 |
| 500 | 百度翻译API错误 | 检查API配置和网络 |
| 503 | 服务不可用 | 检查数据库和Redis连接 |

### 错误响应格式

```json
{
  "success": false,
  "message": "错误描述",
  "error_code": "ERROR_CODE",
  "details": "详细错误信息"
}
```

## 🔒 安全说明

- API密钥请妥善保管，不要泄露
- 建议在生产环境中使用HTTPS
- 可以配置IP白名单限制访问
- 建议设置请求频率限制

## 📈 监控和日志

服务启动时会显示详细的连接信息：

```
🚀 启动翻译API服务...
✅ MySQL数据库连接成功
   数据库主机: localhost:3306
   数据库名称: baidu
✅ Redis连接测试成功
   Redis主机: localhost:6379
   Redis版本: 6.2.6
🎉 服务启动完成！
```



## 📄 许可证

MIT License


如有问题，请联系开发团队或提交Issue。
