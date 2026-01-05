from typing import List, Optional, Dict, Any
import asyncio
import time
import base64
import logging
import httpx
from ..clients import WanModelClient
from pathlib import Path


class DashScopeImageGenerator:
    """DashScope 图片生成 API 客户端"""

    def __init__(
        self,
        wan_client: WanModelClient,
        download_root_path: Optional[str] = None
    ):
        """
        初始化客户端

        Args:
            wan_client (WanModelClient): Wan 模型客户端实例
            download_root_path (str, optional): 下载生成的图片保存路径，默认为 None。如果保存路径为 None，则不下载生成的图片。
        """
        self.wan_client = wan_client
        if download_root_path:
            download_dir = Path(download_root_path)
            if not download_dir.exists():
                logging.warning(
                    f"下载生成图片保存路径不存在，创建路径: {download_root_path}"
                )
                download_dir.mkdir(parents=True, exist_ok=True)
            self.download_root_path = download_dir
        else:
            self.download_root_path = None

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
            filename = f"image_{int(time.time())}.png"

        img_path = self.download_root_path / filename

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(image_url)
            response.raise_for_status()
            img_path.write_bytes(response.content)

        return str(img_path)

    async def generate_img(
        self,
        text: str,
        images: List[str] = [],
        model: str = "wan2.6-image",
        negative_prompt: str = "",
        prompt_extend: bool = True,
        watermark: bool = False,
        n: int = 1,
        size: str = "1280*1280",
        poll_interval: float = 5.0,
        max_wait_time: float = 300.0,
        timeout: float = 60.0
    ) -> Dict[str, Any]:
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
            poll_interval (float, optional): 轮询间隔（秒），默认值为 2.0
            max_wait_time (float, optional): 最大等待时间（秒），默认值为 300.0
            timeout (float, optional): 请求超时时间（秒），默认值为 60.0

        Returns:
            Dict[str, Any]: 最终任务结果字典（来自 DashScope 图像生成 API）
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
            timeout=timeout
        )

        # 获取任务 ID
        task_id = task_response.get("output", {}).get("task_id")
        if not task_id:
            raise ValueError(f"无法获取任务ID，响应: {task_response}")

        # 轮询任务状态
        start_time = time.time()

        while True:
            result = await self.wan_client.get_task_result(task_id, timeout=timeout)

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

                return result
            elif task_status == "FAILED":
                error_code = result.get("output", {}).get("error_code", "任务失败")
                error_msg = result.get("output", {}).get("message", "任务失败")
                logging.error(f"DashScope图像生成任务 {task_id} 失败，错误码: {error_code}，错误信息: {error_msg}")
                raise RuntimeError(
                    f"任务失败: \n错误码: {error_code}\n错误信息: {error_msg}")

            if time.time() - start_time > max_wait_time:
                logging.error(f"等待任务 {task_id} 完成超时（超过 {max_wait_time} 秒）")
                raise TimeoutError(f"等待任务完成超时（超过 {max_wait_time} 秒）")

            await asyncio.sleep(poll_interval)
