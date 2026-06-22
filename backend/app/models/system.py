"""系统配置与管理员 ORM，映射旧表 config / manager。"""
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Config(Base):
    __tablename__ = "config"

    config_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ab_test: Mapped[int | None] = mapped_column(Integer)


class Manager(Base):
    __tablename__ = "manager"

    manager_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    manager_name: Mapped[str] = mapped_column(String(64))
    manager_password: Mapped[str] = mapped_column(String(64))
    manager_salt: Mapped[str | None] = mapped_column(String(64))
