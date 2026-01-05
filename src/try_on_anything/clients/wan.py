from typing import List, Optional, Dict, Any
import os
import logging
import httpx
import base64
import mimetypes

class WanModelClient:
    """通义万相-图像生成与编辑模型调用类"""

    def __init__(self, api_key: Optional[str] = None):
        """
        初始化模型调用类

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

    def _encode_img(self, image_path: str) -> str:
        """将本地图像转换为base64编码，并转换为dashscope的标准输入格式，采用DashScope官方实现方案：
        格式：data:{MIME_type};base64,{base64_data}
        示例：data:image/jpeg;base64,GDU7MtCZzEbTbmRZ...

        Args:
            image_path (str): 本地图像路径

        Returns:
            str: base64编码
        """
        mime_type, _ = mimetypes.guess_type(image_path)
        if not mime_type or not mime_type.startswith("image/"):
            logging.error(f"不支持或无法识别的图像格式: {image_path}")
            raise ValueError("不支持或无法识别的图像格式")
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
        return f"data:{mime_type};base64,{encoded_string}"

    async def send_request(
        self,
        text: str,
        images: List[str] = [],
        model: str = "wan2.6-image",
        negative_prompt: str = "",
        prompt_extend: bool = True,
        watermark: bool = False,
        n: int = 1,
        size: str = "1280*1280",
        timeout: float = 60.0
    ) -> Dict[str, Any]:
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
            timeout (float, optional): 请求超时时间（秒），默认值为 60.0

        Returns:
            Dict[str, Any]: 包含任务 ID 的字典，用于后续查询结果
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
                "messages": [
                    {
                        "role": "user",
                        "content": content
                    }
                ]
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
                response = await client.post(
                    self.base_url,
                    headers=self.headers,
                    json=payload
                )
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

                logging.error("API请求失败", extra={
                    "status_code": error_info["状态码"],
                    "url": error_info["URL"],
                    "error_detail": error_detail,
                })
                raise

    async def get_task_result(
        self,
        task_id: str,
        timeout: float = 60.0
    ) -> Dict[str, Any]:
        """
        查询异步任务结果

        Args:
            task_id (str): 任务 ID，从 generate_image 返回的结果中获取
            timeout (float, optional): 请求超时时间（秒），默认值为 60.0

        Returns:
            Dict[str, Any]: 任务结果字典（由 DashScope 图像生成 API 提供）
        """
        query_url = f"https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}"
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }

        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(query_url, headers=headers)
            response.raise_for_status()
            return response.json()
