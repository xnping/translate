# Translator.js 插件 API 文档

Translator 是一个适用于东盟多语言场景的百度翻译 API 前端插件，支持通用翻译、东盟十国快捷翻译、DOM自动渲染、字体大小控制、批量翻译、语言检测等。
---

## CDN引入

```js
<script src="http://8.138.177.105:8000/static/js/translator.umd.min.js"></script>
```

---

---

## 初始化

```js
const translator = new BaiduTranslator('/api'); // apiUrl 可选，默认为 '/api'
```

---

## 方法列表

### 1. translate

通用文本翻译。

**签名：**
```js
translator.translate(text, fromLang = 'auto', toLang = 'zh', useCache = true, options = {})
```
- `text` (string, 必填)：要翻译的文本
- `fromLang` (string, 可选)：源语言代码，默认 'auto'
- `toLang` (string, 可选)：目标语言代码，默认 'zh'
- `useCache` (boolean, 可选)：是否使用缓存，默认 true
- `options` (object, 可选)：
  - `fontSize` (string)：建议字体大小（如 '24px'），会传给后端并在返回值中体现

**返回：** `Promise<object>`
- `translatedText` (string)：翻译后文本
- `fontSize` (string)：建议字体大小（如有）
- 其它：`from`, `to`, `raw`（原始返回）

**示例：**
```js
const res = await translator.translate('你好', 'zh', 'en', true, { fontSize: '28px' });
console.log(res.translatedText, res.fontSize);
```

---

### 2. translateToXxx

东盟十国快捷翻译方法。

**签名：**
```js
translator.translateToThai(text, options = {})
translator.translateToIndonesian(text, options = {})
// ... 其它语言同理
```
- `text` (string, 必填)：要翻译的中文文本
- `options` (object, 可选)：
  - `fontSize` (string)：建议字体大小
  - `targetElement` (HTMLElement)：指定DOM元素，自动渲染翻译结果和字体

**返回：** `Promise<object>`
- `translatedText` (string)：翻译后文本
- `fontSize` (string)：建议字体大小（如有）
- 其它：`from`, `to`, `raw`

**示例：**
```js
// 只获取翻译文本和建议字体
const res = await translator.translateToThai('你好', { fontSize: '32px' });
console.log(res.translatedText, res.fontSize);

// 自动渲染到DOM并设置字体
translator.translateToThai('你好', { targetElement: document.getElementById('myDiv'), fontSize: '32px' });
```

---

### 3. translateElement

翻译并渲染到指定 DOM 元素。

**签名：**
```js
translator.translateElement(element, fromLang = 'auto', toLang = 'zh', options = {})
```
- `element` (HTMLElement|string)：目标元素或选择器
- `fromLang` (string, 可选)：源语言，默认 'auto'
- `toLang` (string, 可选)：目标语言，默认 'zh'
- `options` (object, 可选)：
  - `fontSize` (string)：建议字体大小
  - `preserveOriginal` (boolean)：是否保留原文，默认 false
  - `originalAttribute` (string)：保存原文的属性名，默认 'data-original-text'

**返回：** `Promise<object>`
- `translatedText` (string)
- `fontSize` (string)
- 其它同上

**示例：**
```js
translator.translateElement('#myDiv', 'zh', 'en', { fontSize: '20px' });
```

---

### 4. translateElements

批量翻译页面元素。

**签名：**
```js
translator.translateElements(selector, fromLang = 'auto', toLang = 'zh', options = {})
```
- `selector` (string)：CSS选择器
- 其它参数同 translateElement

**返回：** `Promise<object[]>`

**示例：**
```js
translator.translateElements('.news-content', 'zh', 'en', { fontSize: '18px' });
```

---

### 5. batchTranslate

批量翻译文本。

**签名：**
```js
translator.batchTranslate(textArray, fromLang = 'auto', toLang = 'zh', options = {})
```
- `textArray` (string[])：要翻译的文本数组
- 其它参数同 translate

**返回：** `Promise<object[]>`

**示例：**
```js
translator.batchTranslate(['你好','世界'], 'zh', 'en', { fontSize: '22px' }).then(console.log);
```

---

### 6. getSupportedLanguages

获取支持的语言列表。

**签名：**
```js
translator.getSupportedLanguages()
```
- 无参数
- 返回：`Promise<object>`

**示例：**
```js
translator.getSupportedLanguages().then(console.log);
```

---

### 7. detectLanguage

自动检测文本语言。

**签名：**
```js
translator.detectLanguage(text)
```
- `text` (string)：要检测的文本
- 返回：`Promise<string>`（检测到的语言代码）

**示例：**
```js
translator.detectLanguage('hello').then(console.log);
```

---

### 8. clearCache

清除翻译缓存。

**签名：**
```js
translator.clearCache()
```

---

### 9. translateLongText

分段翻译长文本。

**签名：**
```js
translator.translateLongText(longText, fromLang = 'auto', toLang = 'zh', maxSegmentLength = 1000, options = {})
```
- `longText` (string)：长文本
- 其它参数同 translate
- 返回：`Promise<string>`（翻译后完整文本）

**示例：**
```js
translator.translateLongText('很长很长的中文...', 'zh', 'en', 800, { fontSize: '18px' }).then(console.log);
```

---

## 其它说明
- 支持 UMD/ESM/全局 window.BaiduTranslator
- 所有方法均为异步 Promise
- 建议配合后端 API font_size 字段使用，实现前后端字体风格一致 
