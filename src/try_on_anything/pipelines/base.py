from abc import ABC, abstractmethod
from typing import Callable, Awaitable, Optional
import logging

from ..utils import encode_image_for_vl
from ..common.types import VLModelParsedResult
from ..common.constants import VL_MODEL_MAX_TOKENS, VL_MODEL_THINKING_BUDGET
from ..generators.base import DashScopeImageGenerator
from ..clients import QwenVLClient


class BaseTryOnPipeline(ABC):
    """试穿Pipeline基类

    Args:
        img_generator (DashScopeImageGenerator): 图像生成器实例
    """

    def __init__(self, img_generator: DashScopeImageGenerator):
        # 图像生成器
        self.img_generator: DashScopeImageGenerator = img_generator

    @abstractmethod
    async def run(self, **kwargs):
        """执行试穿Pipeline的抽象方法，子类必须实现此方法

        Args:
            **kwargs: 具体Pipeline执行所需的参数，由子类定义

        Returns:
            试穿结果，具体返回值由子类定义
        """
        pass


class VLModelEnhancedTryOnPipeline(BaseTryOnPipeline):
    """使用VL模型增强试穿效果的Pipeline中间层基类

    这是一个抽象类，为需要VL模型增强的Pipeline提供通用的VL模型调用逻辑。
    子类需要实现具体的系统提示词和响应解析方法。

    Args:
        img_generator (DashScopeImageGenerator): 图像生成器实例
        vl_client (QwenVLClient): VL模型客户端实例
        use_vl_model (bool, optional): 是否使用VL模型增强效果，默认值为 True
    """

    def __init__(self,
                 img_generator: DashScopeImageGenerator,
                 vl_client: QwenVLClient,
                 use_vl_model: bool = True):

        super().__init__(img_generator=img_generator)
        self.use_vl_model = use_vl_model
        self.vl_client = vl_client

    @property
    @abstractmethod
    def system_prompt_for_vl_model(self) -> str:
        """VL模型增强pipeline必须实现VL大模型的系统提示词"""
        pass

    @abstractmethod
    def _parse_vl_model_response(self, response: str) -> VLModelParsedResult:
        """VL模型增强pipeline必须实现VL大模型的响应解析"""
        pass

    async def _call_vl_model(
        self,
        img_path: str,
        vl_model_name: str,
        max_tokens: int = VL_MODEL_MAX_TOKENS,
        enable_thinking: bool = True,
        thinking_budget: int = VL_MODEL_THINKING_BUDGET,
        status_callback: Optional[Callable[[str, int], Awaitable[None]]] = None
    ) -> VLModelParsedResult:
        """通用方法：VL模型增强pipeline中VL大模型的调用，子类可以复用或重写此方法

        Args:
            img_path (str): 图像路径
            vl_model_name (str): VL模型名称
            max_tokens (int, optional): VL模型最大输出token数，默认值为 VL_MODEL_MAX_TOKENS
            enable_thinking (bool, optional): 是否启用VL模型的思考模式，默认值为 True
            thinking_budget (int, optional): VL模型思考预算，默认值为 VL_MODEL_THINKING_BUDGET
            status_callback (Callable[[str, int], Awaitable[None]], optional): 状态回调函数，默认值为 None。
                回调函数接收两个参数：status (str) 当前状态描述，progress (int) 进度百分比 (0-100)

        Returns:
            VLModelParsedResult: VL模型解析结果对象
        """

        # 如果启用VL模型，则先调用VL模型提取信息
        # 使用纯 base64 编码，不含 data:image/xxx;base64, 前缀
        img_base64_for_vl = encode_image_for_vl(img_path)

        # 通过回调通知调用方：VL模型分析开始
        if status_callback:
            await status_callback("VL模型分析图像中...", 10)

        logging.info("使用VL模型分析图像...")
        vl_messages = [{
            "role": "system",
            "content": self.system_prompt_for_vl_model
        }, {
            "role":
            "user",
            "content": [{
                "type": "image_url",
                "image_url": {
                    "url": img_base64_for_vl
                }
            }]
        }]
        # 调用VL模型
        response = await self.vl_client.chat(
            model=vl_model_name,
            messages=vl_messages,
            max_tokens=max_tokens,
            enable_thinking=enable_thinking,
            thinking_budget=thinking_budget)
        vl_response = response.content

        # 解析VL模型的响应内容
        vl_parsed_result = self._parse_vl_model_response(vl_response)

        return vl_parsed_result
