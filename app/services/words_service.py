"""
敏感词数据库操作服务 - 基于MySQL
"""

from typing import List, Optional, Tuple
from app.models.words_models import WordCreate, WordUpdate, WordResponse
from app.services.mysql_service import mysql_service
import re


class WordsService:
    """敏感词服务类"""
    
    def __init__(self):
        """初始化敏感词服务"""
        self.mysql = mysql_service
    
    async def create_word(self, word_data: WordCreate) -> Optional[WordResponse]:
        """创建敏感词"""
        try:
            print(f"🔍 开始创建敏感词: {word_data.words}")

            # 检查是否已存在
            existing = await self.get_word_by_content(word_data.words)
            if existing:
                print(f"⚠️ 敏感词已存在: {existing}")
                raise ValueError(f"敏感词 '{word_data.words}' 已存在")

            print(f"✅ 敏感词不存在，开始插入")

            # 在同一个连接中完成插入和查询
            if not self.mysql.pool:
                await self.mysql.create_pool()

            async with self.mysql.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    # 插入新敏感词
                    insert_query = "INSERT INTO words (words) VALUES (%s)"
                    print(f"🔍 执行插入SQL: {insert_query}, 参数: {(word_data.words,)}")
                    await cursor.execute(insert_query, (word_data.words,))
                    word_id = cursor.lastrowid
                    print(f"✅ 插入成功，获得ID: {word_id}")

                    # 立即在同一连接中查询
                    select_query = "SELECT id, words FROM words WHERE id = %s"
                    print(f"🔍 在同一连接中查询: {select_query}, 参数: {(word_id,)}")
                    await cursor.execute(select_query, (word_id,))
                    result = await cursor.fetchone()
                    print(f"✅ 查询结果: {result}")

                    if result:
                        return WordResponse(
                            id=result[0],
                            words=result[1]
                        )
                    else:
                        print(f"❌ 查询失败，result为: {result}")
                        return None

        except ValueError as e:
            print(f"⚠️ 创建敏感词验证失败: {e}")
            raise e
        except Exception as e:
            print(f"❌ 创建敏感词失败: {e}")
            import traceback
            traceback.print_exc()
            raise Exception(f"数据库操作失败: {str(e)}")
    
    async def get_word_by_id(self, word_id: int) -> Optional[WordResponse]:
        """根据ID获取敏感词"""
        try:
            query = "SELECT id, words FROM words WHERE id = %s"
            print(f"🔍 查询敏感词: {query}, 参数: {(word_id,)}")
            result = await self.mysql.execute_query(query, (word_id,))
            print(f"🔍 查询结果: {result}")

            if result and len(result) > 0:
                word = result[0]
                print(f"✅ 找到敏感词: {word}")
                return WordResponse(
                    id=word["id"],
                    words=word["words"]
                )
            else:
                print(f"❌ 未找到敏感词，result: {result}")

            return None

        except Exception as e:
            print(f"❌ 获取敏感词失败: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    async def get_word_by_content(self, word_content: str) -> Optional[WordResponse]:
        """根据内容获取敏感词"""
        try:
            query = "SELECT id, words FROM words WHERE words = %s"
            result = await self.mysql.execute_query(query, (word_content,))
            
            if result:
                word = result[0]
                return WordResponse(
                    id=word["id"],
                    words=word["words"]
                )
            
            return None
            
        except Exception as e:
            print(f"❌ 获取敏感词失败: {e}")
            return None
    
    async def get_words_list(self, page: int = 1, page_size: int = 10, keyword: str = None) -> Tuple[List[WordResponse], int]:
        """获取敏感词列表"""
        try:
            offset = (page - 1) * page_size
            
            # 构建查询条件
            where_clause = ""
            params = []
            
            if keyword:
                where_clause = "WHERE words LIKE %s"
                params.append(f"%{keyword}%")
            
            # 获取总数
            count_query = f"SELECT COUNT(*) as total FROM words {where_clause}"
            count_result = await self.mysql.execute_query(count_query, params)
            total = count_result[0]["total"] if count_result else 0
            
            # 获取分页数据
            query = f"SELECT id, words FROM words {where_clause} ORDER BY id DESC LIMIT %s OFFSET %s"
            params.extend([page_size, offset])
            
            results = await self.mysql.execute_query(query, params)
            
            words_list = [
                WordResponse(
                    id=row["id"],
                    words=row["words"]
                )
                for row in results
            ]
            
            return words_list, total
            
        except Exception as e:
            print(f"❌ 获取敏感词列表失败: {e}")
            return [], 0
    
    async def update_word(self, word_id: int, word_data: WordUpdate) -> Optional[WordResponse]:
        """更新敏感词"""
        try:
            # 检查敏感词是否存在
            existing = await self.get_word_by_id(word_id)
            if not existing:
                raise ValueError(f"敏感词ID {word_id} 不存在")
            
            # 如果要更新内容，检查新内容是否已存在
            if word_data.words:
                existing_content = await self.get_word_by_content(word_data.words)
                if existing_content and existing_content.id != word_id:
                    raise ValueError(f"敏感词 '{word_data.words}' 已存在")
            
            # 构建更新语句
            update_fields = []
            params = []
            
            if word_data.words is not None:
                update_fields.append("words = %s")
                params.append(word_data.words)
            
            if not update_fields:
                return existing
            
            params.append(word_id)
            query = f"UPDATE words SET {', '.join(update_fields)} WHERE id = %s"
            
            affected_rows = await self.mysql.execute_update(query, params)
            
            if affected_rows > 0:
                return await self.get_word_by_id(word_id)
            
            return existing
            
        except Exception as e:
            print(f"❌ 更新敏感词失败: {e}")
            raise e
    
    async def delete_word(self, word_id: int) -> bool:
        """删除敏感词"""
        try:
            # 检查敏感词是否存在
            existing = await self.get_word_by_id(word_id)
            if not existing:
                raise ValueError(f"敏感词ID {word_id} 不存在")
            
            query = "DELETE FROM words WHERE id = %s"
            affected_rows = await self.mysql.execute_delete(query, (word_id,))
            
            return affected_rows > 0
            
        except Exception as e:
            print(f"❌ 删除敏感词失败: {e}")
            raise e
    
    async def batch_create_words(self, words_list: List[str]) -> dict:
        """批量创建敏感词"""
        try:
            success_count = 0
            failed_count = 0
            failed_words = []
            
            for word_content in words_list:
                try:
                    word_data = WordCreate(words=word_content.strip())
                    result = await self.create_word(word_data)
                    if result:
                        success_count += 1
                    else:
                        failed_count += 1
                        failed_words.append(word_content)
                except Exception as e:
                    failed_count += 1
                    failed_words.append(f"{word_content} (错误: {str(e)})")
            
            return {
                "total": len(words_list),
                "success_count": success_count,
                "failed_count": failed_count,
                "failed_words": failed_words
            }
            
        except Exception as e:
            print(f"❌ 批量创建敏感词失败: {e}")
            raise e
    
    async def batch_delete_words(self, word_ids: List[int]) -> dict:
        """批量删除敏感词"""
        try:
            success_count = 0
            failed_count = 0
            failed_ids = []
            
            for word_id in word_ids:
                try:
                    result = await self.delete_word(word_id)
                    if result:
                        success_count += 1
                    else:
                        failed_count += 1
                        failed_ids.append(word_id)
                except Exception as e:
                    failed_count += 1
                    failed_ids.append(f"{word_id} (错误: {str(e)})")
            
            return {
                "total": len(word_ids),
                "success_count": success_count,
                "failed_count": failed_count,
                "failed_ids": failed_ids
            }
            
        except Exception as e:
            print(f"❌ 批量删除敏感词失败: {e}")
            raise e
    
    async def check_sensitive_words(self, text: str) -> dict:
        """检测文本中的敏感词"""
        try:
            # 获取所有敏感词
            all_words, _ = await self.get_words_list(page=1, page_size=10000)
            
            found_words = []
            clean_text = text
            
            for word_obj in all_words:
                word = word_obj.words
                if word in text:
                    found_words.append({
                        "word": word,
                        "positions": [m.start() for m in re.finditer(re.escape(word), text)]
                    })
                    # 替换敏感词
                    clean_text = clean_text.replace(word, "*" * len(word))
            
            return {
                "original_text": text,
                "clean_text": clean_text,
                "has_sensitive_words": len(found_words) > 0,
                "sensitive_words_count": len(found_words),
                "found_words": found_words
            }
            
        except Exception as e:
            print(f"❌ 检测敏感词失败: {e}")
            raise e


# 创建全局实例
words_service = WordsService()
