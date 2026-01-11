# -*- coding: utf-8 -*-
"""
API层基类，提供通用的端点实现
"""
import logging
import aiofiles
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, UploadFile, HTTPException

from ..config import Config
from ..schemas import (
    TaskStatus,
    TaskType,
    TryOnSubmitResponse,
    TaskStatusResponse,
    TryOnResultResponse,
    TaskDeleteResponse,
)
from ..services import task_manager
from .utils import validate_file, validate_file_size, generate_filename, find_existing_images

config = Config()


class BaseTryOnRouter:
    """试穿/试戴API基类

    子类需要实现:
    - task_type: 任务类型
    - service: 服务实例
    """

    def __init__(self, prefix: str, tags: list):
        """初始化路由器

        Args:
            prefix: API路径前缀
            tags: API标签列表
        """
        self.router = APIRouter(prefix=prefix, tags=tags)
        self._register_routes()

    @property
    def task_type(self) -> TaskType:
        """任务类型，子类必须实现"""
        raise NotImplementedError

    @property
    def service(self):
        """服务实例，子类必须实现"""
        raise NotImplementedError

    def _register_routes(self):
        """注册所有路由端点"""
        self.router.add_api_route(
            "/status/{task_id}",
            self.get_task_status,
            methods=["GET"],
            response_model=TaskStatusResponse
        )
        self.router.add_api_route(
            "/result/{task_id}",
            self.get_task_result,
            methods=["GET"],
            response_model=TryOnResultResponse
        )
        self.router.add_api_route(
            "/task/{task_id}",
            self.delete_task,
            methods=["DELETE"],
            response_model=TaskDeleteResponse
        )

    async def get_task_status(self, task_id: str):
        """查询任务状态"""
        task_info = await task_manager.get_task(task_id)
        if not task_info:
            raise HTTPException(status_code=404, detail="任务不存在")

        return TaskStatusResponse(
            task_id=task_info.task_id,
            task_type=task_info.task_type,
            status=task_info.status,
            message=task_info.message,
            progress=task_info.progress,
        )

    async def delete_task(self, task_id: str):
        """删除任务"""
        success = await task_manager.delete_task(task_id)
        if success:
            return TaskDeleteResponse(
                task_id=task_id,
                success=True,
                message="任务已删除"
            )
        else:
            raise HTTPException(status_code=404, detail="任务不存在")

    async def get_task_result(self, task_id: str):
        """获取任务结果（通用实现）"""
        task_info = await task_manager.get_task(task_id)
        if not task_info:
            logging.error(f"任务 {task_id} 不存在，无法获取结果")
            raise HTTPException(status_code=404, detail="任务不存在")

        # 构建响应（使用任务类型动态获取字段）
        response_data = {
            "task_id": task_info.task_id,
            "task_type": task_info.task_type,
            "status": task_info.status,
        }

        # 根据任务类型添加特定字段
        if task_info.task_type == TaskType.ACCESSORY:
            response_data["accessory_type"] = task_info.accessory_type
            response_data["person_position"] = task_info.person_position
        elif task_info.task_type == TaskType.CLOTHING:
            response_data["clothing_type"] = task_info.clothing_type
            response_data["person_position"] = task_info.person_position

        response = TryOnResultResponse(**response_data)

        # 添加原图URL
        image_paths = self._get_image_paths_from_task(task_info)
        for key, path in image_paths.items():
            if path:
                filename = Path(path).name
                url = f"/api/tasks/{task_id}/{filename}"
                setattr(response, f"{key}_url", url)

        # 如果任务完成，添加结果图URL
        if task_info.status == TaskStatus.COMPLETED and task_info.result:
            downloaded_images = task_info.result.get("downloaded_images", [])
            if downloaded_images:
                result_filename = Path(downloaded_images[0]).name
                response.result_image_url = f"/api/tasks/{task_id}/{result_filename}"

        # 如果任务失败，添加错误信息
        if task_info.status == TaskStatus.FAILED:
            response.error_message = task_info.error_message

        return response

    def _get_image_paths_from_task(self, task_info) -> dict:
        """从任务信息中获取图片路径"""
        paths = {}
        if task_info.task_type == TaskType.ACCESSORY:
            paths["accessory_image"] = task_info.accessory_image_path
            paths["person_image"] = task_info.person_image_path
        elif task_info.task_type == TaskType.CLOTHING:
            paths["clothing_image"] = task_info.clothing_image_path
            paths["person_image"] = task_info.person_image_path
        return paths

    async def _process_and_save_images(
        self,
        task_info,
        images: dict,
        existing_images: dict = None
    ) -> dict:
        """处理并保存图片文件

        Args:
            task_info: 任务信息对象
            images: 上传的图片字典 {key: UploadFile}
            existing_images: 已存在的图片字典 {key: Path}

        Returns:
            保存后的图片路径字典 {key: str}
        """
        result = {}
        existing_images = existing_images or {}

        for key, upload_file in images.items():
            if upload_file:
                # 验证并保存新上传的文件
                validate_file(upload_file)
                filename = generate_filename(upload_file.filename)
                file_path = task_info.task_dir / filename

                content = await upload_file.read()
                await validate_file_size(content, upload_file.filename)

                async with aiofiles.open(file_path, "wb") as f:
                    await f.write(content)

                result[key] = str(file_path)
            elif key in existing_images and existing_images[key]:
                # 使用已存在的文件
                result[key] = str(existing_images[key])
            else:
                # 既没有上传新文件，也没有已存在的文件
                result[key] = None

        return result
