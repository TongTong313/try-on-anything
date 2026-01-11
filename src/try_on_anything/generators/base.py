from typing import List, Optional, Dict, Any, Tuple
import asyncio
import time
import base64
import logging
import httpx
import uuid
from PIL import Image
from ..clients import WanModelClient
from ..common.constants import (HTTP_DOWNLOAD_TIMEOUT, HTTP_REQUEST_TIMEOUT,
                                DEFAULT_POLL_INTERVAL, DEFAULT_MAX_WAIT_TIME,
                                SUPPORTED_OUTPUT_SIZES)
from pathlib import Path
from abc import ABC, abstractmethod


class DashScopeImageGenerator(ABC):
    """DashScope 图片生成 API 客户端
    
    Args:
        wan_client (WanModelClient): Wan 模型客户端实例
        download_root_path (str, optional): 下载生成的图片保存路径，默认为 None。如果保存路径为 None，则不下载生成的图片。
    """

    _BASE_PROMPT: str = ""
    _ADDITIONAL_REQUIREMENTS_PROMPT: str = ""

    def __init__(self,
                 wan_client: WanModelClient,
                 download_root_path: Optional[str] = None) -> None:
        self.wan_client = wan_client
        if download_root_path:
            download_dir = Path(download_root_path)
            if not download_dir.exists():
                logging.warning(f"下载生成图片保存路径不存在，创建路径: {download_root_path}")
                download_dir.mkdir(parents=True, exist_ok=True)
            self.download_root_path = download_dir
        else:
            self.download_root_path = None

    @abstractmethod
    def _build_prompt(self, **kwargs) -> str:
        """构建提示词"""
        raise NotImplementedError

    def _get_image_size(self, image_path: str) -> Tuple[int, int]:
        """获取图像尺寸（宽度和高度）- 公共方法

        Args:
            image_path (str): 图像路径

        Returns:
            Tuple[int, int]: 图像尺寸，格式为 (宽度, 高度)

        Raises:
            FileNotFoundError: 如果图像文件不存在
            ValueError: 如果无法读取图像文件
        """
        if not Path(image_path).exists():
            raise FileNotFoundError(f"图像文件不存在: {image_path}")

        try:
            with Image.open(image_path) as image:
                width, height = image.size
                return (width, height)
        except Exception as e:
            raise ValueError(f"无法读取图像文件 {image_path}: {str(e)}")

    def _choose_output_img_size(self, image_size: Tuple[int, int]) -> str:
        """根据输入图像尺寸选择最接近的输出图像尺寸 - 公共方法

        Args:
            image_size (Tuple[int, int]): 输入图像尺寸，格式为 (宽度, 高度)

        Returns:
            str: 符合接口要求的输出图像尺寸，格式为 "宽度*高度"
        """
        # 计算输入图像的长宽比
        aspect_ratio = image_size[0] / image_size[1]
        # 找到最接近的尺寸
        closest_size = min(SUPPORTED_OUTPUT_SIZES,
                           key=lambda x: abs(x[0] / x[1] - aspect_ratio))
        logging.info(f"输入图像尺寸: {image_size}，最接近的输出图像尺寸为: {closest_size}，"
                     f"长宽比为: {closest_size[0]/closest_size[1]:.2f}")
        return f"{closest_size[0]}*{closest_size[1]}"

    async def _download_img(self, image_url: str) -> str:
        """下载图像并保存到本地（异步），返回本地路径
        
        Args:
            image_url (str): 图像URL地址
        Returns:
            str: 本地保存路径
        """
        url_path = Path(image_url.split("?")[0])  # 移除查询参数
        filename = url_path.name

        if not filename or "." not in filename:
            filename = f"image_{uuid.uuid4().hex}.png"

        img_path = self.download_root_path / filename

        async with httpx.AsyncClient(timeout=HTTP_DOWNLOAD_TIMEOUT) as client:
            response = await client.get(image_url)
            response.raise_for_status()
            img_path.write_bytes(response.content)

        return str(img_path)

    async def call_generate_model(
            self,
            text: str,
            images: List[str] = [],
            model: str = "wan2.6-image",
            negative_prompt: str = "",
            prompt_extend: bool = True,
            watermark: bool = False,
            n: int = 1,
            size: str = "1280*1280",
            poll_interval: float = DEFAULT_POLL_INTERVAL,
            max_wait_time: float = DEFAULT_MAX_WAIT_TIME,
            timeout: float = HTTP_REQUEST_TIMEOUT) -> Dict[str, Any]:
        """
        生成图像并等待结果（同步等待异步任务完成）

        Args:
            text (str): 文本提示词
            images (List[str], optional): 图像列表，可以是 URL 字符串或本地文件路径，默认值为 []
            model (str, optional): 生成模型名称，默认值为 "wan2.6-image"
            negative_prompt (str, optional): 负面提示词，默认值为 ""
            prompt_extend (bool, optional): 是否扩展提示词，默认值为 True
            watermark (bool, optional): 是否添加水印，默认值为 False
            n (int, optional): 生成图像数量，默认值为 1
            size (str, optional): 图像尺寸，格式为 "宽度*高度"，默认值为 "1280*1280"
            poll_interval (float, optional): 轮询间隔（秒），默认值为 DEFAULT_POLL_INTERVAL (5.0)
            max_wait_time (float, optional): 最大等待时间（秒），默认值为 DEFAULT_MAX_WAIT_TIME (300.0)
            timeout (float, optional): 请求超时时间（秒），默认值为 HTTP_REQUEST_TIMEOUT (60.0)

        Returns:
            Dict[str, Any]: 最终任务结果字典（来自 DashScope 图像生成 API）

        Raises:
            ValueError: 当无法获取任务ID时
            RuntimeError: 当任务失败或下载图像失败时
            TimeoutError: 当等待任务完成超时时
            httpx.HTTPError: 当网络请求失败时
        """
        # 提交任务
        task_response = await self.wan_client.send_request(
            text=text,
            images=images,
            model=model,
            negative_prompt=negative_prompt,
            prompt_extend=prompt_extend,
            watermark=watermark,
            n=n,
            size=size,
            timeout=timeout)

        # 获取任务 ID
        task_id = task_response.get("output", {}).get("task_id")
        if not task_id:
            raise ValueError(f"无法获取任务ID，响应: {task_response}")

        # 轮询任务状态
        start_time = time.time()

        while True:
            result = await self.wan_client.get_task_result(task_id,
                                                           timeout=timeout)

            # 检查任务状态
            task_status = result.get("output", {}).get("task_status")

            if task_status == "SUCCEEDED":
                logging.info(f"DashScope图像生成任务 {task_id} 完成，开始下载图像...")
                output = result.get("output", {})
                choices = output.get("choices", [])
                for choice in choices:
                    try:
                        message = choice.get("message", {})
                        content = message.get("content")[0]
                        image_url = content.get("image", "")
                        if image_url and self.download_root_path:
                            saved_path = await self._download_img(image_url)
                            logging.info(f"图像已保存到: {saved_path}")
                    except Exception as e:
                        logging.exception(f"下载图像失败: {e}")
                        # 重新抛出异常，让调用方感知下载失败
                        raise RuntimeError(f"下载图像失败: {e}")

                return result
            elif task_status == "FAILED":
                error_code = result.get("output", {}).get("error_code", "任务失败")
                error_msg = result.get("output", {}).get("message", "任务失败")
                logging.error(
                    f"DashScope图像生成任务 {task_id} 失败，错误码: {error_code}，错误信息: {error_msg}"
                )
                raise RuntimeError(
                    f"任务失败: \n错误码: {error_code}\n错误信息: {error_msg}")

            if time.time() - start_time > max_wait_time:
                logging.error(f"等待任务 {task_id} 完成超时（超过 {max_wait_time} 秒）")
                raise TimeoutError(f"等待任务完成超时（超过 {max_wait_time} 秒）")

            await asyncio.sleep(poll_interval)

    @abstractmethod
    async def generate_try_on_img(self, *args, **kwargs):
        raise NotImplementedError
