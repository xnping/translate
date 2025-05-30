"""
数据库模型定义
"""

from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Word(Base):
    """敏感词表模型"""
    __tablename__ = "words"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True, comment="主键ID")
    words = Column(String(255), nullable=False, index=True, comment="敏感词内容")
    
    def __repr__(self):
        return f"<Word(id={self.id}, words='{self.words}')>"
