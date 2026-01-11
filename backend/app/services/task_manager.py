# -*- coding: utf-8 -*-
"""
任务管理器 - 管理异步任务的状态和结果
"""
import asyncio
import shutil
import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path
import uuid

from ..schemas import TaskStatus, TaskType
from ..config import Config

# 配置日志
logger = logging.getLogger(__name__)

# 声明配置实例
config = Config()


class TaskInfo:
    """任务信息类

    Args:
        task_id (str): 任务ID
        task_dir (Path): 任务专属文件夹路径
        task_type (TaskType): 任务类型（饰品试戴或服装穿戴）

    Attributes:
        status (TaskStatus): 任务状态
        message (str): 任务状态描述
        progress (int): 任务进度百分比
        result (Optional[Dict[str, Any]]): 任务结果
        error_message (Optional[str]): 任务错误信息
        created_at (datetime): 任务创建时间
        updated_at (datetime): 任务最后更新时间
        person_image_path (Optional[str]): 人物图片路径
        person_position (Optional[str]): 识别出的穿戴位置
        accessory_image_path (Optional[str]): 饰品图片路径（饰品任务）
        accessory_detail_image_path (Optional[str]): 饰品细节图路径（饰品任务）
        accessory_type (Optional[str]): 识别出的饰品类型（饰品任务）
        clothing_image_path (Optional[str]): 服装图片路径（服装任务）
        clothing_type (Optional[str]): 识别出的服装类型（服装任务）
    """

    def __init__(self, task_id: str, task_dir: Path, task_type: TaskType):
        # 基础信息
        self.task_id: str = task_id
        self.task_dir: Path = task_dir
        self.task_type: TaskType = task_type

        # 任务状态信息
        self.status: TaskStatus = TaskStatus.PENDING
        self.message: str = "任务已创建，等待处理"
        self.progress: int = 0
        self.result: Optional[Dict[str, Any]] = None
        self.error_message: Optional[str] = None
        self.created_at: datetime = datetime.now()
        self.updated_at: datetime = datetime.now()

        # 公共图片路径
        self.person_image_path: Optional[str] = None
        self.person_position: Optional[str] = None

        # 饰品专属字段
        self.accessory_image_path: Optional[str] = None
        self.accessory_detail_image_path: Optional[str] = None
        self.accessory_type: Optional[str] = None

        # 服装专属字段
        self.clothing_image_path: Optional[str] = None
        self.clothing_type: Optional[str] = None

    def update_status(self,
                      status: TaskStatus,
                      message: str = None,
                      progress: int = None):
        """更新任务状态

        Args:
            status (TaskStatus): 任务状态
            message (str, optional): 任务状态描述, 默认值为 None
            progress (int, optional): 任务进度百分比, 默认值为 None
        """
        self.status = status
        if message:
            self.message = message
        if progress is not None:
            self.progress = progress
        self.updated_at = datetime.now()

    def set_result(self, result: Dict[str, Any]):
        """设置任务结果

        Args:
            result (Dict[str, Any]): 任务结果
        """
        self.result = result
        self.status = TaskStatus.COMPLETED
        self.progress = 100
        self.message = "任务完成"
        self.updated_at = datetime.now()

    def set_error(self, error_message: str):
        """设置任务错误

        Args:
            error_message (str): 错误信息
        """
        self.error_message = error_message
        self.status = TaskStatus.FAILED
        self.message = f"任务失败: {error_message}"
        self.updated_at = datetime.now()


class TaskManager:
    """
    任务管理器
    使用内存字典存储任务状态，适合单机部署
    后续可扩展为Redis存储以支持分布式部署

    Attributes:
        _tasks (Dict[str, TaskInfo]): 任务字典，键为任务ID，值为任务信息对象
        _lock (asyncio.Lock): 异步锁，用于保护任务字典的并发访问

    """

    def __init__(self):
        self._tasks: Dict[str, TaskInfo] = {}
        self._lock = asyncio.Lock()  # 异步锁，保护任务字典的并发访问

    async def create_task(self, task_type: TaskType) -> Tuple[TaskInfo, Optional[str]]:
        """创建新任务，同时创建任务专属文件夹

        Fetures:
            - 如果任务数量超过上限，会自动删除最早的任务

        Args:
            task_type (TaskType): 任务类型（饰品试戴或服装穿戴）

        Returns:
            Tuple[TaskInfo, Optional[str]]: 新创建的任务信息对象，以及被删除的旧任务ID（如果有）
        """
        async with self._lock:
            deleted_task_id = None

            # 检查任务数量是否超过上限
            if len(self._tasks) >= config.MAX_TASKS:
                # 找到最早创建的任务
                oldest_task = min(self._tasks.values(),
                                  key=lambda t: t.created_at)
                deleted_task_id = oldest_task.task_id
                logger.warning(
                    f"任务数量已达上限({config.MAX_TASKS})，自动删除最早的任务: {deleted_task_id}"
                )
                self._delete_task_internal(deleted_task_id)

            task_id = str(uuid.uuid4())
            # 创建任务专属文件夹
            task_dir = config.TASKS_DIR / task_id
            task_dir.mkdir(parents=True, exist_ok=True)
            task_info = TaskInfo(task_id, task_dir, task_type)
            self._tasks[task_id] = task_info
            return task_info, deleted_task_id

    async def get_task(self, task_id: str) -> Optional[TaskInfo]:
        """获取任务信息

        Args:
            task_id (str): 任务ID
        Returns:
            Optional[TaskInfo]: 任务信息对象，如果不存在则返回 None
        """
        async with self._lock:
            return self._tasks.get(task_id)

    async def reset_task(self, task_id: str) -> Optional[TaskInfo]:
        """重置任务状态，用于失败任务的重新提交

        将任务状态重置为PENDING，清除错误信息和结果，但保留任务文件夹

        Args:
            task_id (str): 任务ID
        Returns:
            Optional[TaskInfo]: 重置后的任务信息对象，如果任务不存在则返回 None
        """
        async with self._lock:
            task_info = self._tasks.get(task_id)
            if not task_info:
                return None

            # 重置任务状态
            task_info.status = TaskStatus.PENDING
            task_info.message = "任务已重置，等待处理"
            task_info.progress = 0
            task_info.result = None
            task_info.error_message = None
            task_info.updated_at = datetime.now()
            # 清除之前的识别结果（公共字段）
            task_info.person_position = None
            # 清除饰品相关识别结果
            task_info.accessory_type = None
            # 清除服装相关识别结果
            task_info.clothing_type = None

            return task_info

    async def create_task_with_id(self, task_id: str, task_type: TaskType) -> TaskInfo:
        """使用指定的task_id创建任务（用于后端重启后恢复任务）

        Args:
            task_id (str): 指定的任务ID
            task_type (TaskType): 任务类型（饰品试戴或服装穿戴）
        Returns:
            TaskInfo: 新创建的任务信息对象
        """
        async with self._lock:
            # 创建任务专属文件夹
            task_dir = config.TASKS_DIR / task_id
            task_dir.mkdir(parents=True, exist_ok=True)
            task_info = TaskInfo(task_id, task_dir, task_type)
            self._tasks[task_id] = task_info
            return task_info

    def _delete_task_internal(self, task_id: str) -> bool:
        """内部删除方法（不加锁，供已持有锁的方法调用）
        
        Args:
            task_id (str): 任务ID
        Returns:
            bool: 如果任务存在并成功删除返回 True，否则返回 False
        """
        deleted = False
        if task_id in self._tasks:
            task_info = self._tasks[task_id]
            if task_info.task_dir and task_info.task_dir.exists():
                shutil.rmtree(task_info.task_dir, ignore_errors=True)
            del self._tasks[task_id]
            deleted = True
        else:
            task_dir = config.TASKS_DIR / task_id
            if task_dir.exists():
                shutil.rmtree(task_dir, ignore_errors=True)
                deleted = True
        return deleted

    async def delete_task(self, task_id: str) -> bool:
        """删除任务及其文件夹

        Args:
            task_id (str): 任务ID
        Returns:
            bool: 如果任务存在并成功删除返回 True，否则返回 False
        """
        async with self._lock:
            return self._delete_task_internal(task_id)

    async def cleanup_old_tasks(self, max_age_hours: int = None):
        """清理过期任务及其文件夹

        Args:
            max_age_hours (int, optional): 任务最大存活时间（小时），默认值为配置中的 TASK_MAX_AGE_HOURS
        Returns:
            int: 被清理的任务数量
        """
        if max_age_hours is None:
            max_age_hours = config.TASK_MAX_AGE_HOURS
        async with self._lock:
            now = datetime.now()
            expired_tasks = [
                task_id for task_id, task_info in self._tasks.items()
                if (now -
                    task_info.created_at).total_seconds() > max_age_hours *
                3600
            ]
            for task_id in expired_tasks:
                self._delete_task_internal(task_id)
            return len(expired_tasks)


# 全局任务管理器实例
task_manager = TaskManager()
