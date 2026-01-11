# -*- coding: utf-8 -*-
"""
Service层基类，提供通用的业务逻辑
"""
import asyncio
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod

from try_on_anything.clients import QwenVLClient, WanModelClient
from .task_manager import TaskInfo
from ..schemas import TaskStatus


class BaseTryOnService(ABC):
    """试穿/试戴服务基类

    使用模板方法模式，子类只需实现差异部分：
    - get_pipeline_class(): 返回Pipeline类
    - get_generator_class(): 返回Generator类
    """

    def __init__(self):
        self._pipeline = None

    @abstractmethod
    def get_pipeline_class(self):
        """获取Pipeline类（子类必须实现）"""
        pass

    @abstractmethod
    def get_generator_class(self):
        """获取Generator类（子类必须实现）"""
        pass

    def _get_pipeline(
        self,
        use_vl_model: bool = True,
        download_root_path: str = None,
        vl_model_api_key: Optional[str] = None,
        img_gen_model_api_key: Optional[str] = None
    ):
        """获取Pipeline实例（通用实现）

        Args:
            use_vl_model: 是否使用VL模型
            download_root_path: 下载路径
            vl_model_api_key: VL模型API Key
            img_gen_model_api_key: 图像生成模型API Key

        Returns:
            Pipeline实例
        """
        # 1. 创建 WanModelClient
        wan_client = WanModelClient(api_key=img_gen_model_api_key)

        # 2. 创建 Generator
        generator_class = self.get_generator_class()
        img_generator = generator_class(
            wan_client=wan_client,
            download_root_path=download_root_path
        )

        # 3. 创建 QwenVLClient（仅在启用VL模型时需要）
        vl_client = None
        if use_vl_model:
            vl_client = QwenVLClient(api_key=vl_model_api_key)

        # 4. 创建 Pipeline
        pipeline_class = self.get_pipeline_class()
        return pipeline_class(
            img_generator=img_generator,
            vl_client=vl_client,
            use_vl_model=use_vl_model
        )

    async def process_task(
        self,
        task_info: TaskInfo,
        image_paths: Dict[str, str],
        task_params: Dict[str, Any],
        use_vl_model: bool = True,
        vl_model_api_key: Optional[str] = None,
        img_gen_model_api_key: Optional[str] = None,
        vl_model: str = "qwen3-vl-plus",
        img_gen_model: str = "wan2.6-image"
    ):
        """处理任务（通用实现）

        Args:
            task_info: 任务信息对象
            image_paths: 图片路径字典
            task_params: 任务参数字典（传递给Pipeline的参数）
            use_vl_model: 是否使用VL模型
            vl_model_api_key: VL模型API Key
            img_gen_model_api_key: 图像生成模型API Key
            vl_model: VL模型名称
            img_gen_model: 图像生成模型名称
        """
        # 定义状态回调函数
        async def status_callback(status: str, progress: int):
            """Pipeline状态回调函数"""
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

            # 获取Pipeline实例
            pipeline = self._get_pipeline(
                use_vl_model=use_vl_model,
                download_root_path=str(task_info.task_dir),
                vl_model_api_key=vl_model_api_key,
                img_gen_model_api_key=img_gen_model_api_key
            )

            # 调用Pipeline执行任务
            result = await pipeline.run(
                **image_paths,
                **task_params,
                vl_model_name=vl_model,
                img_gen_model_name=img_gen_model,
                status_callback=status_callback
            )

            # 处理结果
            self._handle_result(task_info, result)

        except FileNotFoundError as e:
            # 文件不存在错误
            error_msg = f"文件不存在: {str(e)}"
            logging.error(error_msg)
            task_info.set_error(error_msg)

        except ValueError as e:
            # 参数验证错误
            error_msg = f"参数错误: {str(e)}"
            logging.error(error_msg)
            task_info.set_error(error_msg)

        except ConnectionError as e:
            # 网络连接错误
            error_msg = f"网络连接失败: {str(e)}"
            logging.error(error_msg)
            task_info.set_error(error_msg)

        except TimeoutError as e:
            # 超时错误
            error_msg = f"请求超时: {str(e)}"
            logging.error(error_msg)
            task_info.set_error(error_msg)

        except Exception as e:
            # 未知错误
            error_msg = f"系统错误: {str(e)}"
            logging.exception(f"任务处理失败: {e}")  # 记录完整堆栈
            task_info.set_error(error_msg)

    def _handle_result(self, task_info: TaskInfo, result: Dict[str, Any]):
        """处理Pipeline返回的结果（通用实现）"""
        task_status = result.get("output", {}).get("task_status")

        if task_status == "SUCCEEDED":
            # 提取下载的图片路径
            downloaded_images = []
            choices = result.get("output", {}).get("choices", [])
            for choice in choices:
                try:
                    content = choice.get("message", {}).get("content", [])
                    if content:
                        image_url = content[0].get("image", "")
                        if image_url:
                            filename = Path(image_url.split('?')[0]).name
                            local_path = str(task_info.task_dir / filename)
                            downloaded_images.append(local_path)
                except (IndexError, KeyError):
                    continue

            result["downloaded_images"] = downloaded_images

            # 提取结果信息（子类可以重写此方法来提取特定字段）
            self._extract_result_info(task_info, result)
            task_info.set_result(result)
        else:
            # 任务失败
            error_msg = result.get("output", {}).get("message", "未知错误")
            task_info.set_error(error_msg)

    def _extract_result_info(self, task_info: TaskInfo, result: Dict[str, Any]):
        """从结果中提取信息（子类可重写）"""
        # 默认实现：尝试提取常见字段
        for key in ["accessory_type", "clothing_type", "person_position"]:
            if key in result:
                setattr(task_info, key, result[key])

    def start_task(
        self,
        task_info: TaskInfo,
        image_paths: Dict[str, str],
        task_params: Dict[str, Any],
        use_vl_model: bool = True,
        vl_model_api_key: Optional[str] = None,
        img_gen_model_api_key: Optional[str] = None,
        vl_model: str = "qwen3-vl-plus",
        img_gen_model: str = "wan2.6-image"
    ):
        """启动异步任务（通用实现）"""
        # 保存文件路径到任务信息
        for key, path in image_paths.items():
            setattr(task_info, f"{key}_path", path)

        # 创建异步任务
        asyncio.create_task(
            self.process_task(
                task_info=task_info,
                image_paths=image_paths,
                task_params=task_params,
                use_vl_model=use_vl_model,
                vl_model_api_key=vl_model_api_key,
                img_gen_model_api_key=img_gen_model_api_key,
                vl_model=vl_model,
                img_gen_model=img_gen_model
            )
        )
