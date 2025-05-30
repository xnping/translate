"""
数据库模型定义 - 根据实际SQL表结构
"""

from typing import Optional
from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.config.config import Base


class Label(Base):
    """标签表"""
    __tablename__ = "label"

    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # 标签信息
    label: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, comment="标签名称")
    type: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="类型ID")


class Type(Base):
    """类型表"""
    __tablename__ = "type"

    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # 类型信息
    type: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, comment="类型名称")
    class_: Mapped[Optional[str]] = mapped_column("class", String(255), nullable=True, comment="类别")
