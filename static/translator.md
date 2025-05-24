# Translator.js API 文档

`Translator.js` 是一个适用于东盟多语言场景的翻译 API 前端插件，基于异步翻译服务，支持通用翻译、东盟十国快捷翻译、批量翻译、缓存控制等功能。

## 初始化

```js
// 初始化翻译器
const translator = new BaiduTranslator('/api'); // 默认API路径为 '/api'
```

## 核心方法

### 1. 通用翻译

```js
translator.translate(text, fromLang = 'auto', toLang = 'zh', useCache = true, options = {})
  .then(result => console.log(result.translatedText));
```

**参数说明：**
- `text` (string, 必填)：要翻译的文本
- `fromLang` (string, 可选)：源语言代码，默认 'auto'
- `toLang` (string, 可选)：目标语言代码，默认 'zh'
- `useCache` (boolean, 可选)：是否使用缓存，默认 true
- `options` (object, 可选)：
  - `fontSize` (string)：建议字体大小（如 '24px'）

**返回值：** 
```json
{
  "from": "zh",
  "to": "en",
  "trans_result": [{ "src": "你好", "dst": "Hello" }],
  "font_size": "24px",
  "translatedText": "Hello" // 便捷访问属性
}
```

### 2. 批量翻译

```js
translator.batchTranslate(items, fromLang = 'auto', toLang = 'zh', options = {})
  .then(results => console.log(results));
```

**参数说明：**
- `items` (Array, 必填)：要翻译的文本数组，可以是：
  - 字符串数组: `['文本1', '文本2']`
  - 对象数组: `[{text: '文本1', id: 'id1'}, {text: '文本2', id: 'id2'}]`
- `fromLang` (string, 可选)：源语言代码，默认 'auto'
- `toLang` (string, 可选)：目标语言代码，默认 'zh'
- `options` (object, 可选)：
  - `fontSize` (string)：建议字体大小
  - `maxConcurrent` (number)：最大并发请求数

**返回值：**
```json
{
  "results": [
    {
      "from": "zh",
      "to": "en",
      "trans_result": [{ "src": "你好", "dst": "Hello" }],
      "id": "id1",
      "index": 0
    },
    ...
  ],
  "total": 2,
  "success": 2,
  "failed": 0
}
```

### 3. 获取支持的语言列表

```js
translator.getLanguages()
  .then(languages => console.log(languages));
```

**返回值：**
```json
{
  "auto": "自动检测",
  "zh": "中文",
  "en": "英语",
  "th": "泰语",
  ...
}
```

### 4. 健康检查

```js
translator.healthCheck()
  .then(status => console.log(status));
```

**返回值：**
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "cache": {
    "connected": true,
    "hit_rate": 0.75
  }
}
```

## 快捷翻译方法

### 1. 特定语言翻译

以下方法自动将中文翻译为目标语言：

```js
// 翻译到英语
translator.translateToEnglish('你好世界', { fontSize: '24px' })
  .then(result => console.log(result.translatedText));

// 翻译到泰语
translator.translateToThai('你好世界', { fontSize: '32px' })
  .then(result => console.log(result.translatedText));
```

**支持的方法：**
- `translateToIndonesian(text, options)` - 翻译到印尼语
- `translateToMalay(text, options)` - 翻译到马来语
- `translateToFilipino(text, options)` - 翻译到菲律宾语
- `translateToBurmese(text, options)` - 翻译到缅甸语
- `translateToKhmer(text, options)` - 翻译到高棉语
- `translateToLao(text, options)` - 翻译到老挝语
- `translateToThai(text, options)` - 翻译到泰语
- `translateToVietnamese(text, options)` - 翻译到越南语
- `translateToEnglish(text, options)` - 翻译到英语
- `translateToChinese(text, options)` - 翻译到中文
- `translateToTamil(text, options)` - 翻译到泰米尔语

### 2. 特定语言批量翻译

以下方法自动批量将中文翻译为目标语言：

```js
// 批量翻译到英语
translator.batchTranslateToEnglish([
  { text: '你好', id: 'greeting' },
  { text: '世界', id: 'world' },
  '中国'  // 直接使用字符串也可以
], { fontSize: '24px', maxConcurrent: 5 })
  .then(results => console.log(results));
```

**支持的方法：**
- `batchTranslateToIndonesian(items, options)` - 批量翻译到印尼语
- `batchTranslateToMalay(items, options)` - 批量翻译到马来语
- `batchTranslateToFilipino(items, options)` - 批量翻译到菲律宾语
- `batchTranslateToBurmese(items, options)` - 批量翻译到缅甸语
- `batchTranslateToKhmer(items, options)` - 批量翻译到高棉语
- `batchTranslateToLao(items, options)` - 批量翻译到老挝语
- `batchTranslateToThai(items, options)` - 批量翻译到泰语
- `batchTranslateToVietnamese(items, options)` - 批量翻译到越南语
- `batchTranslateToEnglish(items, options)` - 批量翻译到英语
- `batchTranslateToChinese(items, options)` - 批量翻译到中文
- `batchTranslateToTamil(items, options)` - 批量翻译到泰米尔语

## 实用示例

### 前端展示翻译结果并设置字体大小

```js
// 单文本翻译
translator.translateToThai('你好世界', { fontSize: '32px' })
  .then(result => {
    const element = document.getElementById('greeting');
    element.innerText = result.translatedText;
    if (result.font_size) {
      element.style.fontSize = result.font_size;
    }
  });

// 批量翻译
translator.batchTranslateToEnglish([
  { text: '你好', id: 'greeting' },
  { text: '世界', id: 'world' }
], { fontSize: '24px' })
  .then(response => {
    // 处理结果
    response.results.forEach(result => {
      const element = document.getElementById(result.id);
      if (element) {
        element.innerText = result.trans_result[0].dst;
        if (response.font_size) {
          element.style.fontSize = response.font_size;
        }
      }
    });
  });
```

### 自定义错误处理

```js
translator.translate('你好', 'zh', 'en')
  .then(result => {
    // 成功处理
    console.log(result.translatedText);
  })
  .catch(error => {
    // 错误处理
    console.error('翻译失败:', error.message);
    showErrorToUser('翻译服务暂时不可用，请稍后再试');
  });
```

## 支持语言列表

| 语言代码 | 语言名称  | 方法后缀      |
|---------|----------|--------------|
| auto    | 自动检测  | -            |
| zh      | 中文      | Chinese      |
| en      | 英语      | English      |
| id      | 印尼语    | Indonesian   |
| ms      | 马来语    | Malay        |
| fil     | 菲律宾语  | Filipino     |
| my      | 缅甸语    | Burmese      |
| km      | 高棉语    | Khmer        |
| lo      | 老挝语    | Lao          |
| th      | 泰语      | Thai         |
| vie     | 越南语    | Vietnamese   |
| ta      | 泰米尔语  | Tamil        |
