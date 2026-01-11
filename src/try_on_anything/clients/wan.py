from typing import List, Optional, Dict, Any
import os
import logging
import httpx
import base64
import mimetypes
import io
from PIL import Image
from ..common.constants import (
    MIN_IMAGE_SIZE_FOR_WAN,
    MAX_IMAGE_SIZE_FOR_WAN,
    HTTP_REQUEST_TIMEOUT
)


class WanModelClient:
    """通义万相-图像生成与编辑模型调用类"""

    def __init__(self, api_key: Optional[str] = None):
        """
        初始化模型调用类，对于图像的输入需要满足WAN模型的最小和最大尺寸要求，最小尺寸为384，最大尺寸为5000

        Args:
            api_key (str, optional): API 密钥，如果不提供则从环境变量 WAN_API_KEY 读取，默认值为 None。
        """
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key 未提供，请设置 DASHSCOPE_API_KEY 环境变量或传入 api_key 参数")

        # 设置API URL和请求头
        self.base_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/image-generation/generation"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "X-DashScope-Async": "enable"
        }

    def _ensure_size_limits(self, img: Image.Image) -> Image.Image:
        """确保图像尺寸符合 API 要求，如果太小则等比例放大，如果太大则等比例缩小

            Args:
                img (Image.Image): 输入图像

            Returns:
                Image.Image: 处理后的图像（尺寸符合要求）

            Raises:
                ValueError: 当图像宽高比过大，无法同时满足最小边和最大边约束时抛出
            """
        width, height = img.size
        min_dim = min(width, height)
        max_dim = max(width, height)

        # 检查极端情况：同时违反最小边和最大边约束
        if min_dim < MIN_IMAGE_SIZE_FOR_WAN and max_dim > MAX_IMAGE_SIZE_FOR_WAN:
            # 计算放大到最小边要求后，最大边会变成多少
            scale_for_min = MIN_IMAGE_SIZE_FOR_WAN / min_dim
            projected_max = max_dim * scale_for_min

            if projected_max > MAX_IMAGE_SIZE_FOR_WAN:
                # 计算当前宽高比和允许的最大宽高比
                current_aspect_ratio = max_dim / min_dim
                max_allowed_aspect_ratio = MAX_IMAGE_SIZE_FOR_WAN / MIN_IMAGE_SIZE_FOR_WAN

                error_msg = (
                    f"图像尺寸 {width}x{height} 的宽高比过大（{current_aspect_ratio:.2f}:1），"
                    f"无法同时满足最小边 >= {MIN_IMAGE_SIZE_FOR_WAN} 和最大边 <= {MAX_IMAGE_SIZE_FOR_WAN} 的要求。"
                    f"允许的最大宽高比为 {max_allowed_aspect_ratio:.2f}:1。"
                    f"请使用宽高比更合理的图像。")
                logging.error(error_msg)
                raise ValueError(error_msg)

        # 检查是否需要调整尺寸
        needs_resize = False
        scale = 1.0

        # 计算需要的缩放比例，同时满足最小边和最大边的约束
        if min_dim < MIN_IMAGE_SIZE_FOR_WAN:
            # 需要放大以满足最小边要求
            scale_for_min = MIN_IMAGE_SIZE_FOR_WAN / min_dim
            scale = max(scale, scale_for_min)
            needs_resize = True
            logging.warning(
                f"图像尺寸 {width}x{height} 的最小边 {min_dim} 小于要求 Wan 模型最小边要求 {MIN_IMAGE_SIZE_FOR_WAN}，将进行放大后编码"
            )

        if max_dim > MAX_IMAGE_SIZE_FOR_WAN:
            # 需要缩小以满足最大边要求
            scale_for_max = MAX_IMAGE_SIZE_FOR_WAN / max_dim
            scale = min(scale, scale_for_max)
            needs_resize = True
            logging.warning(
                f"图像尺寸 {width}x{height} 的最大边 {max_dim} 超过要求 Wan 模型最大边要求 {MAX_IMAGE_SIZE_FOR_WAN}，将进行缩小后编码"
            )

        # 执行缩放
        if needs_resize:
            new_width = int(width * scale)
            new_height = int(height * scale)
            logging.info(
                f"图像尺寸从 {width}x{height} 调整到 {new_width}x{new_height} (缩放比例: {scale:.3f})"
            )
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        return img

    def _encode_img(self, image_path: str) -> str:
        """将本地图像转换为base64编码，并转换为dashscope的标准输入格式，采用DashScope官方实现方案：
        格式：data:{MIME_type};base64,{base64_data}
        示例：data:image/jpeg;base64,GDU7MtCZzEbTbmRZ...

        在编码前会自动检查并调整图像尺寸，确保符合 API 要求（最小边 >= 384，最大边 <= 5000）

        Args:
            image_path (str): 本地图像路径

        Returns:
            str: base64编码
        """
        mime_type, _ = mimetypes.guess_type(image_path)
        if not mime_type or not mime_type.startswith("image/"):
            logging.error(f"不支持或无法识别的图像格式: {image_path}")
            raise ValueError("不支持或无法识别的图像格式")

        # 打开图像并确保尺寸符合要求
        img = Image.open(image_path)
        img = self._ensure_size_limits(img)

        # 将处理后的图像转换为字节流
        img_byte_arr = io.BytesIO()
        # 保持原始格式，如果是JPEG则使用JPEG，否则使用PNG
        img_format = img.format if img.format else 'PNG'
        if img_format == 'JPEG':
            img.save(img_byte_arr, format='JPEG', quality=95)
        else:
            img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)

        # 编码为base64
        encoded_string = base64.b64encode(img_byte_arr.read()).decode('utf-8')
        return f"data:{mime_type};base64,{encoded_string}"

    async def send_request(self,
                           text: str,
                           images: List[str] = [],
                           model: str = "wan2.6-image",
                           negative_prompt: str = "",
                           prompt_extend: bool = True,
                           watermark: bool = False,
                           n: int = 1,
                           size: str = "1280*1280",
                           timeout: float = HTTP_REQUEST_TIMEOUT) -> Dict[str, Any]:
        """
        向通义万象系列模型发送请求

        Args:
            text (str): 文本提示词
            images (List[str], optional): 图像列表，可以是 URL 字符串或本地文件路径，默认值为 []
            model (str, optional): 模型名称，默认为 "wan2.6-image"
            negative_prompt (str, optional): 负面提示词，默认值为 ""
            prompt_extend (bool, optional): 是否扩展提示词，默认值为 True
            watermark (bool, optional): 是否添加水印，默认值为 False
            n (int, optional): 生成图像数量，默认值为 1
            size (str, optional): 图像尺寸，格式为 "宽度*高度"，默认值为 "1280*1280"
            timeout (float, optional): 请求超时时间（秒），默认值为 HTTP_REQUEST_TIMEOUT (60.0)

        Returns:
            Dict[str, Any]: 包含任务 ID 的字典，用于后续查询结果

        Raises:
            ValueError: 当图像格式不支持或尺寸无法满足要求时
            FileNotFoundError: 当本地图像文件不存在时
            httpx.HTTPStatusError: 当 API 返回错误状态码时
            httpx.TimeoutException: 当请求超时时
        """
        # 构建消息内容
        content = [{"text": text}]

        # 添加图像
        for image in images:
            if image.startswith("http"):
                content.append({"image": image})
            else:
                content.append({"image": self._encode_img(image)})

        # 构建请求体
        payload = {
            "model": model,
            "input": {
                "messages": [{
                    "role": "user",
                    "content": content
                }]
            },
            "parameters": {
                "negative_prompt": negative_prompt,
                "prompt_extend": prompt_extend,
                "watermark": watermark,
                "n": n,
                "size": size
            }
        }

        # 发送异步请求
        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                response = await client.post(self.base_url,
                                             headers=self.headers,
                                             json=payload)
                response.raise_for_status()
                # 返回响应json字段
                return response.json()
            except httpx.HTTPStatusError as e:
                # 捕获HTTP错误，特别是400错误
                error_info = {
                    "状态码": e.response.status_code if e.response else "N/A",
                    "URL": str(e.request.url) if e.request else self.base_url,
                }

                # 尝试解析错误响应
                error_detail = None
                if e.response:
                    try:
                        error_detail = e.response.json()
                    except:
                        error_detail = e.response.text

                logging.error("API请求失败",
                              extra={
                                  "status_code": error_info["状态码"],
                                  "url": error_info["URL"],
                                  "error_detail": error_detail,
                              })
                raise

    async def get_task_result(self,
                              task_id: str,
                              timeout: float = HTTP_REQUEST_TIMEOUT) -> Dict[str, Any]:
        """
        查询异步任务结果

        Args:
            task_id (str): 任务 ID，从 generate_image 返回的结果中获取
            timeout (float, optional): 请求超时时间（秒），默认值为 HTTP_REQUEST_TIMEOUT (60.0)

        Returns:
            Dict[str, Any]: 任务结果字典（由 DashScope 图像生成 API 提供）

        Raises:
            httpx.HTTPStatusError: 当 API 返回错误状态码时
            httpx.TimeoutException: 当请求超时时
        """
        query_url = f"https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}"
        headers = {"Authorization": f"Bearer {self.api_key}"}

        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(query_url, headers=headers)
            response.raise_for_status()
            return response.json()
