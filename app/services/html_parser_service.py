"""
HTML解析服务
"""

import re
from typing import List, Dict


class HtmlParserService:
    """HTML解析服务类"""
    
    def __init__(self):
        """初始化HTML解析服务"""
        # 中文字符正则表达式
        self.chinese_pattern = r'[\u4e00-\u9fff]+'
        # HTML标签正则表达式
        self.tag_pattern = r'<([a-zA-Z][a-zA-Z0-9]*)\b[^>]*>(.*?)</\1>'
    
    def extract_tags_and_chinese(self, html_body: str) -> Dict:
        """
        从HTML body中提取所有标签和中文文本
        
        Args:
            html_body: HTML页面body内容
            
        Returns:
            提取结果字典
        """
        result = {
            "all_tags": [],           # 所有标签信息
            "chinese_texts": [],      # 所有中文文本
            "tag_chinese_map": {},    # 标签与中文的映射关系
            "statistics": {}          # 统计信息
        }
        
        # 1. 提取所有HTML标签及其内容
        tag_matches = re.findall(self.tag_pattern, html_body, re.DOTALL)
        
        tag_index = 0
        for tag_name, tag_content in tag_matches:
            tag_index += 1
            
            # 清理标签内容，移除嵌套的HTML标签
            clean_content = re.sub(r'<[^>]+>', '', tag_content)
            clean_content = clean_content.strip()
            
            # 提取中文文本
            chinese_texts = re.findall(self.chinese_pattern, clean_content)
            
            if chinese_texts:  # 只保存包含中文的标签
                tag_info = {
                    "index": tag_index,
                    "tag_name": tag_name,
                    "original_content": tag_content[:200] + "..." if len(tag_content) > 200 else tag_content,
                    "clean_content": clean_content,
                    "chinese_texts": chinese_texts,
                    "chinese_count": len(chinese_texts)
                }
                
                result["all_tags"].append(tag_info)
                result["chinese_texts"].extend(chinese_texts)
                result["tag_chinese_map"][f"{tag_name}_{tag_index}"] = chinese_texts
        
        # 2. 额外提取所有文本节点中的中文（不在标签内的）
        text_only = re.sub(r'<[^>]+>', ' ', html_body)
        text_only = re.sub(r'\s+', ' ', text_only).strip()
        all_chinese_in_text = re.findall(self.chinese_pattern, text_only)
        
        # 3. 统计信息
        result["statistics"] = {
            "total_tags_with_chinese": len(result["all_tags"]),
            "total_chinese_segments": len(result["chinese_texts"]),
            "total_chinese_in_page": len(all_chinese_in_text),
            "unique_chinese_texts": len(set(result["chinese_texts"])),
            "tag_types": list(set([tag["tag_name"] for tag in result["all_tags"]]))
        }
        
        return result
    
    def get_unique_chinese_texts(self, chinese_texts: List[str]) -> List[str]:
        """
        获取去重后的中文文本列表
        
        Args:
            chinese_texts: 中文文本列表
            
        Returns:
            去重后的中文文本列表
        """
        return list(set(chinese_texts))


# 创建全局实例
html_parser_service = HtmlParserService()
