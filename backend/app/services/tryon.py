# -*- coding: utf-8 -*-
"""
试戴服务 - 核心业务逻辑，调用算法Pipeline
"""
from try_on_anything.pipelines import AccessoryTryOnPipeline
from try_on_anything.clients import QwenVLClient, WanModelClient
from try_on_anything.generators.accessory_try_on import AccessoryTryOnImageGenerator
import asyncio
from pathlib import Path
from typing import Optional

from .task_manager import TaskInfo, task_manager
from ..schemas import TaskStatus


class TryOnService:
    """
    饰品试戴服务类：封装算法Pipeline的调用逻辑

    Attributes:
        _pipeline (Optional[AccessoryTryOnPipeline]): Pipeline实例缓存
    """

    def __init__(self):
        self._pipeline: Optional[AccessoryTryOnPipeline] = None

    def _get_pipeline(
        self,
        use_vl_model: bool = True,
        download_root_path: str = None,
        vl_model_api_key: Optional[str] = None,
        img_gen_model_api_key: Optional[str] = None
    ) -> AccessoryTryOnPipeline:
        """
        获取Pipeline实例

        Args:
            use_vl_model (bool, optional): 是否使用VL模型，默认值为 True
            download_root_path (str, optional): 下载路径，默认值为 None
            vl_model_api_key (str, optional): VL模型API Key，默认值为 None
            img_gen_model_api_key (str, optional): 图像生成模型API Key，默认值为 None

        Returns:
            AccessoryTryOnPipeline: Pipeline实例
        """
        # 1. 创建 WanModelClient
        wan_client = WanModelClient(api_key=img_gen_model_api_key)

        # 2. 创建 AccessoryTryOnImageGenerator
        img_generator = AccessoryTryOnImageGenerator(
            wan_client=wan_client,
            download_root_path=download_root_path
        )

        # 3. 创建 QwenVLClient（仅在启用VL模型时需要）
        vl_client = None
        if use_vl_model:
            vl_client = QwenVLClient(api_key=vl_model_api_key)

        # 4. 创建 AccessoryTryOnPipeline
        return AccessoryTryOnPipeline(
            img_generator=img_generator,
            vl_client=vl_client,
            use_vl_model=use_vl_model
        )

    async def process_tryon_task(
        self,
        task_info: TaskInfo,
        accessory_image_path: str,
        person_image_path: str,
        accessory_detail_image_path: Optional[str] = None,
        accessory_type: Optional[str] = None,
        person_position: Optional[str] = None,
        use_vl_model: bool = True,
        vl_model_api_key: Optional[str] = None,
        img_gen_model_api_key: Optional[str] = None,
        vl_model: str = "qwen3-vl-plus",
        img_gen_model: str = "wan2.6-image"
    ):
        """
        处理试穿任务（异步执行）

        Args:
            task_info (TaskInfo): 任务信息对象
            accessory_image_path (str): 饰品图片路径
            person_image_path (str): 人物图片路径
            accessory_detail_image_path (str, optional): 饰品细节图路径，默认值为 None
            accessory_type (str, optional): 饰品类型，默认值为 None
            person_position (str, optional): 佩戴位置，默认值为 None
            use_vl_model (bool, optional): 是否使用VL模型自动识别，默认值为 True
            vl_model_api_key (str, optional): VL模型API Key，默认值为 None
            img_gen_model_api_key (str, optional): 图像生成模型API Key，默认值为 None
            vl_model (str, optional): VL模型名称，默认值为 "qwen3-vl-plus"
            img_gen_model (str, optional): 图像生成模型名称，默认值为 "wan2.6-image"
        """
        # 定义状态回调函数，用于更新任务状态
        async def status_callback(status: str, progress: int):
            """
            Pipeline状态回调函数
            当Pipeline执行到不同阶段时，通过此回调更新任务状态

            Args:
                status (str): 当前状态描述
                progress (int): 当前进度百分比
            """
            task_info.update_status(
                TaskStatus.PROCESSING,
                status,
                progress
            )

        try:
            # 更新任务状态为处理中
            task_info.update_status(
                TaskStatus.PROCESSING,
                "准备中...",
                0
            )

            # 获取Pipeline实例，使用任务文件夹作为下载路径，传递API Key
            pipeline = self._get_pipeline(
                use_vl_model=use_vl_model,
                download_root_path=str(task_info.task_dir),
                vl_model_api_key=vl_model_api_key,
                img_gen_model_api_key=img_gen_model_api_key
            )

            # 调用Pipeline执行试穿，传入状态回调函数
            result = await pipeline.run(
                accessory_img_path=accessory_image_path,
                person_img_path=person_image_path,
                accessory_detail_img_path=accessory_detail_image_path,
                accessory_type=accessory_type,
                person_position=person_position,
                vl_model_name=vl_model,
                img_gen_model_name=img_gen_model,
                status_callback=status_callback
            )

            # 检查DashScope API返回的任务状态
            # Pipeline返回的是DashScope原始响应，状态字段在 output.task_status 中
            task_status = result.get("output", {}).get("task_status")
            if task_status == "SUCCEEDED":
                # 从结果中提取图片URL并构建本地路径
                # Pipeline已将图片下载到任务文件夹，这里根据URL提取文件名构建路径
                downloaded_images = []
                choices = result.get("output", {}).get("choices", [])
                for choice in choices:
                    try:
                        content = choice.get("message", {}).get("content", [])
                        if content:
                            image_url = content[0].get("image", "")
                            if image_url:
                                # 从URL提取文件名（与算法Pipeline下载逻辑一致）
                                filename = Path(image_url.split('?')[0]).name
                                local_path = str(task_info.task_dir / filename)
                                downloaded_images.append(local_path)
                    except (IndexError, KeyError):
                        continue

                # 将下载路径添加到结果中，供API层使用
                result["downloaded_images"] = downloaded_images

                # 提取结果信息
                task_info.accessory_type = result.get("accessory_type")
                task_info.person_position = result.get("person_position")
                task_info.set_result(result)
            else:
                # 任务失败，提取错误信息
                error_msg = result.get("output", {}).get("message", "未知错误")
                task_info.set_error(error_msg)

        except Exception as e:
            task_info.set_error(str(e))

    def start_task(
        self,
        task_info: TaskInfo,
        accessory_image_path: str,
        person_image_path: str,
        accessory_detail_image_path: Optional[str] = None,
        accessory_type: Optional[str] = None,
        person_position: Optional[str] = None,
        use_vl_model: bool = True,
        vl_model_api_key: Optional[str] = None,
        img_gen_model_api_key: Optional[str] = None,
        vl_model: str = "qwen3-vl-plus",
        img_gen_model: str = "wan2.6-image"
    ):
        """
        启动异步任务
        将任务添加到事件循环中执行

        Args:
            task_info (TaskInfo): 任务信息对象
            accessory_image_path (str): 饰品图片路径
            person_image_path (str): 人物图片路径
            accessory_detail_image_path (str, optional): 饰品细节图路径，默认值为 None
            accessory_type (str, optional): 饰品类型，默认值为 None
            person_position (str, optional): 佩戴位置，默认值为 None
            use_vl_model (bool, optional): 是否使用VL模型自动识别，默认值为 True
            vl_api_key (str, optional): VL模型API Key，默认值为 None
            image_api_key (str, optional): 图像生成模型API Key，默认值为 None
            vl_model (str, optional): VL模型名称，默认值为 "qwen3-vl-plus"
            img_gen_model (str, optional): 图像生成模型名称，默认值为 "wan2.6-image"
        """
        # 保存文件路径到任务信息
        task_info.accessory_image_path = accessory_image_path
        task_info.person_image_path = person_image_path
        task_info.accessory_detail_image_path = accessory_detail_image_path

        # 创建异步任务
        asyncio.create_task(
            self.process_tryon_task(
                task_info=task_info,
                accessory_image_path=accessory_image_path,
                person_image_path=person_image_path,
                accessory_detail_image_path=accessory_detail_image_path,
                accessory_type=accessory_type,
                person_position=person_position,
                use_vl_model=use_vl_model,
                vl_model_api_key=vl_model_api_key,
                img_gen_model_api_key=img_gen_model_api_key,
                vl_model=vl_model,
                img_gen_model=img_gen_model
            )
        )


# 全局服务实例
tryon_service = TryOnService()
