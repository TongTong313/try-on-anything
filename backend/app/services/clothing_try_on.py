# -*- coding: utf-8 -*-
"""
服装试穿服务 - 核心业务逻辑
"""
from typing import Optional

from try_on_anything.pipelines import ClothingTryOnPipeline
from try_on_anything.generators.clothing_try_on import ClothingTryOnImageGenerator
from .base import BaseTryOnService
from .task_manager import TaskInfo


class ClothingTryOnService(BaseTryOnService):
    """服装试穿服务类"""

    def get_pipeline_class(self):
        """返回服装试穿Pipeline类"""
        return ClothingTryOnPipeline

    def get_generator_class(self):
        """返回服装试穿Generator类"""
        return ClothingTryOnImageGenerator

    def start_task(
        self,
        task_info: TaskInfo,
        clothing_image_path: str,
        person_image_path: str,
        clothing_type: Optional[str] = None,
        person_position: Optional[str] = None,
        use_vl_model: bool = True,
        vl_model_api_key: Optional[str] = None,
        img_gen_model_api_key: Optional[str] = None,
        vl_model: str = "qwen3-vl-plus",
        img_gen_model: str = "wan2.6-image"
    ):
        """启动服装试穿任务

        Args:
            task_info: 任务信息对象
            clothing_image_path: 服装图片路径
            person_image_path: 人物图片路径
            clothing_type: 服装类型（可选）
            person_position: 穿着位置（可选）
            use_vl_model: 是否使用VL模型
            vl_model_api_key: VL模型API Key
            img_gen_model_api_key: 图像生成模型API Key
            vl_model: VL模型名称
            img_gen_model: 图像生成模型名称
        """
        # 准备图片路径字典
        image_paths = {
            "clothing_img_path": clothing_image_path,
            "person_img_path": person_image_path
        }

        # 准备任务参数字典
        task_params = {
            "clothing_type": clothing_type,
            "person_position": person_position
        }

        # 保存路径到任务信息
        task_info.clothing_image_path = clothing_image_path
        task_info.person_image_path = person_image_path

        # 调用基类的start_task方法
        super().start_task(
            task_info=task_info,
            image_paths=image_paths,
            task_params=task_params,
            use_vl_model=use_vl_model,
            vl_model_api_key=vl_model_api_key,
            img_gen_model_api_key=img_gen_model_api_key,
            vl_model=vl_model,
            img_gen_model=img_gen_model
        )


# 全局服务实例
clothing_try_on_service = ClothingTryOnService()
