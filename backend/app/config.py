# -*- coding: utf-8 -*-
"""
应用配置管理
"""
import os
from pydantic import BaseModel, model_validator
from typing import List, Set
from pathlib import Path


# 后端目录（模块级常量，供类属性默认值使用）
_BASE_DIR = Path(__file__).resolve().parent.parent


class Config(BaseModel):
    """应用配置类

    使用 Pydantic BaseModel 进行类型强校验。
    在需要使用配置的文件中声明实例: config = Config()
    """

    # Pydantic v2 配置
    model_config = {"arbitrary_types_allowed": True}

    # 后端目录
    BASE_DIR: Path = _BASE_DIR
    # 任务数据存储目录（每个任务一个文件夹）
    TASKS_DIR: Path = _BASE_DIR / "tasks"
    # 允许的图片格式
    ALLOWED_EXTENSIONS: Set[str] = {".jpg", ".jpeg", ".png", ".webp"}
    # 最大文件大小 (30MB)
    MAX_FILE_SIZE: int = 30 * 1024 * 1024
    # API前缀
    API_PREFIX: str = "/api"
    # 任务超时时间（秒）
    TASK_TIMEOUT: int = 300
    # 任务过期时间（小时）
    TASK_MAX_AGE_HOURS: int = 24
    # 任务数量上限（超过此数量会自动删除最早的任务）
    MAX_TASKS: int = 20

    @property
    def CORS_ORIGINS(self) -> List[str]:
        """获取CORS允许的源列表，支持通过环境变量配置

        Returns:
            List[str]: 允许的CORS源列表
        """
        env_origins = os.getenv("CORS_ORIGINS")
        if env_origins:
            return [origin.strip() for origin in env_origins.split(",")]
        # 默认值：本地开发环境
        return ["http://localhost:5173", "http://127.0.0.1:5173"]

    @model_validator(mode="after")
    def _ensure_dirs_exist(self) -> "Config":
        """确保必要目录存在"""
        self.TASKS_DIR.mkdir(parents=True, exist_ok=True)
        return self
