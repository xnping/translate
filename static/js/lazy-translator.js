/**
 * 视图内翻译模块 - 只翻译当前可见的内容
 * @version 1.0.0
 */
class LazyTranslator {
  /**
   * 初始化懒加载翻译器
   * @param {BaiduTranslator} translator - 翻译API客户端实例
   * @param {Object} options - 配置选项
   */
  constructor(translator, options = {}) {
    this.translator = translator;
    this.options = Object.assign({
      // 默认配置
      batchSize: 5,         // 批量翻译的元素数量
      threshold: 0.1,       // 元素可见度阈值
      fromLang: 'auto',     // 源语言
      toLang: 'zh',         // 目标语言
      debounceDelay: 300,   // 防抖延迟(毫秒)
      selector: '[data-translate]', // 要翻译元素的选择器
      translateAttribute: 'data-translate-id', // 用于标识已翻译元素的属性
      originalTextAttribute: 'data-original-text', // 保存原始文本的属性
    }, options);

    // 初始化状态
    this.visibleElements = [];
    this.translationInProgress = false;
    this.observer = null;
    this.translatedElements = new Set();
    this.translationQueue = [];
    this.debouncedProcessQueue = this._debounce(this._processQueue.bind(this), this.options.debounceDelay);
    
    // 用于存储翻译结果的缓存
    this.cache = new Map();
  }

  /**
   * 初始化并开始监测可翻译元素
   */
  init() {
    console.log("LazyTranslator初始化，配置:", this.options);
    // 创建交叉观察器
    this.observer = new IntersectionObserver((entries) => {
      let hasNewVisibleElements = false;
      
      entries.forEach(entry => {
        const element = entry.target;
        const elementId = element.getAttribute(this.options.translateAttribute);
        
        if (entry.isIntersecting && !this.translatedElements.has(elementId)) {
          // 元素变为可见且未翻译
          this.visibleElements.push(element);
          hasNewVisibleElements = true;
        }
      });
      
      if (hasNewVisibleElements) {
        this.debouncedProcessQueue();
      }
    }, {
      threshold: this.options.threshold,
      rootMargin: '100px' // 提前100px开始加载
    });
    
    // 开始观察所有需要翻译的元素
    this._observeElements();
    
    // 添加滚动和调整大小的事件监听器以重新检查元素
    window.addEventListener('scroll', () => this.debouncedProcessQueue(), { passive: true });
    window.addEventListener('resize', () => this.debouncedProcessQueue(), { passive: true });
    
    return this;
  }
  
  /**
   * 观察页面上所有需要翻译的元素
   * @private
   */
  _observeElements() {
    const elements = document.querySelectorAll(this.options.selector);
    console.log(`找到${elements.length}个需要翻译的元素:`, elements);
    
    // 为每个元素分配唯一ID并开始观察
    elements.forEach((element, index) => {
      // 跳过已经处理过的元素
      if (element.hasAttribute(this.options.translateAttribute)) {
        console.log(`元素已处理过，跳过:`, element);
        return;
      }
      
      // 保存原始文本
      const originalText = element.textContent.trim();
      console.log(`元素${index}原始文本: "${originalText}"`);
      element.setAttribute(this.options.originalTextAttribute, originalText);
      
      // 分配唯一ID
      const elementId = `translate-${Date.now()}-${index}`;
      element.setAttribute(this.options.translateAttribute, elementId);
      
      // 开始观察此元素
      this.observer.observe(element);
    });
  }
  
  /**
   * 处理翻译队列
   * @private
   */
  async _processQueue() {
    if (this.translationInProgress || this.visibleElements.length === 0) {
      return;
    }
    
    this.translationInProgress = true;
    
    try {
      // 获取下一批要翻译的元素
      const batch = this.visibleElements.splice(0, this.options.batchSize);
      
      // 收集需要翻译的文本和对应的元素
      const textsToTranslate = [];
      const elementsMap = new Map();
      
      batch.forEach(element => {
        const text = element.getAttribute(this.options.originalTextAttribute);
        const elementId = element.getAttribute(this.options.translateAttribute);
        
        // 检查缓存中是否已有此文本的翻译
        if (this.cache.has(text)) {
          // 直接使用缓存的翻译结果
          element.textContent = this.cache.get(text);
          this.translatedElements.add(elementId);
        } else {
          // 添加到待翻译队列
          textsToTranslate.push({
            text,
            id: elementId
          });
          elementsMap.set(elementId, element);
        }
      });
      
      // 如果有需要翻译的文本，发送批量翻译请求
      if (textsToTranslate.length > 0) {
        console.log(`准备翻译${textsToTranslate.length}个元素，从${this.options.fromLang}到${this.options.toLang}`);
        console.log("翻译内容:", textsToTranslate);
        
        try {
          const result = await this.translator.batchTranslate(
            textsToTranslate,
            this.options.fromLang,
            this.options.toLang
          );
          
          console.log("翻译结果:", result);
          
          // 处理翻译结果
          if (result && result.results) {
            result.results.forEach(item => {
              console.log("处理翻译项:", item);
              
              if (item.success) {
                const element = elementsMap.get(item.id);
                if (element) {
                  const originalText = element.getAttribute(this.options.originalTextAttribute);
                  // 提取翻译文本
                  let translatedText = "";
                  
                  // 检查translatedText属性是否存在
                  if (item.translatedText) {
                    translatedText = item.translatedText;
                  } 
                  // 否则从trans_result中获取
                  else if (item.trans_result && item.trans_result.length > 0) {
                    console.log("trans_result完整内容:", item.trans_result);
                    translatedText = item.trans_result[0].dst;
                    console.log(`从trans_result提取翻译: ${item.trans_result[0].src} -> ${item.trans_result[0].dst}`);
                  } else {
                    console.log("未找到翻译结果:", item);
                  }
                  
                  // 确保我们有文本可以显示
                  if (translatedText) {
                    // 更新元素内容
                    console.log(`元素更新前内容: "${element.textContent}", 将更新为: "${translatedText}"`);
                    
                    // 直接赋值可能会失败，尝试多种方式更新内容
                    try {
                      // 方式1: 直接更新textContent
                      element.textContent = translatedText;
                      
                      // 方式2: 使用innerHTML（如果上面的方式不工作）
                      if (element.textContent !== translatedText) {
                        element.innerHTML = translatedText;
                      }
                      
                      // 方式3: 创建文本节点并替换
                      if (element.textContent !== translatedText) {
                        while (element.firstChild) {
                          element.removeChild(element.firstChild);
                        }
                        element.appendChild(document.createTextNode(translatedText));
                      }
                      
                      // 立即检查元素内容是否已更新
                      console.log(`元素更新后内容: "${element.textContent}"`);
                    } catch (err) {
                      console.error("更新DOM内容失败:", err);
                    }
                    
                    // 确保DOM已更新
                    setTimeout(() => {
                      console.log(`500ms后元素内容: "${element.textContent}"`);
                      // 如果还是失败，最后尝试
                      if (element.textContent !== translatedText) {
                        console.log("尝试最终DOM更新方法");
                        element.textContent = "";
                        element.textContent = translatedText;
                      }
                    }, 500);
                    
                    // 缓存翻译结果
                    this.cache.set(originalText, translatedText);
                    // 标记为已翻译
                    this.translatedElements.add(item.id);
                    
                    // 调试输出
                    console.log(`已翻译: ${originalText} -> ${translatedText}`);
                  }
                }
              }
            });
          }
        } catch (error) {
          console.error('翻译请求出错:', error);
        }
      }
      
      // 如果还有可见元素，继续处理
      if (this.visibleElements.length > 0) {
        setTimeout(() => this._processQueue(), 50);
      }
    } catch (error) {
      console.error('视图内翻译出错:', error);
    } finally {
      this.translationInProgress = false;
    }
  }
  
  /**
   * 切换语言
   * @param {string} toLang - 目标语言代码
   */
  changeLanguage(toLang) {
    console.log(`切换语言到: ${toLang}`);
    // 设置目标语言
    this.options.toLang = toLang;
    
    // 根据目标语言设置源语言
    // 如果目标语言是中文，源语言设为英文；否则源语言设为中文
    this.options.fromLang = toLang === 'zh' ? 'en' : 'zh';
    console.log(`源语言设置为: ${this.options.fromLang}，目标语言设置为: ${this.options.toLang}`);
    
    // 清除缓存和翻译状态
    this.cache.clear();
    this.translatedElements.clear();
    
    // 重置所有元素状态
    document.querySelectorAll(this.options.selector).forEach(element => {
      const originalText = element.getAttribute(this.options.originalTextAttribute);
      if (originalText) {
        element.textContent = originalText;
      }
    });
    
    // 重新开始观察元素
    this._observeElements();
    
    // 立即处理当前可见的元素，不使用防抖
    this._processQueue();
  }
  
  /**
   * 对函数进行防抖处理
   * @private
   */
  _debounce(func, wait) {
    let timeout;
    return function() {
      const context = this;
      const args = arguments;
      clearTimeout(timeout);
      timeout = setTimeout(() => func.apply(context, args), wait);
    };
  }
  
  /**
   * 手动触发翻译检查
   * 在动态加载内容后调用
   */
  refresh() {
    this._observeElements();
    this.debouncedProcessQueue();
  }
} 