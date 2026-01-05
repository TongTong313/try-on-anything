# -*- coding: utf-8 -*-
"""
服务层包
"""
from .task_manager import TaskManager, TaskInfo, task_manager
from .tryon import TryOnService, tryon_service

__all__ = [
    "TaskManager",
    "TaskInfo",
    "task_manager",
    "TryOnService",
    "tryon_service",
]
