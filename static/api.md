# API 文档

## 1. 获取支持语言列表

- **接口**：`GET /api/languages`
- **说明**：返回东盟十国官方语言代码及名称。
- **请求参数**：无
- **返回示例**：
```json
{
  "auto": "自动检测",
  "id": "印尼语",
  "ms": "马来语",
  "fil": "菲律宾语",
  "my": "缅甸语",
  "km": "高棉语",
  "lo": "老挝语",
  "th": "泰语",
  "vie": "越南语",
  "en": "英语",
  "zh": "中文",
  "ta": "泰米尔语"
}
```

---

## 2. 通用翻译接口（异步）

- **接口**：`POST /api/translate`
- **说明**：通用文本翻译，支持自定义源语言和目标语言，采用异步处理。
- **请求参数**（JSON）：
  - `text` (string, 必填)：要翻译的文本
  - `from_lang` (string, 可选，默认`auto`)：源语言代码
  - `to_lang` (string, 可选，默认`zh`)：目标语言代码
  - `font_size` (string, 可选)：翻译后建议的字体大小（如 `"24px"`），会原样返回
- **返回示例**：
```json
{
  "from": "zh",
  "to": "en",
  "trans_result": [
    { "src": "你好", "dst": "Hello" }
  ],
  "font_size": "28px"
}
```
- **使用示例**：
  - curl：
    ```bash
    curl -X POST http://localhost:8000/api/translate \
      -H "Content-Type: application/json" \
      -d '{"text": "你好世界", "from_lang": "zh", "to_lang": "en", "font_size": "28px"}'
    ```
  - JS：
    ```js
    fetch('/api/translate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: '你好世界', from_lang: 'zh', to_lang: 'en', font_size: '28px' })
    }).then(r => r.json()).then(console.log);
    ```

---

## 3. 批量翻译接口（异步）

- **接口**：`POST /api/batch/translate`
- **接口说明**：支持一次请求翻译多个文本，使用并行请求处理，提高处理速度
- **请求参数**（JSON）：
  - `items` (array, 必填)：要翻译的文本数组，每项包含：
    - `text` (string, 必填)：要翻译的文本内容
    - `id` (string, 可选)：客户端定义的ID，用于匹配结果
  - `from_lang` (string, 可选，默认`auto`)：源语言代码
  - `to_lang` (string, 可选，默认`zh`)：目标语言代码
  - `font_size` (string, 可选)：翻译后建议的字体大小
- **返回示例**：
```json
{
  "results": [
    {
      "from": "zh",
      "to": "en",
      "trans_result": [
        { "src": "你好", "dst": "Hello" }
      ],
      "id": "greeting",
      "index": 0
    },
    {
      "from": "zh", 
      "to": "en",
      "trans_result": [
        { "src": "世界", "dst": "World" }
      ],
      "id": "world",
      "index": 1
    }
  ],
  "total": 2,
  "success": 2,
  "failed": 0
}
```
- **使用示例**：
  - curl：
    ```bash
    curl -X POST http://localhost:8000/api/batch/translate \
      -H "Content-Type: application/json" \
      -d '{
        "items": [
          {"text": "你好", "id": "greeting"}, 
          {"text": "世界", "id": "world"}
        ], 
        "from_lang": "zh", 
        "to_lang": "en", 
        "font_size": "28px"
      }'
    ```
  - JS：
    ```js
    fetch('/api/batch/translate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        items: [
          {text: '你好', id: 'greeting'}, 
          {text: '世界', id: 'world'}
        ],
        from_lang: 'zh',
        to_lang: 'en',
        font_size: '28px'
      })
    }).then(r => r.json()).then(console.log);
    ```

---

## 4. 单一目标语言翻译接口（异步）

- **接口**：`POST /api/translate_to_xxx`
  - 其中 `xxx` 为目标语言英文名（见下表）
- **说明**：将中文翻译为指定目标语言，使用异步处理
- **请求参数**（JSON）：
  - `text` (string, 必填)：要翻译的中文文本
  - `font_size` (string, 可选)：翻译后建议的字体大小（如 `"24px"`），会原样返回
- **返回示例**：同通用翻译接口
- **支持的接口列表**：
  | 目标语言 | 接口路径                        | 语言代码 |
  |----------|---------------------------------|----------|
  | 印尼语   | /api/translate_to_indonesian    | id       |
  | 马来语   | /api/translate_to_malay         | ms       |
  | 菲律宾语 | /api/translate_to_filipino      | fil      |
  | 缅甸语   | /api/translate_to_burmese       | my       |
  | 高棉语   | /api/translate_to_khmer         | km       |
  | 老挝语   | /api/translate_to_lao           | lo       |
  | 泰语     | /api/translate_to_thai          | th       |
  | 越南语   | /api/translate_to_vietnamese    | vie      |
  | 英语     | /api/translate_to_english       | en       |
  | 泰米尔语 | /api/translate_to_tamil         | ta       |

- **使用示例**：
  - curl：
    ```bash
    curl -X POST http://localhost:8000/api/translate_to_thai \
      -H "Content-Type: application/json" \
      -d '{"text": "你好世界", "font_size": "32px"}'
    ```
  - JS：
    ```js
    fetch('/api/translate_to_thai', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: '你好世界', font_size: '32px' })
    }).then(r => r.json()).then(console.log);
    ```

## 5. 单一目标语言批量翻译接口（异步）

- **接口**：`POST /api/batch/translate_to_xxx`
  - 其中 `xxx` 为目标语言英文名（同上表）
- **说明**：批量将中文翻译为指定目标语言，使用异步并行处理
- **请求参数**（JSON）：
  - `items` (array, 必填)：要翻译的文本数组，每项可以是：
    - 字符串：直接作为要翻译的文本
    - 对象：包含 `text` 和可选的 `id` 字段
  - `font_size` (string, 可选)：翻译后建议的字体大小
- **返回示例**：同批量翻译接口
- **使用示例**：
  - curl：
    ```bash
    curl -X POST http://localhost:8000/api/batch/translate_to_thai \
      -H "Content-Type: application/json" \
      -d '{
        "items": [
          {"text": "你好", "id": "greeting"}, 
          {"text": "世界", "id": "world"},
          "中国"
        ], 
        "font_size": "32px"
      }'
    ```
  - JS：
    ```js
    fetch('/api/batch/translate_to_thai', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        items: [
          {text: '你好', id: 'greeting'}, 
          {text: '世界', id: 'world'},
          '中国'
        ],
        font_size: '32px'
      })
    }).then(r => r.json()).then(console.log);
    ```

---

## 6. 错误返回格式

- **单条翻译错误示例**：
```json
{
  "error": "文本不能为空"
}
```

- **批量翻译错误示例**：
```json
{
  "results": [
    {
      "from": "zh",
      "to": "en",
      "trans_result": [
        { "src": "你好", "dst": "Hello" }
      ],
      "id": "greeting",
      "index": 0
    }
  ],
  "total": 2,
  "success": 1,
  "failed": 1,
  "errors": [
    {
      "index": 1,
      "id": "empty",
      "error": "文本不能为空"
    }
  ]
}
```

---

## 7. 健康检查接口

- **接口**：`GET /health`
- **说明**：检查服务状态，包括Redis缓存连接状态
- **返回示例**：
```json
{
  "status": "ok",
  "timestamp": 1623456789.123,
  "cache": "connected"
}
```

---

## 8. 前端插件调用示例

```js
const translator = new BaiduTranslator('/api');

// 通用翻译
translator.translate('你好', 'zh', 'en', true, { fontSize: '30px' }).then(res => {
  document.getElementById('myDiv').innerText = res.translatedText;
  if (res.font_size) document.getElementById('myDiv').style.fontSize = res.font_size;
});

// 特定语言翻译
translator.translateToThai('你好', { fontSize: '24px' }).then(res => {
  document.getElementById('myDiv').innerText = res.translatedText;
  if (res.font_size) document.getElementById('myDiv').style.fontSize = res.font_size;
});

// 批量翻译
translator.batchTranslate(
  [{text: '你好', id: 'greeting'}, {text: '世界', id: 'world'}],
  'zh', 'en'
).then(res => {
  // 处理结果
  res.results.forEach(item => {
    document.getElementById(item.id).innerText = item.trans_result[0].dst;
  });
});
``` 