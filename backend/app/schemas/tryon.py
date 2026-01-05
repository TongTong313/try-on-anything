# -*- coding: utf-8 -*-
"""
Pydantic数据模型 - 请求和响应的数据结构定义
"""
from typing import Optional
from enum import Enum
from pydantic import BaseModel


class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"          # 等待处理
    PROCESSING = "processing"    # 处理中
    COMPLETED = "completed"      # 已完成
    FAILED = "failed"            # 失败


class TryOnSubmitResponse(BaseModel):
    """试戴任务提交响应"""
    task_id: str                # 任务ID
    message: str                # 提示信息
    deleted_task_id: Optional[str] = None  # 因超出上限被删除的旧任务ID


class TaskStatusResponse(BaseModel):
    """任务状态查询响应"""
    task_id: str                # 任务ID
    status: TaskStatus          # 任务状态
    message: Optional[str] = None   # 状态描述
    progress: Optional[int] = None  # 进度百分比 (0-100)


class TryOnResultResponse(BaseModel):
    """试戴结果响应"""
    task_id: str                        # 任务ID
    status: TaskStatus                  # 任务状态
    result_image_url: Optional[str] = None      # 结果图片URL
    accessory_image_url: Optional[str] = None     # 原饰品图片URL
    person_image_url: Optional[str] = None      # 原人物图片URL
    accessory_type: Optional[str] = None          # 识别的饰品类型
    person_position: Optional[str] = None       # 识别的佩戴位置
    error_message: Optional[str] = None         # 错误信息（如果失败）


class TaskDeleteResponse(BaseModel):
    """任务删除响应"""
    task_id: str                # 被删除的任务ID
    success: bool               # 是否删除成功
    message: str                # 提示信息
