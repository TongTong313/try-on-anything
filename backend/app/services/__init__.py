# -*- coding: utf-8 -*-
"""
服务层包
"""
from .task_manager import TaskManager, TaskInfo, task_manager
from .accessory_try_on import AccessoryTryOnService, accessory_try_on_service
from .clothing_try_on import ClothingTryOnService, clothing_try_on_service

__all__ = [
    "TaskManager",
    "TaskInfo",
    "task_manager",
    "AccessoryTryOnService",
    "accessory_try_on_service",
    "ClothingTryOnService",
    "clothing_try_on_service",
]
