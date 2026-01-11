from typing import Optional, Dict, Any
import textwrap

from .base import DashScopeImageGenerator
from ..clients import WanModelClient
from ..common.constants import (DEFAULT_POLL_INTERVAL, DEFAULT_MAX_WAIT_TIME,
                                HTTP_REQUEST_TIMEOUT)


class ClothingTryOnImageGenerator(DashScopeImageGenerator):
    """服装试穿效果图生成器，继承自 DashScopeImageGenerator   

    Args:
        wan_client (WanModelClient): Wan 模型客户端实例
        download_root_path (str, optional): 下载生成的图片保存路径，默认为 None。如果保存路径为 None，则不下载生成的图片。
    """

    # 基础提示词模板
    _BASE_PROMPT = "请将图1的{clothing_type}穿到图2人物的{person_position}，生成一张试穿效果图，需要注意不允许修改图2人物图像的其他任何元素，保证衣服和人物的比例合理"

    # 服装试穿的额外要求提示词
    _ADDITIONAL_REQUIREMENTS_PROMPT = textwrap.dedent("""\
        # 额外要求：
        1. 衣服试穿要彻底，要彻底删除原有的人物对应的服装，不要保留任何痕迹
    """)

    def __init__(self,
                 wan_client: WanModelClient,
                 download_root_path: Optional[str] = None) -> None:
        super().__init__(wan_client=wan_client,
                         download_root_path=download_root_path)

    def _build_prompt(self,
                      clothing_type: Optional[str] = None,
                      person_position: Optional[str] = None) -> str:
        """根据不同的服装类型和穿戴位置构建提示词

        Args:
            clothing_type (Optional[str]): 服装类型（例如：上衣、裤子、鞋子等），默认值为 None
            person_position (Optional[str]): 服装的人物穿戴位置（例如：上身、下身、脚上等），默认值为 None

        Returns:
            str: 构建的提示词
        """
        prompt = self._BASE_PROMPT.format(
            clothing_type=clothing_type if clothing_type else '服装',
            person_position=person_position if person_position else '对应位置')
        prompt += f"\n{self._ADDITIONAL_REQUIREMENTS_PROMPT}"

        return prompt

    async def generate_try_on_img(
            self,
            clothing_img_path: str,
            person_img_path: str,
            clothing_type: Optional[str] = None,
            person_position: Optional[str] = None,
            model: str = "wan2.6-image",
            negative_prompt: str = "",
            prompt_extend: bool = True,
            watermark: bool = False,
            n: int = 1,
            poll_interval: float = DEFAULT_POLL_INTERVAL,
            max_wait_time: float = DEFAULT_MAX_WAIT_TIME,
            timeout: float = HTTP_REQUEST_TIMEOUT) -> Dict[str, Any]:
        """生成服装试穿效果图

        Args:
            clothing_img_path (str): 服装图像路径
            person_img_path (str): 人物图像路径
            clothing_type (Optional[str]): 服装类型（例如：上衣、裤子、鞋子等），默认值为 None
            person_position (Optional[str]): 服装的人物穿戴位置（例如：上身、下身、脚上等），默认值为 None
            model (str, optional): 生成模型名称，默认为 "wan2.6-image"
            negative_prompt (str, optional): 负面提示词，默认值为 ""
            prompt_extend (bool, optional): 是否扩展提示词，默认值为 True
            watermark (bool, optional): 是否添加水印，默认值为 False
            n (int, optional): 生成图像数量，默认值为 1
            poll_interval (float, optional): 轮询间隔（秒），默认值为 DEFAULT_POLL_INTERVAL (5.0)
            max_wait_time (float, optional): 最大等待时间（秒），默认值为 DEFAULT_MAX_WAIT_TIME (300.0)
            timeout (float, optional): 请求超时时间（秒），默认值为 HTTP_REQUEST_TIMEOUT (60.0)

        Returns:
            Dict[str, Any]: 生成的试穿效果图结果（由 DashScope 图像生成 API 提供）

        Raises:
            FileNotFoundError: 当图像文件不存在时
            ValueError: 当图像尺寸不符合要求时
            RuntimeError: 当任务失败或下载图像失败时
            TimeoutError: 当等待任务完成超时时
        """
        # 获取人物图像尺寸（宽度和高度）
        person_img_size = self._get_image_size(person_img_path)
        # 根据人物图像尺寸选择输出图像尺寸（格式：宽度*高度）
        output_size = self._choose_output_img_size(person_img_size)

        # 准备图像列表
        images = [clothing_img_path, person_img_path]

        # 构建提示词
        prompt = self._build_prompt(clothing_type=clothing_type,
                                    person_position=person_position)

        # 调用生成图像接口
        result = await self.call_generate_model(
            text=prompt,
            images=images,
            size=output_size,
            model=model,
            negative_prompt=negative_prompt,
            prompt_extend=prompt_extend,
            watermark=watermark,
            n=n,
            poll_interval=poll_interval,
            max_wait_time=max_wait_time,
            timeout=timeout)

        return result
