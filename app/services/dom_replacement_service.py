"""
基于DOM解析的精确HTML替换服务 - 100%替换率方案
"""

import re
from typing import Dict, List, Tuple
from bs4 import BeautifulSoup, NavigableString, Tag


class DomReplacementService:
    """基于DOM解析的精确替换服务"""
    
    def __init__(self):
        """初始化DOM替换服务"""
        self.chinese_pattern = r'[\u4e00-\u9fff]+'
    
    def extract_all_chinese_with_dom(self, html_body: str) -> Dict:
        """
        使用DOM解析提取所有中文文本，包括精确位置信息
        
        Args:
            html_body: HTML内容
            
        Returns:
            完整的中文文本提取结果
        """
        print("🔍 使用DOM解析提取中文文本...")
        
        # 使用BeautifulSoup解析HTML
        soup = BeautifulSoup(html_body, 'html.parser')
        
        chinese_texts = []
        text_nodes = []
        
        # 递归遍历所有文本节点
        def extract_from_element(element, path=""):
            if isinstance(element, NavigableString):
                # 处理文本节点
                text_content = str(element).strip()
                if text_content:
                    chinese_matches = re.findall(self.chinese_pattern, text_content)
                    if chinese_matches:
                        text_info = {
                            'content': text_content,
                            'chinese_texts': chinese_matches,
                            'path': path,
                            'element': element,
                            'parent': element.parent
                        }
                        text_nodes.append(text_info)
                        chinese_texts.extend(chinese_matches)
            
            elif isinstance(element, Tag):
                # 处理标签节点
                current_path = f"{path}/{element.name}" if path else element.name
                
                # 处理标签的属性中的中文
                for attr_name, attr_value in element.attrs.items():
                    if isinstance(attr_value, str):
                        chinese_matches = re.findall(self.chinese_pattern, attr_value)
                        if chinese_matches:
                            attr_info = {
                                'content': attr_value,
                                'chinese_texts': chinese_matches,
                                'path': f"{current_path}@{attr_name}",
                                'element': element,
                                'attr_name': attr_name
                            }
                            text_nodes.append(attr_info)
                            chinese_texts.extend(chinese_matches)
                
                # 递归处理子元素
                for child in element.children:
                    extract_from_element(child, current_path)
        
        # 开始提取
        extract_from_element(soup)
        
        result = {
            'soup': soup,
            'text_nodes': text_nodes,
            'chinese_texts': chinese_texts,
            'statistics': {
                'total_text_nodes': len(text_nodes),
                'total_chinese_segments': len(chinese_texts),
                'unique_chinese_texts': len(set(chinese_texts))
            }
        }
        
        print(f" DOM提取完成: {len(text_nodes)} 个文本节点, {len(chinese_texts)} 个中文片段")
        return result
    
    def replace_chinese_in_dom(self, dom_data: Dict, translation_map: Dict[str, str]) -> str:
        """
        在DOM中精确替换中文文本
        
        Args:
            dom_data: DOM提取的数据
            translation_map: 翻译映射表
            
        Returns:
            替换后的HTML字符串
        """
        print("开始DOM精确替换...")
        
        soup = dom_data['soup']
        text_nodes = dom_data['text_nodes']
        replacement_count = 0
        
        # 处理每个文本节点
        for node_info in text_nodes:
            content = node_info['content']
            chinese_texts = node_info['chinese_texts']
            element = node_info['element']
            path = node_info['path']
            
            # 替换文本内容
            new_content = content
            node_replacements = 0
            
            # 按长度从长到短排序，避免短文本干扰长文本
            sorted_chinese = sorted(chinese_texts, key=len, reverse=True)
            
            for chinese_text in sorted_chinese:
                if chinese_text in translation_map:
                    translated_text = translation_map[chinese_text]
                    if chinese_text in new_content:
                        new_content = new_content.replace(chinese_text, translated_text)
                        node_replacements += 1
            
            # 如果内容有变化，更新DOM
            if node_replacements > 0 and new_content != content:
                if 'attr_name' in node_info:
                    # 更新属性值
                    attr_name = node_info['attr_name']
                    element[attr_name] = new_content
                    print(f"  ✅ 属性替换: {path} = '{content[:30]}...' → '{new_content[:30]}...'")
                else:
                    # 更新文本节点
                    element.replace_with(new_content)
                    print(f"  ✅ 文本替换: {path} = '{content[:30]}...' → '{new_content[:30]}...'")
                
                replacement_count += node_replacements
        
        print(f"✅ DOM替换完成: 总共替换了 {replacement_count} 处文本")
        
        # 返回更新后的HTML
        return str(soup)
    
    def handle_special_cases(self, html_content: str, translation_map: Dict[str, str]) -> str:
        """
        处理特殊情况的中文文本
        
        Args:
            html_content: HTML内容
            translation_map: 翻译映射表
            
        Returns:
            处理后的HTML
        """
        print("🔧 处理特殊情况...")
        
        updated_html = html_content
        special_replacements = 0
        
        # 1. 处理JavaScript中的中文字符串
        def replace_js_chinese(match):
            nonlocal special_replacements
            js_content = match.group(1)
            original_js = js_content
            
            # 在JavaScript字符串中查找并替换中文
            for chinese, translated in translation_map.items():
                # 处理单引号字符串
                pattern1 = f"'{re.escape(chinese)}'"
                replacement1 = f"'{translated}'"
                js_content = re.sub(pattern1, replacement1, js_content)
                
                # 处理双引号字符串
                pattern2 = f'"{re.escape(chinese)}"'
                replacement2 = f'"{translated}"'
                js_content = re.sub(pattern2, replacement2, js_content)
                
                # 处理模板字符串
                pattern3 = f'`{re.escape(chinese)}`'
                replacement3 = f'`{translated}`'
                js_content = re.sub(pattern3, replacement3, js_content)
            
            if js_content != original_js:
                special_replacements += 1
                print(f"  ✅ JavaScript替换完成")
            
            return f"<script{match.group(0)[7:-9]}{js_content}</script>"
        
        # 2. 处理CSS中的中文内容
        def replace_css_chinese(match):
            nonlocal special_replacements
            css_content = match.group(1)
            original_css = css_content
            
            # 在CSS content属性中查找并替换中文
            for chinese, translated in translation_map.items():
                # 处理content属性
                pattern = f'content:\\s*["\']([^"\']*{re.escape(chinese)}[^"\']*)["\']'
                def replace_content(m):
                    return f'content: "{m.group(1).replace(chinese, translated)}"'
                css_content = re.sub(pattern, replace_content, css_content)
            
            if css_content != original_css:
                special_replacements += 1
                print(f"  ✅ CSS替换完成")
            
            return f"<style{match.group(0)[6:-8]}{css_content}</style>"
        
        # 应用特殊处理
        updated_html = re.sub(r'<script[^>]*>(.*?)</script>', replace_js_chinese, updated_html, flags=re.DOTALL)
        updated_html = re.sub(r'<style[^>]*>(.*?)</style>', replace_css_chinese, updated_html, flags=re.DOTALL)
        
        # 3. 处理HTML注释中的中文
        def replace_comment_chinese(match):
            nonlocal special_replacements
            comment_content = match.group(1)
            original_comment = comment_content
            
            for chinese, translated in translation_map.items():
                if chinese in comment_content:
                    comment_content = comment_content.replace(chinese, translated)
            
            if comment_content != original_comment:
                special_replacements += 1
                print(f"  ✅ 注释替换完成")
            
            return f"<!--{comment_content}-->"
        
        updated_html = re.sub(r'<!--(.*?)-->', replace_comment_chinese, updated_html, flags=re.DOTALL)
        
        print(f"✅ 特殊情况处理完成: {special_replacements} 处")
        return updated_html
    
    def ultimate_replace_chinese(self, html_body: str, translation_map: Dict[str, str]) -> Tuple[str, Dict]:
        """
        终极中文替换方案 - 追求100%替换率
        
        Args:
            html_body: 原始HTML
            translation_map: 翻译映射表
            
        Returns:
            (替换后的HTML, 统计信息)
        """
        print("🚀 启动终极替换方案...")
        
        # 第一步：DOM精确提取和替换
        dom_data = self.extract_all_chinese_with_dom(html_body)
        html_after_dom = self.replace_chinese_in_dom(dom_data, translation_map)
        
        # 第二步：处理特殊情况
        html_after_special = self.handle_special_cases(html_after_dom, translation_map)
        
        # 第三步：最后的暴力替换
        html_final = self._final_brute_force_replace(html_after_special, translation_map)
        
        # 统计结果
        original_chinese = re.findall(self.chinese_pattern, html_body)
        remaining_chinese = re.findall(self.chinese_pattern, html_final)
        
        stats = {
            'original_chinese_count': len(original_chinese),
            'remaining_chinese_count': len(remaining_chinese),
            'replaced_count': len(original_chinese) - len(remaining_chinese),
            'replacement_rate': (len(original_chinese) - len(remaining_chinese)) / len(original_chinese) * 100 if original_chinese else 100,
            'remaining_texts': list(set(remaining_chinese))
        }
        
        print(f"🎉 终极替换完成! 替换率: {stats['replacement_rate']:.2f}%")
        
        return html_final, stats
    
    def _final_brute_force_replace(self, html_content: str, translation_map: Dict[str, str]) -> str:
        """
        最后的暴力替换 - 确保100%覆盖
        """
        print("💪 执行最后的暴力替换...")
        
        updated_html = html_content
        brute_replacements = 0
        
        # 获取所有剩余的中文
        remaining_chinese = re.findall(self.chinese_pattern, updated_html)
        unique_remaining = list(set(remaining_chinese))
        
        for chinese_text in unique_remaining:
            if chinese_text in translation_map:
                translated_text = translation_map[chinese_text]
                count_before = updated_html.count(chinese_text)
                if count_before > 0:
                    updated_html = updated_html.replace(chinese_text, translated_text)
                    brute_replacements += count_before
                    print(f"  💥 暴力替换: '{chinese_text}' → '{translated_text}' ({count_before}处)")
        
        print(f"💪 暴力替换完成: {brute_replacements} 处")
        return updated_html

    def create_translation_map(self, translation_results: Dict) -> Dict[str, str]:
        """
        创建翻译映射表，处理重复翻译结果

        Args:
            translation_results: 百度翻译返回的结果

        Returns:
            原文到译文的映射字典
        """
        translation_map = {}
        translation_counts = {}  # 统计每个翻译的出现次数

        for translation in translation_results.get('translations', []):
            if translation.get('success', False):
                original = translation['original']
                translated = translation['translated']

                # 如果已存在该原文的翻译，选择更好的翻译
                if original in translation_map:
                    # 统计翻译出现次数，选择最常见的翻译
                    if original not in translation_counts:
                        translation_counts[original] = {}

                    current_translation = translation_map[original]
                    if current_translation not in translation_counts[original]:
                        translation_counts[original][current_translation] = 0
                    if translated not in translation_counts[original]:
                        translation_counts[original][translated] = 0

                    translation_counts[original][current_translation] += 1
                    translation_counts[original][translated] += 1

                    # 选择出现次数最多的翻译，如果次数相同则选择更长的翻译
                    best_translation = max(
                        translation_counts[original].items(),
                        key=lambda x: (x[1], len(x[0]))  # 先按次数，再按长度
                    )[0]

                    translation_map[original] = best_translation
                    print(f"  🔄 更新翻译: '{original}' → '{best_translation}' (出现{translation_counts[original][best_translation]}次)")
                else:
                    translation_map[original] = translated
                    translation_counts[original] = {translated: 1}

        print(f"📋 创建翻译映射表: {len(translation_map)} 个唯一映射关系")

        # 打印重复翻译统计
        repeated_translations = {k: v for k, v in translation_counts.items() if len(v) > 1}
        if repeated_translations:
            print(f"📊 发现 {len(repeated_translations)} 个原文有多种翻译:")
            for original, translations in list(repeated_translations.items())[:5]:
                print(f"  '{original}': {translations}")

        return translation_map


# 创建全局实例
dom_replacement_service = DomReplacementService()
