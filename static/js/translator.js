/**
 * BaiduTranslator 客户端库
 * 用于调用东盟十国翻译API
 * @version 2.0.0
 */
class BaiduTranslator {
  /**
   * 初始化翻译器
   * @param {string} baseUrl - API基础URL，例如 '/api' 或 'https://your-domain.com/api'
   */
  constructor(baseUrl = '/api') {
    this.baseUrl = baseUrl.endsWith('/') ? baseUrl.slice(0, -1) : baseUrl;
    this.languageNames = {
      'id': 'indonesian',  // 印尼语
      'ms': 'malay',       // 马来语
      'fil': 'filipino',   // 菲律宾语
      'my': 'burmese',     // 缅甸语
      'km': 'khmer',       // 高棉语
      'lo': 'lao',         // 老挝语
      'th': 'thai',        // 泰语
      'vie': 'vietnamese', // 越南语
      'en': 'english',     // 英语
      'zh': 'chinese',     // 中文
      'ta': 'tamil'        // 泰米尔语
    };
    this.languageCodes = {};
    // 反向映射，方便通过英文名查询代码
    Object.keys(this.languageNames).forEach(code => {
      this.languageCodes[this.languageNames[code]] = code;
    });
  }

  /**
   * 通用翻译方法
   * @param {string} text - 要翻译的文本
   * @param {string} fromLang - 源语言代码，默认'auto'自动检测
   * @param {string} toLang - 目标语言代码，默认'zh'中文
   * @param {boolean} useCache - 是否使用缓存，默认true
   * @param {Object} options - 附加选项
   * @param {string} options.fontSize - 字体大小，如"24px"
   * @returns {Promise<Object>} 翻译结果
   */
  async translate(text, fromLang = 'auto', toLang = 'zh', useCache = true, options = {}) {
    if (!text) {
      throw new Error('翻译文本不能为空');
    }

    const url = `${this.baseUrl}/translate`;
    const payload = {
      text,
      from_lang: fromLang,
      to_lang: toLang
    };

    if (options.fontSize) {
      payload.font_size = options.fontSize;
    }

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `请求失败: ${response.status}`);
      }

      const result = await response.json();
      // 简化返回结果，提供translatedText属性
      if (result.trans_result && result.trans_result.length > 0) {
        result.translatedText = result.trans_result[0].dst;
      }
      return result;
    } catch (error) {
      console.error('翻译出错:', error);
      throw error;
    }
  }

  /**
   * 批量翻译方法
   * @param {Array} items - 要翻译的文本数组，可以是字符串数组或{text, id}对象数组
   * @param {string} fromLang - 源语言代码，默认'auto'自动检测
   * @param {string} toLang - 目标语言代码，默认'zh'中文
   * @param {Object} options - 附加选项
   * @param {string} options.fontSize - 字体大小，如"24px"
   * @param {number} options.maxConcurrent - 最大并发请求数
   * @returns {Promise<Object>} 批量翻译结果
   */
  async batchTranslate(items, fromLang = 'auto', toLang = 'zh', options = {}) {
    if (!items || !items.length) {
      throw new Error('翻译文本列表不能为空');
    }

    // 转换输入格式
    const normalizedItems = items.map(item => {
      if (typeof item === 'string') {
        return { text: item };
      } else if (typeof item === 'object' && item.text) {
        return item;
      } else {
        throw new Error('输入项格式不正确，应为字符串或包含text属性的对象');
      }
    });

    const url = `${this.baseUrl}/batch/translate`;
    const payload = {
      items: normalizedItems,
      from_lang: fromLang,
      to_lang: toLang
    };

    if (options.fontSize) {
      payload.font_size = options.fontSize;
    }

    if (options.maxConcurrent) {
      payload.max_concurrent = options.maxConcurrent;
    }

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `请求失败: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('批量翻译出错:', error);
      throw error;
    }
  }

  /**
   * 获取支持的语言列表
   * @returns {Promise<Object>} 语言代码和名称的映射
   */
  async getLanguages() {
    try {
      const response = await fetch(`${this.baseUrl}/languages`);
      if (!response.ok) {
        throw new Error(`请求失败: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('获取语言列表出错:', error);
      throw error;
    }
  }

  /**
   * 健康检查
   * @returns {Promise<Object>} 服务状态信息
   */
  async healthCheck() {
    try {
      const response = await fetch(`${this.baseUrl.replace(/\/api$/, '')}/health`);
      if (!response.ok) {
        throw new Error(`健康检查失败: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('健康检查出错:', error);
      throw error;
    }
  }

  /**
   * 动态生成特定语言翻译方法
   * @param {string} langCode - 目标语言代码
   * @returns {Function} 翻译方法
   */
  _createTranslateToMethod(langCode) {
    const langName = this.languageNames[langCode];
    if (!langName) {
      throw new Error(`不支持的语言代码: ${langCode}`);
    }
    
    return async (text, options = {}) => {
      if (!text) {
        throw new Error('翻译文本不能为空');
      }

      const url = `${this.baseUrl}/translate_to_${langName}`;
      const payload = { text };
      
      if (options.fontSize) {
        payload.font_size = options.fontSize;
      }

      try {
        const response = await fetch(url, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(payload)
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.error || `请求失败: ${response.status}`);
        }

        const result = await response.json();
        // 简化返回结果，提供translatedText属性
        if (result.trans_result && result.trans_result.length > 0) {
          result.translatedText = result.trans_result[0].dst;
        }
        return result;
      } catch (error) {
        console.error(`翻译到${langName}出错:`, error);
        throw error;
      }
    };
  }

  /**
   * 动态生成特定语言批量翻译方法
   * @param {string} langCode - 目标语言代码
   * @returns {Function} 批量翻译方法
   */
  _createBatchTranslateToMethod(langCode) {
    const langName = this.languageNames[langCode];
    if (!langName) {
      throw new Error(`不支持的语言代码: ${langCode}`);
    }
    
    return async (items, options = {}) => {
      if (!items || !items.length) {
        throw new Error('翻译文本列表不能为空');
      }

      const url = `${this.baseUrl}/batch/translate_to_${langName}`;
      const payload = { items };
      
      if (options.fontSize) {
        payload.font_size = options.fontSize;
      }

      if (options.maxConcurrent) {
        payload.max_concurrent = options.maxConcurrent;
      }

      try {
        const response = await fetch(url, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(payload)
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.error || `请求失败: ${response.status}`);
        }

        return await response.json();
      } catch (error) {
        console.error(`批量翻译到${langName}出错:`, error);
        throw error;
      }
    };
  }
}

// 动态添加特定语言翻译方法
(function() {
  // 支持的语言代码
  const languages = {
    'id': 'indonesian',    // 印尼语
    'ms': 'malay',         // 马来语
    'fil': 'filipino',     // 菲律宾语
    'my': 'burmese',       // 缅甸语
    'km': 'khmer',         // 高棉语
    'lo': 'lao',           // 老挝语
    'th': 'thai',          // 泰语
    'vie': 'vietnamese',   // 越南语
    'en': 'english',       // 英语
    'zh': 'chinese',       // 中文
    'ta': 'tamil'          // 泰米尔语
  };

  // 为每种语言动态创建专用方法
  Object.keys(languages).forEach(langCode => {
    const langName = languages[langCode];
    // 首字母大写
    const capitalizedName = langName.charAt(0).toUpperCase() + langName.slice(1);
    
    // 添加单文本翻译方法，如 translateToEnglish()
    BaiduTranslator.prototype[`translateTo${capitalizedName}`] = function(text, options) {
      return this._createTranslateToMethod(langCode).call(this, text, options);
    };
    
    // 添加批量翻译方法，如 batchTranslateToEnglish()
    BaiduTranslator.prototype[`batchTranslateTo${capitalizedName}`] = function(items, options) {
      return this._createBatchTranslateToMethod(langCode).call(this, items, options);
    };
  });
})();

// 支持CommonJS和ES模块
if (typeof module !== 'undefined' && typeof module.exports !== 'undefined') {
  module.exports = BaiduTranslator;
} else {
  window.BaiduTranslator = BaiduTranslator;
}
