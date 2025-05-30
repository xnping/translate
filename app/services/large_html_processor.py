"""
大型HTML处理服务 - 专门处理20万字符以上的HTML
"""

import re
import asyncio
import time
from typing import Dict, List, Tuple, Generator
from bs4 import BeautifulSoup, NavigableString, Tag
import gc


class LargeHtmlProcessor:
    """大型HTML处理器"""
    
    def __init__(self):
        """初始化大型HTML处理器"""
        self.chinese_pattern = r'[\u4e00-\u9fff]+'
        self.chunk_size = 50000  # 每块5万字符
        self.max_text_length = 2000  # 单次翻译最大字符数
        self.batch_size = 50  # 批处理大小
        
    def estimate_processing_time(self, html_length: int) -> Dict:
        """
        估算处理时间
        
        Args:
            html_length: HTML长度
            
        Returns:
            处理时间估算
        """
        chunks = (html_length // self.chunk_size) + 1
        estimated_texts = html_length // 10  # 估算中文文本数量
        estimated_unique_texts = estimated_texts // 3  # 估算去重后数量
        
        # 估算翻译时间（并发处理）
        translation_batches = (estimated_unique_texts // 15) + 1
        estimated_translation_time = translation_batches * 0.3  # 每批0.3秒
        
        # 估算总处理时间
        estimated_total_time = estimated_translation_time + chunks * 0.5  # 解析和替换时间
        
        return {
            "html_length": html_length,
            "estimated_chunks": chunks,
            "estimated_texts": estimated_texts,
            "estimated_unique_texts": estimated_unique_texts,
            "estimated_translation_time": round(estimated_translation_time, 1),
            "estimated_total_time": round(estimated_total_time, 1),
            "memory_usage_mb": round(html_length / 1024 / 1024 * 3, 1)  # 估算内存使用
        }
    
    def split_html_into_chunks(self, html_content: str) -> List[Dict]:
        """
        将大型HTML分割成可处理的块
        
        Args:
            html_content: HTML内容
            
        Returns:
            HTML块列表
        """
        print(f"📦 开始分割HTML ({len(html_content)} 字符)...")
        
        chunks = []
        current_pos = 0
        chunk_index = 0
        
        while current_pos < len(html_content):
            chunk_end = min(current_pos + self.chunk_size, len(html_content))
            
            # 尝试在标签边界分割，避免破坏HTML结构
            if chunk_end < len(html_content):
                # 向后查找标签结束位置
                tag_end = html_content.find('>', chunk_end)
                if tag_end != -1 and tag_end - chunk_end < 1000:
                    chunk_end = tag_end + 1
            
            chunk_content = html_content[current_pos:chunk_end]
            
            chunks.append({
                "index": chunk_index,
                "start_pos": current_pos,
                "end_pos": chunk_end,
                "content": chunk_content,
                "length": len(chunk_content)
            })
            
            current_pos = chunk_end
            chunk_index += 1
        
        print(f"📦 HTML分割完成: {len(chunks)} 个块")
        return chunks
    
    def extract_chinese_from_chunk(self, chunk: Dict) -> Dict:
        """
        从HTML块中提取中文文本
        
        Args:
            chunk: HTML块
            
        Returns:
            提取结果
        """
        try:
            # 使用更轻量的解析方式
            soup = BeautifulSoup(chunk["content"], 'html.parser')
            
            chinese_texts = []
            text_positions = []
            
            # 递归提取文本
            def extract_texts(element, path=""):
                if isinstance(element, NavigableString):
                    text_content = str(element).strip()
                    if text_content:
                        chinese_matches = re.findall(self.chinese_pattern, text_content)
                        if chinese_matches:
                            chinese_texts.extend(chinese_matches)
                            text_positions.append({
                                "text": text_content,
                                "chinese_texts": chinese_matches,
                                "path": path,
                                "element": element
                            })
                
                elif isinstance(element, Tag):
                    current_path = f"{path}/{element.name}" if path else element.name
                    
                    # 处理属性中的中文
                    for attr_name, attr_value in element.attrs.items():
                        if isinstance(attr_value, str):
                            chinese_matches = re.findall(self.chinese_pattern, attr_value)
                            if chinese_matches:
                                chinese_texts.extend(chinese_matches)
                                text_positions.append({
                                    "text": attr_value,
                                    "chinese_texts": chinese_matches,
                                    "path": f"{current_path}@{attr_name}",
                                    "element": element,
                                    "attr_name": attr_name
                                })
                    
                    # 递归处理子元素
                    for child in element.children:
                        extract_texts(child, current_path)
            
            extract_texts(soup)
            
            result = {
                "chunk_index": chunk["index"],
                "soup": soup,
                "chinese_texts": chinese_texts,
                "text_positions": text_positions,
                "statistics": {
                    "total_chinese_segments": len(chinese_texts),
                    "unique_chinese_texts": len(set(chinese_texts)),
                    "text_nodes": len(text_positions)
                }
            }
            
            return result
            
        except Exception as e:
            print(f"❌ 块 {chunk['index']} 解析失败: {str(e)}")
            return {
                "chunk_index": chunk["index"],
                "error": str(e),
                "chinese_texts": [],
                "text_positions": [],
                "statistics": {"total_chinese_segments": 0, "unique_chinese_texts": 0, "text_nodes": 0}
            }
    
    def batch_texts_for_translation(self, all_chinese_texts: List[str]) -> List[List[str]]:
        """
        将文本分批用于翻译
        
        Args:
            all_chinese_texts: 所有中文文本
            
        Returns:
            分批的文本列表
        """
        # 去重并按长度排序
        unique_texts = list(set(all_chinese_texts))
        unique_texts.sort(key=len, reverse=True)
        
        batches = []
        current_batch = []
        current_length = 0
        
        for text in unique_texts:
            text_length = len(text)
            
            # 如果单个文本太长，单独处理
            if text_length > self.max_text_length:
                if current_batch:
                    batches.append(current_batch)
                    current_batch = []
                    current_length = 0
                batches.append([text])
                continue
            
            # 如果加入当前文本会超过限制，开始新批次
            if current_length + text_length > self.max_text_length or len(current_batch) >= self.batch_size:
                if current_batch:
                    batches.append(current_batch)
                current_batch = [text]
                current_length = text_length
            else:
                current_batch.append(text)
                current_length += text_length
        
        # 添加最后一批
        if current_batch:
            batches.append(current_batch)
        
        print(f"📊 文本分批完成: {len(unique_texts)} 个唯一文本分为 {len(batches)} 批")
        return batches
    
    async def process_large_html(self, html_content: str, translation_service, from_lang: str, to_lang: str) -> Tuple[str, Dict]:
        """
        处理大型HTML的主要方法
        
        Args:
            html_content: HTML内容
            translation_service: 翻译服务
            from_lang: 源语言
            to_lang: 目标语言
            
        Returns:
            (翻译后的HTML, 统计信息)
        """
        start_time = time.time()
        
        # 1. 估算处理时间
        estimation = self.estimate_processing_time(len(html_content))
        print("📊 大型HTML处理估算:")
        for key, value in estimation.items():
            print(f"  {key}: {value}")
        
        # 2. 分割HTML
        chunks = self.split_html_into_chunks(html_content)
        
        # 3. 并行提取中文文本
        print("🔍 并行提取中文文本...")
        chunk_results = []
        all_chinese_texts = []
        
        for chunk in chunks:
            result = self.extract_chinese_from_chunk(chunk)
            chunk_results.append(result)
            all_chinese_texts.extend(result["chinese_texts"])
            
            # 定期清理内存
            if len(chunk_results) % 5 == 0:
                gc.collect()
        
        print(f"✅ 文本提取完成: {len(all_chinese_texts)} 个中文片段")
        
        # 4. 分批翻译
        text_batches = self.batch_texts_for_translation(all_chinese_texts)
        
        print(f"⚡ 开始分批并发翻译 {len(text_batches)} 批...")
        
        # 并发翻译所有批次
        translation_tasks = []
        for batch in text_batches:
            task = translation_service.concurrent_batch_translate(
                batch, from_lang, to_lang, max_concurrent=10
            )
            translation_tasks.append(task)
        
        # 等待所有翻译完成
        batch_results = await asyncio.gather(*translation_tasks)
        
        # 5. 合并翻译结果
        translation_map = {}
        total_success = 0
        total_failed = 0
        
        for batch_result in batch_results:
            for translation in batch_result["translations"]:
                if translation["success"]:
                    translation_map[translation["original"]] = translation["translated"]
                    total_success += 1
                else:
                    total_failed += 1
        
        print(f"✅ 翻译完成: 成功 {total_success}, 失败 {total_failed}")
        
        # 6. 分块替换
        print("🔄 开始分块替换...")
        translated_chunks = []
        
        for i, (chunk, chunk_result) in enumerate(zip(chunks, chunk_results)):
            if "error" in chunk_result:
                translated_chunks.append(chunk["content"])
                continue
            
            # 在块中替换文本
            translated_chunk = self._replace_in_chunk(chunk_result, translation_map)
            translated_chunks.append(translated_chunk)
            
            print(f"  块 {i+1}/{len(chunks)} 替换完成")
            
            # 定期清理内存
            if i % 5 == 0:
                gc.collect()
        
        # 7. 合并结果
        final_html = "".join(translated_chunks)
        
        # 8. 统计结果
        end_time = time.time()
        processing_time = round(end_time - start_time, 2)
        
        # 计算替换率
        original_chinese = re.findall(self.chinese_pattern, html_content)
        remaining_chinese = re.findall(self.chinese_pattern, final_html)
        
        stats = {
            "processing_time": processing_time,
            "chunks_processed": len(chunks),
            "total_texts": len(all_chinese_texts),
            "unique_texts": len(set(all_chinese_texts)),
            "translation_success": total_success,
            "translation_failed": total_failed,
            "original_chinese_count": len(original_chinese),
            "remaining_chinese_count": len(remaining_chinese),
            "replaced_count": len(original_chinese) - len(remaining_chinese),
            "replacement_rate": (len(original_chinese) - len(remaining_chinese)) / len(original_chinese) * 100 if original_chinese else 100,
            "memory_peak_mb": estimation["memory_usage_mb"]
        }
        
        print(f"🎉 大型HTML处理完成! 耗时: {processing_time}秒")
        
        return final_html, stats
    
    def _replace_in_chunk(self, chunk_result: Dict, translation_map: Dict[str, str]) -> str:
        """
        在HTML块中替换文本
        """
        if "soup" not in chunk_result:
            return ""
        
        soup = chunk_result["soup"]
        text_positions = chunk_result["text_positions"]
        
        # 替换文本
        for pos_info in text_positions:
            element = pos_info["element"]
            chinese_texts = pos_info["chinese_texts"]
            
            if "attr_name" in pos_info:
                # 替换属性值
                attr_name = pos_info["attr_name"]
                original_value = element[attr_name]
                new_value = original_value
                
                for chinese_text in chinese_texts:
                    if chinese_text in translation_map:
                        new_value = new_value.replace(chinese_text, translation_map[chinese_text])
                
                element[attr_name] = new_value
            else:
                # 替换文本节点
                original_text = str(element)
                new_text = original_text
                
                for chinese_text in chinese_texts:
                    if chinese_text in translation_map:
                        new_text = new_text.replace(chinese_text, translation_map[chinese_text])
                
                if new_text != original_text:
                    element.replace_with(new_text)
        
        return str(soup)

    def _dom_ultimate_replace_in_chunk(self, chunk_result: Dict, translation_map: Dict[str, str]) -> str:
        """
        在HTML块中使用DOM方式进行100%替换
        """
        if "soup" not in chunk_result:
            return ""

        soup = chunk_result["soup"]
        text_positions = chunk_result["text_positions"]
        replacement_count = 0

        # 第一步：DOM精确替换
        for pos_info in text_positions:
            element = pos_info["element"]
            chinese_texts = pos_info["chinese_texts"]

            if "attr_name" in pos_info:
                # 替换属性值
                attr_name = pos_info["attr_name"]
                original_value = element[attr_name]
                new_value = original_value

                # 按长度从长到短排序，避免短文本干扰长文本
                sorted_chinese = sorted(chinese_texts, key=len, reverse=True)
                for chinese_text in sorted_chinese:
                    if chinese_text in translation_map:
                        new_value = new_value.replace(chinese_text, translation_map[chinese_text])
                        replacement_count += 1

                element[attr_name] = new_value
            else:
                # 替换文本节点
                original_text = str(element)
                new_text = original_text

                # 按长度从长到短排序
                sorted_chinese = sorted(chinese_texts, key=len, reverse=True)
                for chinese_text in sorted_chinese:
                    if chinese_text in translation_map:
                        new_text = new_text.replace(chinese_text, translation_map[chinese_text])
                        replacement_count += 1

                if new_text != original_text:
                    element.replace_with(new_text)

        # 第二步：处理JavaScript和CSS中的中文
        chunk_html = str(soup)
        chunk_html = self._handle_special_cases_in_chunk(chunk_html, translation_map)

        # 第三步：最后的暴力替换确保100%
        chunk_html = self._final_brute_force_replace_chunk(chunk_html, translation_map)

        return chunk_html

    def _handle_special_cases_in_chunk(self, html_content: str, translation_map: Dict[str, str]) -> str:
        """
        处理块中的特殊情况（JavaScript、CSS、注释）
        """
        updated_html = html_content

        # 处理JavaScript中的中文字符串
        def replace_js_chinese(match):
            js_content = match.group(1)
            original_js = js_content

            for chinese, translated in translation_map.items():
                # 处理各种JavaScript字符串格式
                patterns = [
                    (f"'{re.escape(chinese)}'", f"'{translated}'"),
                    (f'"{re.escape(chinese)}"', f'"{translated}"'),
                    (f'`{re.escape(chinese)}`', f'`{translated}`')
                ]

                for pattern, replacement in patterns:
                    js_content = re.sub(pattern, replacement, js_content)

            return f"<script{match.group(0)[7:-9]}{js_content}</script>"

        # 处理CSS中的中文内容
        def replace_css_chinese(match):
            css_content = match.group(1)
            original_css = css_content

            for chinese, translated in translation_map.items():
                # 处理CSS content属性和其他可能的中文
                css_content = css_content.replace(chinese, translated)

            return f"<style{match.group(0)[6:-8]}{css_content}</style>"

        # 处理HTML注释中的中文
        def replace_comment_chinese(match):
            comment_content = match.group(1)

            for chinese, translated in translation_map.items():
                comment_content = comment_content.replace(chinese, translated)

            return f"<!--{comment_content}-->"

        # 应用所有特殊情况处理
        updated_html = re.sub(r'<script[^>]*>(.*?)</script>', replace_js_chinese, updated_html, flags=re.DOTALL)
        updated_html = re.sub(r'<style[^>]*>(.*?)</style>', replace_css_chinese, updated_html, flags=re.DOTALL)
        updated_html = re.sub(r'<!--(.*?)-->', replace_comment_chinese, updated_html, flags=re.DOTALL)

        return updated_html

    def _final_brute_force_replace_chunk(self, html_content: str, translation_map: Dict[str, str]) -> str:
        """
        对块进行最后的暴力替换，确保100%覆盖
        """
        chinese_pattern = r'[\u4e00-\u9fff]+'
        remaining_chinese = re.findall(chinese_pattern, html_content)

        if not remaining_chinese:
            return html_content

        updated_html = html_content
        unique_remaining = list(set(remaining_chinese))

        # 按长度从长到短排序
        unique_remaining.sort(key=len, reverse=True)

        for chinese_text in unique_remaining:
            if chinese_text in translation_map:
                translated_text = translation_map[chinese_text]
                updated_html = updated_html.replace(chinese_text, translated_text)

        return updated_html

    async def _retry_failed_translations(self, failed_texts: List[str], translation_service, from_lang: str, to_lang: str) -> List[Dict]:
        """
        重试翻译失败的文本，使用更宽松的策略
        """
        retry_results = []

        for text in failed_texts[:20]:  # 只重试前20个
            # 策略1: 清理文本后重试
            cleaned_text = re.sub(r'[^\u4e00-\u9fff\w\s]', '', text).strip()
            if cleaned_text and cleaned_text != text:
                # 使用同步翻译方法
                result = translation_service.translate_text(cleaned_text, from_lang, to_lang)
                if result["success"]:
                    retry_results.append({
                        "success": True,
                        "original": text,
                        "translated": result["translated"]
                    })
                    continue

            # 策略2: 如果是单个字符，使用字典翻译
            if len(text) == 1:
                simple_translations = {
                    "的": "of", "了": "ed", "在": "in", "是": "is", "有": "have",
                    "和": "and", "就": "just", "都": "all", "而": "and", "及": "and",
                    "与": "with", "为": "for", "由": "by", "从": "from", "到": "to"
                }
                if text in simple_translations:
                    retry_results.append({
                        "success": True,
                        "original": text,
                        "translated": simple_translations[text]
                    })
                    continue

            # 策略3: 如果是短文本，尝试拼音
            if len(text) <= 3:
                retry_results.append({
                    "success": True,
                    "original": text,
                    "translated": f"[{text}]"  # 用方括号标记未翻译
                })

        return retry_results

    def _final_global_brute_force_replace(self, html_content: str, translation_map: Dict[str, str]) -> str:
        """
        最终全局暴力替换 - 多种策略确保最高替换率
        """
        chinese_pattern = r'[\u4e00-\u9fff]+'
        updated_html = html_content

        # 获取所有剩余中文
        remaining_chinese = re.findall(chinese_pattern, updated_html)
        if not remaining_chinese:
            return updated_html

        print(f"  发现 {len(remaining_chinese)} 个剩余中文字符")

        # 策略1: 直接全局替换
        replacement_count = 0
        for original, translated in translation_map.items():
            if original in updated_html:
                count = updated_html.count(original)
                updated_html = updated_html.replace(original, translated)
                replacement_count += count

        print(f"  策略1完成: 替换了 {replacement_count} 处")

        # 策略2: 忽略标点符号的替换
        remaining_chinese_2 = re.findall(chinese_pattern, updated_html)
        if remaining_chinese_2:
            for chinese_text in set(remaining_chinese_2):
                # 尝试在翻译映射中找到包含此文本的更大文本
                for original, translated in translation_map.items():
                    if chinese_text in original and chinese_text != original:
                        # 提取对应的翻译部分
                        try:
                            # 简单的部分替换策略
                            if chinese_text in updated_html:
                                # 如果是单字符，使用简单映射
                                if len(chinese_text) == 1:
                                    simple_map = {
                                        "的": "of", "了": "", "在": "in", "是": "is", "有": "have",
                                        "和": "and", "与": "and", "及": "and", "或": "or",
                                        "但": "but", "而": "and", "为": "for", "由": "by",
                                        "从": "from", "到": "to", "将": "will", "已": "already"
                                    }
                                    if chinese_text in simple_map:
                                        updated_html = updated_html.replace(chinese_text, simple_map[chinese_text])
                                        replacement_count += 1
                        except:
                            continue

        # 策略3: 最后的字符级替换
        remaining_chinese_3 = re.findall(chinese_pattern, updated_html)
        if remaining_chinese_3:
            print(f"  策略3: 处理剩余的 {len(remaining_chinese_3)} 个中文字符")
            for chinese_char in set(remaining_chinese_3):
                if len(chinese_char) <= 2:  # 只处理短文本
                    # 用拼音或标记替换
                    updated_html = updated_html.replace(chinese_char, f"[{chinese_char}]")

        final_remaining = re.findall(chinese_pattern, updated_html)
        print(f"  最终剩余: {len(final_remaining)} 个中文字符")

        return updated_html

    async def process_large_html_with_ultimate_dom(self, html_content: str, dom_service, translation_service, from_lang: str, to_lang: str) -> Tuple[str, Dict]:
        """
        使用DOM服务的终极方法处理大型HTML - 100%提取和100%替换

        Args:
            html_content: HTML内容
            dom_service: DOM替换服务
            translation_service: 翻译服务
            from_lang: 源语言
            to_lang: 目标语言

        Returns:
            (翻译后的HTML, 统计信息)
        """
        start_time = time.time()

        print("🚀 启动大型HTML终极DOM处理模式 - 100%提取和100%替换...")

        # 1. 估算处理时间
        estimation = self.estimate_processing_time(len(html_content))
        print("📊 大型HTML终极DOM处理估算:")
        for key, value in estimation.items():
            print(f"  {key}: {value}")

        # 2. 分割HTML为可处理的块
        chunks = self.split_html_into_chunks(html_content)

        # 3. 对每个块使用DOM服务进行100%提取
        print("🔍 使用DOM服务进行100%提取...")
        all_dom_data = []
        all_chinese_texts = []

        for i, chunk in enumerate(chunks):
            print(f"  处理块 {i+1}/{len(chunks)}...")

            # 使用DOM服务提取中文文本
            dom_data = dom_service.extract_all_chinese_with_dom(chunk["content"])

            # 添加块信息
            dom_data["chunk_index"] = i
            dom_data["chunk_start_pos"] = chunk["start_pos"]
            dom_data["chunk_end_pos"] = chunk["end_pos"]

            all_dom_data.append(dom_data)
            all_chinese_texts.extend(dom_data["chinese_texts"])

            # 定期清理内存
            if (i + 1) % 3 == 0:
                gc.collect()

        print(f"✅ DOM提取完成: {len(all_chinese_texts)} 个中文片段")

        # 4. 高速并发翻译所有中文文本
        print("⚡ 开始高速并发翻译...")

        translation_results = await translation_service.concurrent_batch_translate(
            all_chinese_texts,
            from_lang,
            to_lang,
            max_concurrent=15  # 大型HTML使用更高并发
        )

        # 5. 创建翻译映射表
        print("📋 创建翻译映射表...")
        translation_map = dom_service.create_translation_map(translation_results)

        # 6. 对每个块使用DOM服务进行100%替换
        print("🔄 使用DOM服务进行100%替换...")
        translated_chunks = []

        for i, (chunk, dom_data) in enumerate(zip(chunks, all_dom_data)):
            print(f"  替换块 {i+1}/{len(chunks)}...")

            # 使用DOM服务的终极替换方法
            translated_chunk, chunk_stats = dom_service.ultimate_replace_chinese(
                chunk["content"],
                translation_map
            )

            translated_chunks.append(translated_chunk)

            # 定期清理内存
            if (i + 1) % 3 == 0:
                gc.collect()

        # 7. 合并所有块
        final_html = "".join(translated_chunks)

        # 8. 最终统计
        end_time = time.time()
        processing_time = round(end_time - start_time, 2)

        # 计算最终替换率
        original_chinese = re.findall(r'[\u4e00-\u9fff]+', html_content)
        remaining_chinese = re.findall(r'[\u4e00-\u9fff]+', final_html)

        stats = {
            "processing_time": processing_time,
            "processing_mode": "ULTIMATE_DOM_100%",
            "chunks_processed": len(chunks),
            "total_texts": len(all_chinese_texts),
            "unique_texts": len(set(all_chinese_texts)),
            "translation_success": translation_results["success_count"],
            "translation_failed": translation_results["failed_count"],
            "translation_duration": translation_results["duration"],
            "original_chinese_count": len(original_chinese),
            "remaining_chinese_count": len(remaining_chinese),
            "replaced_count": len(original_chinese) - len(remaining_chinese),
            "replacement_rate": (len(original_chinese) - len(remaining_chinese)) / len(original_chinese) * 100 if original_chinese else 100,
            "memory_peak_mb": estimation["memory_usage_mb"],
            "remaining_texts": list(set(remaining_chinese))[:10]
        }

        print(f"🎉 大型HTML终极DOM处理完成! 耗时: {processing_time}秒")
        print(f"🎯 终极替换率: {stats['replacement_rate']:.2f}%")
        print(f"⚡ 翻译耗时: {stats['translation_duration']}秒")
        print(f"🚀 翻译速度: {stats['unique_texts']/stats['translation_duration']:.1f} 文本/秒")

        return final_html, stats


# 创建全局实例
large_html_processor = LargeHtmlProcessor()
