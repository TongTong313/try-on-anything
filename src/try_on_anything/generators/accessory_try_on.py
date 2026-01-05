from .base import DashScopeImageGenerator
from typing import Tuple, Optional, Dict, Any
from PIL import Image
from pathlib import Path
import logging


class AccessoryTryOnImageGenerator(DashScopeImageGenerator):
    """饰品试戴效果图生成器，继承自 DashScopeImageGenerator

    至少需要输入两个图像：
    1. 饰品图像 (accessory_img)
    2. 人物图像 (person_img)
    可选输入图像：饰品细节图像（比如项链的吊坠）(accessory_detail_img)
    **额外输入饰品细节图像有利于增强试戴效果，尤其对于小饰品效果更佳**

    输出：试戴效果图(try_on_img)
    """

    def __init__(self, wan_client, download_root_path: Optional[str] = None):
        super().__init__(wan_client=wan_client,
                         download_root_path=download_root_path)

    def _get_image_size(self, image_path: str) -> Tuple[int, int]:
        """获取图像尺寸（宽度和高度）

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
        """根据输入任人物图像尺寸选择输出图像尺寸
        常见比例推荐的分辨率如下：
            - 1:1：1280*1280 
            - 2:3：800*1200
            - 3:2：1200*800
            - 3:4：960*1280
            - 4:3：1280*960
            - 9:16：720*1280
            - 16:9：1280*720
            - 21:9：1344*576

        Args:
            image_size (Tuple[int, int]): 输入图像尺寸，格式为 (宽度, 高度)

        Returns:
            str: 符合接口要求的输出图像尺寸，格式为 "宽度*高度"
        """
        # 常见尺寸列表，元组格式为 (宽度, 高度)
        size_list = [
            (1280, 1280),      # 1:1
            (800, 1200),       # 2:3
            (1200, 800),       # 3:2
            (960, 1280),       # 3:4
            (1280, 960),       # 4:3
            (720, 1280),       # 9:16
            (1280, 720),       # 16:9
            (1344, 576)        # 21:9
        ]

        # 首先计算输入图像的长宽比
        aspect_ratio = image_size[0] / image_size[1]
        # 找到最接近的尺寸，返回该尺寸（宽度*高度格式）
        closest_size = min(
            size_list, key=lambda x: abs(x[0]/x[1] - aspect_ratio))
        logging.info(
            f"输入图像尺寸: {image_size}，最接近的输出图像尺寸为: {closest_size}，长宽比为: {closest_size[0]/closest_size[1]}")
        return f"{closest_size[0]}*{closest_size[1]}"

    def _build_prompt(self, accessory_type: Optional[str] = None, person_position: Optional[str] = None, have_accessory_detail_img: bool = False) -> str:
        """根据是否有饰品细节图像，构建不同的提示词

        Args:
            accessory_type (Optional[str]): 饰品类型（例如：项链、耳环、手链、手表等），默认值为 None
            person_position (Optional[str]): 饰品的人物佩戴位置（例如：脖子、手腕、手指等），默认值为 None
            have_accessory_detail_img (bool): 是否有饰品细节图像，默认值为 False

        Returns:
            str: 构建的提示词
        """
        prompt = f"请将图1{accessory_type if accessory_type else '饰品'}戴到图2人物的{person_position if person_position else '对应位置'}，生成一张试戴效果图，需要注意不允许修改图2人物图像的其他任何元素，保证饰品和人物的比例合理"
        if have_accessory_detail_img:
            prompt += f"，图3是图1的饰品细节图像，要确保生成效果图的饰品细节与图3的饰品细节保持完全一致"
        return prompt

    async def generate_try_on_img(self,
                                  accessory_img_path: str,
                                  person_img_path: str,
                                  accessory_type: Optional[str] = None,
                                  person_position: Optional[str] = None,
                                  accessory_detail_img_path: Optional[str] = None,
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
        """生成试戴效果图

        Args:
            accessory_img_path (str): 饰品图像路径
            person_img_path (str): 人物图像路径
            accessory_type (Optional[str]): 饰品类型（例如：项链、耳环、手链、手表等），默认值为 None
            person_position (Optional[str]): 饰品的人物佩戴位置（例如：脖子、手腕、手指等），默认值为 None
            accessory_detail_img_path (Optional[str]): 饰品细节图像路径，默认值为 None
            model (str, optional): 生成模型名称，默认为 "wan2.6-image"
            negative_prompt (str, optional): 负面提示词，默认值为 ""
            prompt_extend (bool, optional): 是否扩展提示词，默认值为 True
            watermark (bool, optional): 是否添加水印，默认值为 False
            n (int, optional): 生成图像数量，默认值为 1
            size (str, optional): 图像尺寸，格式为 "宽度*高度"，默认值为 "1280*1280"
            poll_interval (float, optional): 轮询间隔（秒），默认值为 5.0
            max_wait_time (float, optional): 最大等待时间（秒），默认值为 300.0
            timeout (float, optional): 请求超时时间（秒），默认值为 60.0

        Returns:
            Dict[str, Any]: 生成的试戴效果图结果（由 DashScope 图像生成 API 提供）
        """
        # 获取人物图像尺寸（宽度和高度）
        person_img_size = self._get_image_size(person_img_path)
        # 根据人物图像尺寸选择输出图像尺寸（格式：宽度*高度）
        output_size = self._choose_output_img_size(person_img_size)

        # 准备图像列表
        images = [accessory_img_path, person_img_path]
        if accessory_detail_img_path:
            images.append(accessory_detail_img_path)

        # 构建提示词
        prompt = self._build_prompt(
            accessory_type=accessory_type,
            person_position=person_position,
            have_accessory_detail_img=accessory_detail_img_path is not None
        )

        # 调用生成图像接口
        result = await self.generate_img(
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
            timeout=timeout
        )

        return result
