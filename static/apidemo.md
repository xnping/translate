# 🌐 翻译API接口文档

## 📋 接口概览

本API提供多语言翻译服务，支持中文与东盟十国官方语言的双向翻译。

**服务器地址**: `http://45.204.6.32:9000`
**支持格式**: JSON
**字符编码**: UTF-8

## 🔧 基础接口

### 1. 健康检查

**接口**: `GET /health`
**说明**: 检查服务状态

#### cURL 示例
```bash
curl -X GET "http://45.204.6.32:9000/health"
```

#### JavaScript 示例
```javascript
// 使用 fetch
fetch('http://45.204.6.32:9000/health')
  .then(response => response.json())
  .then(data => console.log(data))
  .catch(error => console.error('Error:', error));

// 使用 axios
axios.get('http://45.204.6.32:9000/health')
  .then(response => console.log(response.data))
  .catch(error => console.error('Error:', error));
```

#### TypeScript 示例
```typescript
interface HealthResponse {
  status: string;
  version: string;
  cache: object;
}

async function checkHealth(): Promise<HealthResponse> {
  const response = await fetch('http://45.204.6.32:9000/health');
  return await response.json();
}

// 使用示例
checkHealth().then(data => {
  console.log(`服务状态: ${data.status}`);
  console.log(`版本: ${data.version}`);
});
```

### 2. 获取支持语言列表

**接口**: `GET /api/languages`
**说明**: 获取所有支持的语言代码和名称

#### cURL 示例
```bash
curl -X GET "http://45.204.6.32:9000/api/languages"
```

#### JavaScript 示例
```javascript
// 获取语言列表
async function getLanguages() {
  try {
    const response = await fetch('http://45.204.6.32:9000/api/languages');
    const languages = await response.json();

    // 显示支持的语言
    Object.entries(languages).forEach(([code, name]) => {
      console.log(`${code}: ${name}`);
    });

    return languages;
  } catch (error) {
    console.error('获取语言列表失败:', error);
  }
}
```

#### TypeScript 示例
```typescript
interface Languages {
  [key: string]: string;
}

async function getLanguages(): Promise<Languages> {
  const response = await fetch('http://45.204.6.32:9000/api/languages');
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  return await response.json();
}

// 使用示例
getLanguages().then(languages => {
  console.log('支持的语言:', languages);
});
```

## 🔤 翻译接口

### 3. 通用翻译接口

**接口**: `POST /api/translate`
**说明**: 支持任意语言间的翻译

#### 请求参数
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| text | string | 是 | 要翻译的文本 |
| from_lang | string | 否 | 源语言代码，默认auto |
| to_lang | string | 否 | 目标语言代码，默认zh |
| font_size | string | 否 | 建议字体大小 |

#### cURL 示例
```bash
# 中文翻译为英文
curl -X POST "http://45.204.6.32:9000/api/translate" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "你好世界",
    "from_lang": "zh",
    "to_lang": "en",
    "font_size": "24px"
  }'

# 自动检测语言翻译为中文
curl -X POST "http://45.204.6.32:9000/api/translate" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello World",
    "from_lang": "auto",
    "to_lang": "zh"
  }'
```

#### JavaScript 示例
```javascript
// 翻译函数
async function translateText(text, fromLang = 'auto', toLang = 'zh', fontSize = null) {
  const requestBody = {
    text: text,
    from_lang: fromLang,
    to_lang: toLang
  };

  if (fontSize) {
    requestBody.font_size = fontSize;
  }

  try {
    const response = await fetch('http://45.204.6.32:9000/api/translate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestBody)
    });

    const result = await response.json();

    if (result.trans_result && result.trans_result.length > 0) {
      return {
        success: true,
        original: result.trans_result[0].src,
        translated: result.trans_result[0].dst,
        fontSize: result.font_size
      };
    } else {
      throw new Error('翻译失败');
    }
  } catch (error) {
    return {
      success: false,
      error: error.message
    };
  }
}

// 使用示例
translateText('你好世界', 'zh', 'en', '20px')
  .then(result => {
    if (result.success) {
      console.log(`原文: ${result.original}`);
      console.log(`译文: ${result.translated}`);
    } else {
      console.error('翻译失败:', result.error);
    }
  });
```

#### TypeScript 示例
```typescript
interface TranslationRequest {
  text: string;
  from_lang?: string;
  to_lang?: string;
  font_size?: string;
}

interface TranslationResult {
  src: string;
  dst: string;
}

interface TranslationResponse {
  trans_result: TranslationResult[];
  font_size?: string;
}

interface TranslationSuccess {
  success: true;
  original: string;
  translated: string;
  fontSize?: string;
}

interface TranslationError {
  success: false;
  error: string;
}

type TranslationResult = TranslationSuccess | TranslationError;

class TranslationAPI {
  private baseUrl: string;

  constructor(baseUrl: string = 'http://45.204.6.32:9000') {
    this.baseUrl = baseUrl;
  }

  async translate(
    text: string,
    fromLang: string = 'auto',
    toLang: string = 'zh',
    fontSize?: string
  ): Promise<TranslationResult> {
    const requestBody: TranslationRequest = {
      text,
      from_lang: fromLang,
      to_lang: toLang
    };

    if (fontSize) {
      requestBody.font_size = fontSize;
    }

    try {
      const response = await fetch(`${this.baseUrl}/api/translate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody)
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result: TranslationResponse = await response.json();

      if (result.trans_result && result.trans_result.length > 0) {
        return {
          success: true,
          original: result.trans_result[0].src,
          translated: result.trans_result[0].dst,
          fontSize: result.font_size
        };
      } else {
        throw new Error('翻译结果为空');
      }
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : '未知错误'
      };
    }
  }
}

// 使用示例
const api = new TranslationAPI();

api.translate('你好世界', 'zh', 'en', '24px')
  .then(result => {
    if (result.success) {
      console.log(`翻译成功: ${result.original} → ${result.translated}`);
    } else {
      console.error(`翻译失败: ${result.error}`);
    }
  });
```

## 🎯 单一目标语言翻译接口

### 5. 翻译到指定语言

**说明**: 将中文翻译为指定的目标语言，提供便捷的单一目标语言接口

#### 支持的语言接口

| 接口路径 | 目标语言 | 语言代码 |
|----------|----------|----------|
| `/api/translate_to_english` | 英语 | en |
| `/api/translate_to_thai` | 泰语 | th |
| `/api/translate_to_vietnamese` | 越南语 | vie |
| `/api/translate_to_indonesian` | 印尼语 | id |
| `/api/translate_to_malay` | 马来语 | may |
| `/api/translate_to_filipino` | 菲律宾语 | fil |
| `/api/translate_to_burmese` | 缅甸语 | bur |
| `/api/translate_to_khmer` | 高棉语 | hkm |
| `/api/translate_to_lao` | 老挝语 | lao |
| `/api/translate_to_tamil` | 泰米尔语 | tam |

#### 请求参数
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| text | string | 是 | 要翻译的中文文本 |
| font_size | string | 否 | 建议字体大小 |

#### cURL 示例
```bash
# 翻译到英语
curl -X POST "http://45.204.6.32:9000/api/translate_to_english" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "你好世界",
    "font_size": "24px"
  }'

# 翻译到泰语
curl -X POST "http://45.204.6.32:9000/api/translate_to_thai" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "早上好",
    "font_size": "20px"
  }'

# 翻译到越南语
curl -X POST "http://45.204.6.32:9000/api/translate_to_vietnamese" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "谢谢"
  }'
```

#### JavaScript 示例
```javascript
// 单一目标语言翻译类
class SingleTargetTranslator {
  constructor(baseUrl = 'http://45.204.6.32:9000') {
    this.baseUrl = baseUrl;
  }

  // 通用单一目标语言翻译方法
  async translateTo(language, text, fontSize = null) {
    const requestBody = { text };
    if (fontSize) {
      requestBody.font_size = fontSize;
    }

    try {
      const response = await fetch(`${this.baseUrl}/api/translate_to_${language}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody)
      });

      const result = await response.json();

      if (result.trans_result && result.trans_result.length > 0) {
        return {
          success: true,
          original: result.trans_result[0].src,
          translated: result.trans_result[0].dst,
          language: language,
          fontSize: result.font_size
        };
      } else {
        throw new Error(result.error || '翻译失败');
      }
    } catch (error) {
      return {
        success: false,
        error: error.message,
        language: language
      };
    }
  }

  // 便捷方法
  async toEnglish(text, fontSize) {
    return this.translateTo('english', text, fontSize);
  }

  async toThai(text, fontSize) {
    return this.translateTo('thai', text, fontSize);
  }

  async toVietnamese(text, fontSize) {
    return this.translateTo('vietnamese', text, fontSize);
  }

  async toIndonesian(text, fontSize) {
    return this.translateTo('indonesian', text, fontSize);
  }

  async toMalay(text, fontSize) {
    return this.translateTo('malay', text, fontSize);
  }
}

// 使用示例
const translator = new SingleTargetTranslator();

// 翻译到英语
translator.toEnglish('你好世界', '24px')
  .then(result => {
    if (result.success) {
      console.log(`中文→英语: ${result.original} → ${result.translated}`);
    } else {
      console.error('翻译失败:', result.error);
    }
  });

// 翻译到泰语
translator.toThai('早上好')
  .then(result => {
    if (result.success) {
      console.log(`中文→泰语: ${result.original} → ${result.translated}`);
    }
  });

// 批量翻译到不同语言
const texts = ['你好', '世界', '朋友', '谢谢'];
const languages = ['english', 'thai', 'vietnamese', 'indonesian'];

Promise.all(
  texts.map(text =>
    Promise.all(
      languages.map(lang => translator.translateTo(lang, text))
    )
  )
).then(results => {
  results.forEach((langResults, textIndex) => {
    console.log(`\n"${texts[textIndex]}" 的翻译结果:`);
    langResults.forEach(result => {
      if (result.success) {
        console.log(`  ${result.language}: ${result.translated}`);
      }
    });
  });
});
```

#### TypeScript 示例
```typescript
interface SingleTranslationRequest {
  text: string;
  font_size?: string;
}

interface SingleTranslationSuccess {
  success: true;
  original: string;
  translated: string;
  language: string;
  fontSize?: string;
}

interface SingleTranslationError {
  success: false;
  error: string;
  language: string;
}

type SingleTranslationResult = SingleTranslationSuccess | SingleTranslationError;

type SupportedLanguage =
  | 'english' | 'thai' | 'vietnamese' | 'indonesian' | 'malay'
  | 'filipino' | 'burmese' | 'khmer' | 'lao' | 'tamil';

class SingleTargetTranslator {
  private baseUrl: string;

  constructor(baseUrl: string = 'http://45.204.6.32:9000') {
    this.baseUrl = baseUrl;
  }

  async translateTo(
    language: SupportedLanguage,
    text: string,
    fontSize?: string
  ): Promise<SingleTranslationResult> {
    const requestBody: SingleTranslationRequest = { text };
    if (fontSize) {
      requestBody.font_size = fontSize;
    }

    try {
      const response = await fetch(`${this.baseUrl}/api/translate_to_${language}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody)
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result: TranslationResponse = await response.json();

      if (result.trans_result && result.trans_result.length > 0) {
        return {
          success: true,
          original: result.trans_result[0].src,
          translated: result.trans_result[0].dst,
          language,
          fontSize: result.font_size
        };
      } else {
        throw new Error('翻译结果为空');
      }
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : '未知错误',
        language
      };
    }
  }

  // 类型安全的便捷方法
  async toEnglish(text: string, fontSize?: string): Promise<SingleTranslationResult> {
    return this.translateTo('english', text, fontSize);
  }

  async toThai(text: string, fontSize?: string): Promise<SingleTranslationResult> {
    return this.translateTo('thai', text, fontSize);
  }

  async toVietnamese(text: string, fontSize?: string): Promise<SingleTranslationResult> {
    return this.translateTo('vietnamese', text, fontSize);
  }

  async toIndonesian(text: string, fontSize?: string): Promise<SingleTranslationResult> {
    return this.translateTo('indonesian', text, fontSize);
  }

  async toMalay(text: string, fontSize?: string): Promise<SingleTranslationResult> {
    return this.translateTo('malay', text, fontSize);
  }
}

// 使用示例
const translator = new SingleTargetTranslator();

// 类型安全的翻译
async function translateExample() {
  const result = await translator.toEnglish('你好世界', '24px');

  if (result.success) {
    console.log(`翻译成功: ${result.original} → ${result.translated}`);
    console.log(`目标语言: ${result.language}`);
    if (result.fontSize) {
      console.log(`建议字体大小: ${result.fontSize}`);
    }
  } else {
    console.error(`翻译到${result.language}失败: ${result.error}`);
  }
}

// 批量翻译示例
async function batchTranslateExample() {
  const texts = ['你好', '世界', '朋友'];
  const languages: SupportedLanguage[] = ['english', 'thai', 'vietnamese'];

  for (const text of texts) {
    console.log(`\n翻译 "${text}":`);

    const promises = languages.map(lang => translator.translateTo(lang, text));
    const results = await Promise.all(promises);

    results.forEach(result => {
      if (result.success) {
        console.log(`  ${result.language}: ${result.translated}`);
      } else {
        console.error(`  ${result.language}: 失败 - ${result.error}`);
      }
    });
  }
}

translateExample();
batchTranslateExample();
```

### 6. 批量单一目标语言翻译

**接口**: `POST /api/batch/translate_to_{language}`
**说明**: 批量翻译到指定语言

#### cURL 示例
```bash
# 批量翻译到英语
curl -X POST "http://45.204.6.32:9000/api/batch/translate_to_english" \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {"text": "你好", "id": "greeting"},
      {"text": "世界", "id": "world"},
      "中国"
    ],
    "font_size": "20px"
  }'
```

#### JavaScript 示例
```javascript
// 批量单一目标语言翻译
async function batchTranslateTo(language, items, fontSize = null) {
  const requestBody = { items };
  if (fontSize) {
    requestBody.font_size = fontSize;
  }

  try {
    const response = await fetch(`http://45.204.6.32:9000/api/batch/translate_to_${language}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestBody)
    });

    const result = await response.json();
    return result;
  } catch (error) {
    console.error('批量翻译失败:', error);
    return { success: false, error: error.message };
  }
}

// 使用示例
const items = [
  {text: "你好", id: "greeting"},
  {text: "世界", id: "world"},
  {text: "朋友", id: "friend"}
];

batchTranslateTo('english', items, '18px')
  .then(result => {
    if (result.results) {
      result.results.forEach(item => {
        if (item.trans_result) {
          console.log(`${item.id}: ${item.trans_result[0].dst}`);
        }
      });
    }
  });
```

## 📊 监控和统计接口

### 7. 性能统计

**接口**: `GET /api/performance_stats`
**说明**: 获取API性能统计信息

#### cURL 示例
```bash
curl -X GET "http://45.204.6.32:9000/api/performance_stats"
```

#### JavaScript 示例
```javascript
// 获取性能统计
async function getPerformanceStats() {
  try {
    const response = await fetch('http://45.204.6.32:9000/api/performance_stats');
    const stats = await response.json();

    console.log('性能统计:', stats);

    if (stats.cache_stats) {
      console.log(`缓存命中率: ${stats.cache_stats.hits}/${stats.cache_stats.hits + stats.cache_stats.misses}`);
    }

    return stats;
  } catch (error) {
    console.error('获取性能统计失败:', error);
  }
}

// 定期监控性能
setInterval(getPerformanceStats, 30000); // 每30秒检查一次
```

#### TypeScript 示例
```typescript
interface PerformanceStats {
  cache_stats: {
    hits: number;
    misses: number;
    memory_hits: number;
    connection_errors: number;
  };
  status: string;
  timestamp: number;
}

async function getPerformanceStats(): Promise<PerformanceStats | null> {
  try {
    const response = await fetch('http://45.204.6.32:9000/api/performance_stats');
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('获取性能统计失败:', error);
    return null;
  }
}

// 性能监控类
class PerformanceMonitor {
  private intervalId: NodeJS.Timeout | null = null;

  start(intervalMs: number = 30000) {
    this.intervalId = setInterval(async () => {
      const stats = await getPerformanceStats();
      if (stats) {
        this.logStats(stats);
      }
    }, intervalMs);
  }

  stop() {
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
    }
  }

  private logStats(stats: PerformanceStats) {
    const hitRate = stats.cache_stats.hits /
      (stats.cache_stats.hits + stats.cache_stats.misses) * 100;

    console.log(`缓存命中率: ${hitRate.toFixed(2)}%`);
    console.log(`内存缓存命中: ${stats.cache_stats.memory_hits}`);
    console.log(`连接错误: ${stats.cache_stats.connection_errors}`);
  }
}

// 使用示例
const monitor = new PerformanceMonitor();
monitor.start(30000); // 每30秒监控一次
```

### 8. 缓存信息

**接口**: `GET /api/cache_info`
**说明**: 获取缓存系统信息

#### cURL 示例
```bash
curl -X GET "http://45.204.6.32:9000/api/cache_info"
```

#### JavaScript 示例
```javascript
// 获取缓存信息
async function getCacheInfo() {
  try {
    const response = await fetch('http://45.204.6.32:9000/api/cache_info');
    const cacheInfo = await response.json();

    console.log('缓存信息:', cacheInfo);

    if (cacheInfo.cache_stats) {
      const stats = cacheInfo.cache_stats;
      console.log(`总缓存请求: ${stats.hits + stats.misses}`);
      console.log(`缓存命中: ${stats.hits}`);
      console.log(`缓存未命中: ${stats.misses}`);
      console.log(`命中率: ${(stats.hits / (stats.hits + stats.misses) * 100).toFixed(2)}%`);
    }

    return cacheInfo;
  } catch (error) {
    console.error('获取缓存信息失败:', error);
  }
}
```

## ⚠️ 错误处理

### 错误响应格式

所有接口在出错时都会返回统一的错误格式：

```json
{
  "error": "错误描述信息",
  "code": "错误代码(可选)",
  "details": "详细错误信息(可选)"
}
```

### 常见错误代码

| HTTP状态码 | 错误类型 | 说明 |
|------------|----------|------|
| 400 | Bad Request | 请求参数错误 |
| 404 | Not Found | 接口不存在 |
| 500 | Internal Server Error | 服务器内部错误 |
| 503 | Service Unavailable | 服务暂时不可用 |

### JavaScript 错误处理示例

```javascript
// 通用错误处理函数
async function apiRequest(url, options = {}) {
  try {
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      },
      ...options
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || `HTTP ${response.status}: ${response.statusText}`);
    }

    return { success: true, data };
  } catch (error) {
    console.error('API请求失败:', error);
    return {
      success: false,
      error: error.message,
      status: error.status || 'unknown'
    };
  }
}

// 使用示例
async function safeTranslate(text, fromLang, toLang) {
  const result = await apiRequest('http://45.204.6.32:9000/api/translate', {
    method: 'POST',
    body: JSON.stringify({
      text,
      from_lang: fromLang,
      to_lang: toLang
    })
  });

  if (result.success) {
    return result.data.trans_result[0].dst;
  } else {
    console.error('翻译失败:', result.error);
    return null;
  }
}
```

### TypeScript 错误处理示例

```typescript
interface ApiResponse<T> {
  success: true;
  data: T;
}

interface ApiError {
  success: false;
  error: string;
  status: string | number;
}

type ApiResult<T> = ApiResponse<T> | ApiError;

class TranslationAPIClient {
  private baseUrl: string;

  constructor(baseUrl: string = 'http://45.204.6.32:9000') {
    this.baseUrl = baseUrl;
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<ApiResult<T>> {
    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        headers: {
          'Content-Type': 'application/json',
          ...options.headers
        },
        ...options
      });

      const data = await response.json();

      if (!response.ok) {
        return {
          success: false,
          error: data.error || `HTTP ${response.status}: ${response.statusText}`,
          status: response.status
        };
      }

      return { success: true, data };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : '网络错误',
        status: 'network_error'
      };
    }
  }

  async translate(text: string, fromLang: string = 'auto', toLang: string = 'zh'): Promise<ApiResult<TranslationResponse>> {
    return this.request<TranslationResponse>('/api/translate', {
      method: 'POST',
      body: JSON.stringify({
        text,
        from_lang: fromLang,
        to_lang: toLang
      })
    });
  }

  async getHealth(): Promise<ApiResult<HealthResponse>> {
    return this.request<HealthResponse>('/health');
  }
}

// 使用示例
const client = new TranslationAPIClient();

async function translateWithErrorHandling() {
  const result = await client.translate('你好世界', 'zh', 'en');

  if (result.success) {
    const translated = result.data.trans_result[0].dst;
    console.log(`翻译结果: ${translated}`);
  } else {
    console.error(`翻译失败 (${result.status}): ${result.error}`);

    // 根据错误类型进行不同处理
    switch (result.status) {
      case 400:
        console.log('请检查请求参数');
        break;
      case 500:
        console.log('服务器错误，请稍后重试');
        break;
      case 'network_error':
        console.log('网络连接失败，请检查网络');
        break;
      default:
        console.log('未知错误');
    }
  }
}
```

## 🔧 最佳实践

### 1. 请求频率控制

```javascript
// 请求节流器
class RequestThrottler {
  constructor(maxRequestsPerSecond = 10) {
    this.maxRequests = maxRequestsPerSecond;
    this.requests = [];
  }

  async throttle(requestFn) {
    const now = Date.now();

    // 清理1秒前的请求记录
    this.requests = this.requests.filter(time => now - time < 1000);

    if (this.requests.length >= this.maxRequests) {
      const waitTime = 1000 - (now - this.requests[0]);
      await new Promise(resolve => setTimeout(resolve, waitTime));
    }

    this.requests.push(now);
    return requestFn();
  }
}

// 使用示例
const throttler = new RequestThrottler(5); // 每秒最多5个请求

async function throttledTranslate(text) {
  return throttler.throttle(() =>
    fetch('http://45.204.6.32:9000/api/translate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, from_lang: 'zh', to_lang: 'en' })
    }).then(r => r.json())
  );
}
```

### 2. 批量请求优化

```javascript
// 批量请求管理器
class BatchRequestManager {
  constructor(batchSize = 10, delayMs = 100) {
    this.batchSize = batchSize;
    this.delayMs = delayMs;
    this.queue = [];
    this.processing = false;
  }

  async addRequest(text, fromLang = 'zh', toLang = 'en') {
    return new Promise((resolve, reject) => {
      this.queue.push({
        text,
        fromLang,
        toLang,
        resolve,
        reject
      });

      this.processQueue();
    });
  }

  async processQueue() {
    if (this.processing || this.queue.length === 0) return;

    this.processing = true;

    while (this.queue.length > 0) {
      const batch = this.queue.splice(0, this.batchSize);

      try {
        const items = batch.map((req, index) => ({
          text: req.text,
          id: `batch_${index}`
        }));

        const response = await fetch('http://45.204.6.32:9000/api/batch/translate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            items,
            from_lang: batch[0].fromLang,
            to_lang: batch[0].toLang
          })
        });

        const result = await response.json();

        // 分发结果
        batch.forEach((req, index) => {
          const itemResult = result.results[index];
          if (itemResult.trans_result) {
            req.resolve(itemResult.trans_result[0].dst);
          } else {
            req.reject(new Error('翻译失败'));
          }
        });

      } catch (error) {
        batch.forEach(req => req.reject(error));
      }

      // 批次间延迟
      if (this.queue.length > 0) {
        await new Promise(resolve => setTimeout(resolve, this.delayMs));
      }
    }

    this.processing = false;
  }
}

// 使用示例
const batchManager = new BatchRequestManager(10, 200);

// 多个翻译请求会自动合并为批量请求
Promise.all([
  batchManager.addRequest('你好'),
  batchManager.addRequest('世界'),
  batchManager.addRequest('朋友')
]).then(results => {
  console.log('批量翻译结果:', results);
});
```

## 📚 完整示例

### React Hook 示例

```typescript
import { useState, useEffect, useCallback } from 'react';

interface UseTranslationOptions {
  baseUrl?: string;
  defaultFromLang?: string;
  defaultToLang?: string;
}

interface TranslationState {
  loading: boolean;
  result: string | null;
  error: string | null;
}

export function useTranslation(options: UseTranslationOptions = {}) {
  const {
    baseUrl = 'http://45.204.6.32:9000',
    defaultFromLang = 'zh',
    defaultToLang = 'en'
  } = options;

  const [state, setState] = useState<TranslationState>({
    loading: false,
    result: null,
    error: null
  });

  const translate = useCallback(async (
    text: string,
    fromLang: string = defaultFromLang,
    toLang: string = defaultToLang
  ) => {
    setState({ loading: true, result: null, error: null });

    try {
      const response = await fetch(`${baseUrl}/api/translate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text,
          from_lang: fromLang,
          to_lang: toLang
        })
      });

      const data = await response.json();

      if (response.ok && data.trans_result) {
        setState({
          loading: false,
          result: data.trans_result[0].dst,
          error: null
        });
      } else {
        throw new Error(data.error || '翻译失败');
      }
    } catch (error) {
      setState({
        loading: false,
        result: null,
        error: error instanceof Error ? error.message : '未知错误'
      });
    }
  }, [baseUrl, defaultFromLang, defaultToLang]);

  return {
    ...state,
    translate
  };
}

// 使用示例
function TranslationComponent() {
  const { loading, result, error, translate } = useTranslation();

  const handleTranslate = () => {
    translate('你好世界');
  };

  return (
    <div>
      <button onClick={handleTranslate} disabled={loading}>
        {loading ? '翻译中...' : '翻译'}
      </button>
      {result && <p>翻译结果: {result}</p>}
      {error && <p style={{color: 'red'}}>错误: {error}</p>}
    </div>
  );
}
```

---

