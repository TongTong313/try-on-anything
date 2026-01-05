import logging
from ..clients import QwenVLClient
from ..generators.base import DashScopeImageGenerator
from typing import Callable, Awaitable, Optional
from abc import ABC, abstractmethod


class TryOnPipeline(ABC):
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




