/**
 * BaiduTranslator - 百度翻译API前端插件（东盟十国快捷接口，自动字体支持，适合打包）
 *
 * 用法示例：
 *   const translator = new BaiduTranslator('/api');
 *   // 通用翻译
 *   translator.translate('你好', 'zh', 'en', true, { fontSize: '28px' }).then(res => ...);
 *   // 快捷翻译
 *   translator.translateToThai('你好', { fontSize: '32px', targetElement: document.getElementById('myDiv') });
 *   // 只设置字体，不操作DOM
 *   translator.translateToThai('你好', { fontSize: '24px' }).then(res => ...);
 *
 * 支持的快捷方法：
 *   translateToIndonesian(text, options)
 *   translateToMalay(text, options)
 *   translateToFilipino(text, options)
 *   translateToBurmese(text, options)
 *   translateToKhmer(text, options)
 *   translateToLao(text, options)
 *   translateToThai(text, options)
 *   translateToVietnamese(text, options)
 *   translateToEnglish(text, options)
 *   translateToTamil(text, options)
 *
 * options:
 *   fontSize: 可选，建议字体大小，会传给后端并自动设置到 targetElement
 *   targetElement: 可选，指定DOM元素，自动渲染翻译结果和字体
 *   其它 translateElement/translateElements 支持 preserveOriginal、originalAttribute
 *
 * 支持 UMD/ESM/全局 window.BaiduTranslator
 */
(function (root, factory) {
    if (typeof define === 'function' && define.amd) {
        define([], factory);
    } else if (typeof exports === 'object') {
        module.exports = factory();
    } else {
        root.BaiduTranslator = factory();
    }
}(typeof self !== 'undefined' ? self : this, function () {
class BaiduTranslator {
    /**
     * 初始化翻译器
     * @param {string} apiUrl - 后端API地址，默认为"/api"
     */
    constructor(apiUrl = "/api") {
        this.apiUrl = apiUrl;
        this.isBusy = false;
        
        // 常用语言名称和代码映射
        this.commonLanguages = {
            auto: "自动检测",
            zh: "中文",
            en: "英语", 
            jp: "日语",
            kor: "韩语",
            fra: "法语",
            spa: "西班牙语",
            ru: "俄语",
            de: "德语",
            it: "意大利语",
            th: "泰语",
            vie: "越南语",
            id: "印尼语",
            ms: "马来语",
            fil: "菲律宾语",
            my: "缅甸语",
            km: "高棉语",
            lo: "老挝语",
            ta: "泰米尔语"
        };
        
        // 缓存翻译结果
        this.translationCache = new Map();
    }

    /**
     * 获取翻译器是否处于繁忙状态
     * @returns {boolean} - 是否忙碌中
     */
    get busy() {
        return this.isBusy;
    }

    /**
     * 翻译文本
     * @param {string} text - 要翻译的文本
     * @param {string} fromLang - 源语言，默认为auto自动检测
     * @param {string} toLang - 目标语言，默认为zh中文
     * @param {boolean} useCache - 是否使用缓存，默认为true
     * @param {object} options - 选项
     * @returns {Promise<object>} - 翻译结果
     */
    async translate(text, fromLang = "auto", toLang = "zh", useCache = true, options = {}) {
        if (!text || text.trim() === "") {
            throw new Error("翻译文本不能为空");
        }

        const fontSize = options.fontSize;
        const cacheKey = `${text}|${fromLang}|${toLang}|${fontSize||''}`;
        if (useCache && this.translationCache.has(cacheKey)) {
            return this.translationCache.get(cacheKey);
        }

        this.isBusy = true;

        try {
            const body = {
                text,
                from_lang: fromLang,
                to_lang: toLang
            };
            if (fontSize) body.font_size = fontSize;
            const response = await fetch(`${this.apiUrl}/translate`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(body)
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(
                    `翻译请求失败: ${errorData.error || errorData.error_msg || response.statusText}`
                );
            }

            const result = await response.json();
            
            // 处理翻译结果
            if (result.error_code) {
                throw new Error(`翻译API错误: ${result.error_msg}`);
            }

            // 提取翻译结果
            if (result.trans_result && result.trans_result.length > 0) {
                const translationResult = {
                    originalText: text,
                    translatedText: result.trans_result.map(item => item.dst).join("\n"),
                    from: result.from,
                    to: result.to,
                    fontSize: result.font_size || fontSize,
                    raw: result
                };
                
                // 存入缓存
                if (useCache) {
                    this.translationCache.set(cacheKey, translationResult);
                    
                    // 限制缓存大小，防止内存泄漏
                    if (this.translationCache.size > 100) {
                        // 删除最早加入的缓存项
                        const oldestKey = this.translationCache.keys().next().value;
                        this.translationCache.delete(oldestKey);
                    }
                }
                
                return translationResult;
            } else {
                throw new Error("翻译结果格式异常");
            }
        } catch (error) {
            console.error("翻译错误:", error);
            throw error;
        } finally {
            this.isBusy = false;
        }
    }

    /**
     * 批量翻译文本
     * @param {string[]} textArray - 要翻译的文本数组
     * @param {string} fromLang - 源语言，默认为auto自动检测
     * @param {string} toLang - 目标语言，默认为zh中文
     * @returns {Promise<object[]>} - 翻译结果数组
     */
    async batchTranslate(textArray, fromLang = "auto", toLang = "zh") {
        if (!Array.isArray(textArray) || textArray.length === 0) {
            throw new Error("翻译文本数组不能为空");
        }

        // 批量翻译（并发请求）
        const promises = textArray.map(text => 
            this.translate(text, fromLang, toLang)
        );
        
        return Promise.all(promises);
    }

    /**
     * 获取支持的语言列表
     * @returns {Promise<object>} - 语言代码到名称的映射
     */
    async getSupportedLanguages() {
        try {
            const response = await fetch(`${this.apiUrl}/languages`);
            
            if (!response.ok) {
                throw new Error(`获取支持语言失败: ${response.statusText}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error("获取语言列表错误:", error);
            throw error;
        }
    }

    /**
     * 自动检测语言
     * @param {string} text - 要检测的文本
     * @returns {Promise<string>} - 检测到的语言代码
     */
    async detectLanguage(text) {
        if (!text || text.trim() === "") {
            throw new Error("检测文本不能为空");
        }
        
        try {
            // 使用翻译API检测语言
            const result = await this.translate(text, "auto", "zh");
            return result.from;
        } catch (error) {
            console.error("语言检测错误:", error);
            throw error;
        }
    }
    
    /**
     * 清除翻译缓存
     */
    clearCache() {
        this.translationCache.clear();
    }
    
    /**
     * 翻译HTML元素内容
     * @param {HTMLElement|string} element - HTML元素或选择器
     * @param {string} fromLang - 源语言，默认为auto自动检测
     * @param {string} toLang - 目标语言，默认为zh中文 
     * @param {object} options - 选项
     * @param {boolean} options.preserveOriginal - 是否保留原文，默认为false
     * @param {string} options.originalAttribute - 保存原文的属性名，默认为'data-original-text'
     * @param {string} options.fontSize - 可选，翻译后设置目标元素字体大小，仅对 DOM 元素翻译生效
     * @returns {Promise<object>} - 翻译结果
     */
    async translateElement(element, fromLang = "auto", toLang = "zh", options = {}) {
        // 默认选项
        const defaultOptions = {
            preserveOriginal: false, 
            originalAttribute: 'data-original-text',
            fontSize: undefined
        };
        
        const config = {...defaultOptions, ...options};
        
        // 获取元素
        const targetElement = typeof element === 'string' 
            ? document.querySelector(element) 
            : element;
            
        if (!targetElement) {
            throw new Error("找不到指定的HTML元素");
        }
        
        // 获取待翻译文本
        let textToTranslate = targetElement.innerText;
        if (!textToTranslate || textToTranslate.trim() === "") {
            throw new Error("元素内容为空");
        }
        
        // 如果启用了保留原文选项，先尝试恢复原文
        if (config.preserveOriginal) {
            const originalText = targetElement.getAttribute(config.originalAttribute);
            if (originalText) {
                textToTranslate = originalText;
            }
        }
        
        // 执行翻译
        try {
            const res = await this.translate(textToTranslate, fromLang, toLang, true, config);
            
            // 保存原文并更新元素内容
            if (config.preserveOriginal) {
                targetElement.setAttribute(config.originalAttribute, textToTranslate);
            }
            
            targetElement.innerText = res.translatedText;
            
            // 添加翻译元数据
            targetElement.setAttribute('data-translated', 'true');
            targetElement.setAttribute('data-from-lang', res.from);
            targetElement.setAttribute('data-to-lang', res.to);
            
            // 优先 options.fontSize，其次后端 font_size
            const size = config.fontSize || res.fontSize;
            if (size) targetElement.style.fontSize = size;
            
            return res;
        } catch (error) {
            console.error("元素翻译错误:", error);
            throw error;
        }
    }
    
    /**
     * 批量翻译页面元素
     * @param {string} selector - 选择器
     * @param {string} fromLang - 源语言，默认为auto自动检测
     * @param {string} toLang - 目标语言，默认为zh中文
     * @param {object} options - 翻译选项
     * @returns {Promise<object[]>} - 翻译结果数组
     */
    async translateElements(selector, fromLang = "auto", toLang = "zh", options = {}) {
        const elements = document.querySelectorAll(selector);
        if (elements.length === 0) {
            throw new Error("没有找到匹配的元素");
        }
        
        const promises = Array.from(elements).map(element => 
            this.translateElement(element, fromLang, toLang, options)
        );
        
        return Promise.all(promises);
    }
    
    /**
     * 分段翻译长文本
     * @param {string} longText - 长文本
     * @param {string} fromLang - 源语言，默认为auto自动检测
     * @param {string} toLang - 目标语言，默认为zh中文
     * @param {number} maxSegmentLength - 每段最大长度，默认为1000
     * @returns {Promise<string>} - 翻译后的完整文本
     */
    async translateLongText(longText, fromLang = "auto", toLang = "zh", maxSegmentLength = 1000) {
        if (!longText || longText.trim() === "") {
            throw new Error("翻译文本不能为空");
        }
        
        // 按句子分割文本
        const sentences = longText.match(/[^.!?。！？]+[.!?。！？]*/g) || [longText];
        
        // 将句子组合成段落，保证每段不超过最大长度
        const segments = [];
        let currentSegment = "";
        
        for (const sentence of sentences) {
            if ((currentSegment + sentence).length <= maxSegmentLength) {
                currentSegment += sentence;
            } else {
                if (currentSegment) {
                    segments.push(currentSegment);
                }
                currentSegment = sentence;
            }
        }
        
        // 添加最后一段
        if (currentSegment) {
            segments.push(currentSegment);
        }
        
        // 翻译每段文本
        const translatedSegments = await this.batchTranslate(segments, fromLang, toLang);
        
        // 合并翻译结果
        return translatedSegments.map(result => result.translatedText).join(" ");
    }

    // --- 东盟十国快捷接口 ---
    async translateToIndonesian(text, options = {}) {
        return this._translateToAsean('indonesian', text, options);
    }
    async translateToMalay(text, options = {}) {
        return this._translateToAsean('malay', text, options);
    }
    async translateToFilipino(text, options = {}) {
        return this._translateToAsean('filipino', text, options);
    }
    async translateToBurmese(text, options = {}) {
        return this._translateToAsean('burmese', text, options);
    }
    async translateToKhmer(text, options = {}) {
        return this._translateToAsean('khmer', text, options);
    }
    async translateToLao(text, options = {}) {
        return this._translateToAsean('lao', text, options);
    }
    async translateToThai(text, options = {}) {
        return this._translateToAsean('thai', text, options);
    }
    async translateToVietnamese(text, options = {}) {
        return this._translateToAsean('vietnamese', text, options);
    }
    async translateToEnglish(text, options = {}) {
        return this._translateToAsean('english', text, options);
    }
    async translateToTamil(text, options = {}) {
        return this._translateToAsean('tamil', text, options);
    }
    // 内部方法，调用后端快捷接口
    async _translateToAsean(langName, text, options = {}) {
        if (!text || text.trim() === "") {
            throw new Error("翻译文本不能为空");
        }
        const fontSize = options.fontSize;
        const url = `${this.apiUrl}/translate_to_${langName}`;
        this.isBusy = true;
        try {
            const body = { text };
            if (fontSize) body.font_size = fontSize;
            const response = await fetch(url, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(body)
            });
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(`翻译请求失败: ${errorData.error || errorData.error_msg || response.statusText}`);
            }
            const result = await response.json();
            if (result.error_code) {
                throw new Error(`翻译API错误: ${result.error_msg}`);
            }
            if (result.trans_result && result.trans_result.length > 0) {
                const translatedText = result.trans_result.map(item => item.dst).join("\n");
                // 自动渲染到DOM
                if (options.targetElement) {
                    options.targetElement.innerText = translatedText;
                    const size = result.font_size || fontSize;
                    if (size) options.targetElement.style.fontSize = size;
                }
                return {
                    originalText: text,
                    translatedText,
                    from: result.from,
                    to: result.to,
                    fontSize: result.font_size || fontSize,
                    raw: result
                };
            } else {
                throw new Error("翻译结果格式异常");
            }
        } catch (error) {
            console.error("翻译错误:", error);
            throw error;
        } finally {
            this.isBusy = false;
        }
    }
}
return BaiduTranslator;
})); 