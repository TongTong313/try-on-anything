import re
import textwrap
import base64
import mimetypes
from typing import List, Tuple, Optional, Dict, Any, Callable, Awaitable
from ..generators.accessory_try_on import AccessoryTryOnImageGenerator   
from pathlib import Path
from PIL import Image
from ..clients import QwenVLClient, WanModelClient
from .types import VLModelParsedResult
from .base import TryOnPipeline
import logging

# Wan模型 API 要求的最小图像尺寸
MIN_IMAGE_SIZE_FOR_WAN = 384

# 状态回调函数类型定义
# StatusCallback: 用于通知调用方当前Pipeline执行状态的回调函数
# 参数说明:
#   - status (str): 当前状态描述，如 "VL模型分析饰品中..."、"试戴图像生成中..."
#   - progress (int): 当前进度百分比 (0-100)
# 返回值: 无返回值的协程（异步函数）
StatusCallback = Callable[[str, int], Awaitable[None]]


class AccessoryTryOnPipeline(TryOnPipeline):
    """饰品试戴Pipeline，继承自 TryOnPipeline

    Args:
        vl_client (QwenVLClient): VL模型客户端实例
        img_generator (AccessoryTryOnImageGenerator): 图像生成器实例
        use_vl_model (bool, optional): 是否使用VL模型增强穿戴效果，默认值为 True
    """

    def __init__(
        self,
        img_generator: AccessoryTryOnImageGenerator,
        vl_client: QwenVLClient,
        use_vl_model: bool = True,
    ):  
        # 父类初始化
        super().__init__(img_generator=img_generator)

        # 本类初始化
        self.use_vl_model = use_vl_model
        # VL模型客户端
        self.vl_client = vl_client

    @property
    def system_prompt_for_vl_model(self) -> str:
        return textwrap.dedent("""
            为了更好的实现饰品试戴的效果，我需要你帮我做一些信息的预提取。我给你提供了一张饰品的图像，你需要仔细分析这个饰品的图像，按照以下格式返回信息：

            <accessory_type>
            饰品类型名称，例如：项链、耳环、手链、手表等，如有不确定的，请返回"未知"。
            </accessory_type>

            <person_position>
            饰品的人物佩戴位置，例如：脖子、手腕、手指等，如有不确定的，请返回"未知"。
            </person_position>

            <detail_bbox>
            <x1>饰品细节区域左上角的X坐标（0到1之间的浮点数，表示相对值）</x1>
            <y1>饰品细节区域左上角的Y坐标（0到1之间的浮点数，表示相对值）</y1>
            <x2>饰品细节区域右下角的X坐标（0到1之间的浮点数，表示相对值）</x2>
            <y2>饰品细节区域右下角的Y坐标（0到1之间的浮点数，表示相对值）</y2>
            如果无法确定饰品细节区域，请将x1, y1, x2, y2均设置为0。
            </detail_bbox>

            注意：
            - 你必须严格按照上述格式返回结果，确保所有标签正确闭合且没有遗漏或错误。
            - 无论用户输入的是什么语言的提示词，你都必须输出中文便于我后续解析。

            示例：
            <accessory_type>项链</accessory_type>
            <person_position>脖子</person_position>
            <detail_bbox>
            <x1>0.1</x1>
            <y1>0.15</y1>
            <x2>0.3</x2>
            <y2>0.4</y2>
            </detail_bbox>
            """).strip()

    def _parse_vl_model_response(self, response: str) -> VLModelParsedResult:
        """解析VL模型的响应内容

        Args:
            response: VL模型返回的格式化字符串

        Returns:
            VLModelParsedResult: 解析结果对象
        """
        result = VLModelParsedResult(
            accessory_type=None,
            person_position=None,
            detail_bbox=None,
            parse_errors=[]
        )

        # 解析 accessory_type
        accessory_match = re.search(
            r'<accessory_type>\s*(.*?)\s*</accessory_type>', response, re.DOTALL)
        if accessory_match:
            result.accessory_type = accessory_match.group(1).strip()
        else:
            result.parse_errors.append("未找到 accessory_type 标签")

        # 解析 person_position
        position_match = re.search(
            r'<person_position>\s*(.*?)\s*</person_position>', response, re.DOTALL)
        if position_match:
            result.person_position = position_match.group(1).strip()
        else:
            result.parse_errors.append("未找到 person_position 标签")

        # 解析 detail_bbox
        bbox = self._parse_bbox(response)
        if bbox["valid"]:
            result.detail_bbox = {
                "x1": bbox["x1"],
                "y1": bbox["y1"],
                "x2": bbox["x2"],
                "y2": bbox["y2"]
            }
        else:
            result.parse_errors.extend(bbox["errors"])

        return result

    def _parse_bbox(self, response: str) -> Dict[str, Any]:
        """解析并校验边界框坐标

        Returns:
            Dict包含 x1, y1, x2, y2, valid, errors
        """
        bbox_result = {
            "x1": 0.0, "y1": 0.0, "x2": 0.0, "y2": 0.0,
            "valid": False,
            "errors": []
        }

        # 检查是否存在 detail_bbox 标签
        bbox_match = re.search(
            r'<detail_bbox>(.*?)</detail_bbox>', response, re.DOTALL)
        if not bbox_match:
            logging.error("未找到 detail_bbox 标签")
            bbox_result["errors"].append("未找到 detail_bbox 标签")
            return bbox_result

        bbox_content = bbox_match.group(1)

        # 解析四个坐标值
        coords = {}
        for coord_name in ['x1', 'y1', 'x2', 'y2']:
            pattern = rf'<{coord_name}>\s*(.*?)\s*</{coord_name}>'
            match = re.search(pattern, bbox_content, re.DOTALL)
            if match:
                try:
                    value = float(match.group(1).strip())
                    coords[coord_name] = value
                except ValueError:
                    logging.exception(f"{coord_name} 无法转换为数字: {match.group(1)}")
                    bbox_result["errors"].append(
                        f"{coord_name} 无法转换为数字: {match.group(1)}")
                    coords[coord_name] = 0.0
            else:
                logging.error(f"未找到 {coord_name} 标签")
                bbox_result["errors"].append(f"未找到 {coord_name} 标签")
                coords[coord_name] = 0.0

        # 校验坐标值范围 (0-1)
        for coord_name, value in coords.items():
            if value < 0:
                logging.warning(f"{coord_name} 值 {value} 小于0，已修正为0")
                bbox_result["errors"].append(
                    f"{coord_name} 值 {value} 小于0，已修正为0")
                coords[coord_name] = 0.0
            elif value > 1:
                logging.warning(f"{coord_name} 值 {value} 大于1，已修正为1")
                bbox_result["errors"].append(
                    f"{coord_name} 值 {value} 大于1，已修正为1")
                coords[coord_name] = 1.0

        # 校验左上角和右下角的关系
        if coords['x2'] <= coords['x1']:
            logging.error(f"x2({coords['x2']}) 应大于 x1({coords['x1']})，坐标无效")
            bbox_result["errors"].append(
                f"x2({coords['x2']}) 应大于 x1({coords['x1']})，坐标无效"
            )
        if coords['y2'] <= coords['y1']:
            logging.error(f"y2({coords['y2']}) 应大于 y1({coords['y1']})，坐标无效")
            bbox_result["errors"].append(
                f"y2({coords['y2']}) 应大于 y1({coords['y1']})，坐标无效"
            )

        # 检查是否全为0（模型表示无法确定）
        all_zero = all(coords[k] == 0.0 for k in ['x1', 'y1', 'x2', 'y2'])

        bbox_result.update(coords)

        # 只有坐标有效且不全为0时才标记为有效
        has_coord_errors = any("应大于" in e for e in bbox_result["errors"])
        bbox_result["valid"] = not has_coord_errors and not all_zero

        return bbox_result

    def crop_detail_image(self, image_path: str, bbox: Dict[str, float]) -> Image.Image:
        """根据边界框裁剪出饰品细节图像，并确保尺寸符合 API 要求

        Args:
            image_path (str): 原始图像路径
            bbox (Dict[str, float]): 边界框坐标，包含 x1, y1, x2, y2（相对坐标，0-1）

        Returns:
            Image.Image: 裁剪后的细节图像（如果尺寸太小会等比例放大）
        """
        def ensure_min_size(img: Image.Image) -> Image.Image:
            """确保图像尺寸符合 API 最小要求，如果太小则等比例放大

            Args:
                img (Image.Image): 输入图像

            Returns:
                Image.Image: 处理后的图像（尺寸符合要求）
            """
            width, height = img.size
            min_dim = min(width, height)

            # 如果最小边小于要求的最小尺寸，则等比例放大
            if min_dim < MIN_IMAGE_SIZE_FOR_WAN:
                logging.warning(
                    f"细节图尺寸 {width}x{height} 小于最小要求，{MIN_IMAGE_SIZE_FOR_WAN}，将进行等比例放大")
                scale = MIN_IMAGE_SIZE_FOR_WAN / min_dim
                new_width = int(width * scale)
                new_height = int(height * scale)
                logging.info(
                    f"细节图尺寸 {width}x{height} 小于最小要求 {MIN_IMAGE_SIZE_FOR_WAN}，等比例放大到 {new_width}x{new_height}")
                img = img.resize((new_width, new_height),
                                 Image.Resampling.LANCZOS)

            return img

        with Image.open(image_path) as img:
            width, height = img.size
            left = int(bbox['x1'] * width)
            upper = int(bbox['y1'] * height)
            right = int(bbox['x2'] * width)
            lower = int(bbox['y2'] * height)

            detail_img = img.crop((left, upper, right, lower))
            detail_img.load()  # 强制加载像素数据到内存，使图像独立

            # 检查裁剪后的尺寸，如果太小则等比例放大
            detail_img = ensure_min_size(detail_img)
            return detail_img

    def _encode_image_for_vl(self, image_path: str) -> str:
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


    async def run(
        self,
        accessory_img_path: str,
        person_img_path: str,
        accessory_detail_img_path: Optional[str] = None,
        accessory_type: Optional[str] = None,
        person_position: Optional[str] = None,
        vl_model_name: str = "qwen3-vl-plus",
        img_gen_model_name: str = "wan2.6-image",
        status_callback: Optional[StatusCallback] = None,
    ) -> Dict[str, Any]:
        """运行饰品试戴Pipeline

        pipline流程：
            1. 用户输入饰品图和人物图，可选输入饰品细节图
            2. 如果启用VL模型，则先调用VL模型，提取饰品类型、佩戴位置和饰品细节区域
               如果不启用VL模型，则饰品类型、佩戴位置都默认为None
            3. 如果VL模型提取到有效的细节区域，则自动裁剪出细节图
            4. 调用试戴图像生成模型

        Args:
            accessory_img_path (str): 饰品图像路径
            person_img_path (str): 人物图像路径
            accessory_detail_img_path (Optional[str], optional): 饰品细节图像路径。
                如果提供，则直接使用；如果不提供且启用VL模型，则自动裁剪。默认值为 None
            accessory_type (Optional[str], optional): 饰品类型（例如：项链、耳环、手链、手表等）。
                如果提供，则直接使用；如果不提供且启用VL模型，则使用VL模型识别的结果。默认值为 None
            person_position (Optional[str], optional): 饰品的人物佩戴位置（例如：脖子、手腕、手指等）。
                如果提供，则直接使用；如果不提供且启用VL模型，则使用VL模型识别的结果。默认值为 None
            vl_model_name (str, optional): VL模型名称。默认为 "qwen3-vl-plus"
            img_gen_model_name (str, optional): 生成模型名称。默认为 "wan2.6-image"
            status_callback (Optional[StatusCallback], optional): 状态回调函数，用于通知调用方当前执行状态。
                回调函数签名: async def callback(status: str, progress: int) -> None
                - status: 当前状态描述文本
                - progress: 当前进度百分比 (0-100)
                默认值为 None（不进行状态回调）

        Returns:
            Dict[str, Any]: 生成的试戴效果图结果，包含生成图像的URL或路径等信息

        Raises:
            可能抛出的异常取决于底层的VL客户端和图像生成器实现

        Note:
            - 如果启用VL模型（use_vl_model=True），会自动分析饰品图像
            - VL模型分析可能产生解析错误，这些错误会被记录到日志中
            - 自动裁剪的细节图会保存在与原饰品图相同的目录下
        """
        # 验证输入文件是否存在
        if not Path(accessory_img_path).exists():
            raise FileNotFoundError(f"饰品图像文件不存在: {accessory_img_path}")
        if not Path(person_img_path).exists():
            raise FileNotFoundError(f"人物图像文件不存在: {person_img_path}")
        if accessory_detail_img_path and not Path(accessory_detail_img_path).exists():
            raise FileNotFoundError(
                f"饰品细节图像文件不存在: {accessory_detail_img_path}")

        # 保存用户传入的参数（如果有的话，优先使用用户指定的值）
        user_accessory_type = accessory_type
        user_person_position = person_position

        if self.use_vl_model:
            # 如果启用VL模型，则先调用VL模型提取信息
            # 使用纯 base64 编码，不含 data:image/xxx;base64, 前缀
            accessory_img_base64_for_vl = self._encode_image_for_vl(
                accessory_img_path)

            # 通过回调通知调用方：VL模型分析开始
            if status_callback:
                await status_callback("VL模型分析饰品中...", 10)

            logging.info("使用VL模型分析饰品图像...")
            vl_messages = [
                {"role": "system", "content": self.system_prompt_for_vl_model},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": accessory_img_base64_for_vl
                            }
                        }
                    ]
                }
            ]
            # 使用 asyncio.run() 调用异步的 chat 方法
            vl_response = await self.vl_client.chat(
                model=vl_model_name,
                messages=vl_messages,
                max_tokens=1024 * 8,
                enable_thinking=True,
                thinking_budget=1024 * 8
            )
            vl_response_content = vl_response.content
            vl_parsed_result = self._parse_vl_model_response(
                vl_response_content)

            # 使用VL模型提取的信息（如果用户没有手动指定，则使用VL模型识别的结果）
            accessory_type = user_accessory_type if user_accessory_type else vl_parsed_result.accessory_type
            person_position = user_person_position if user_person_position else vl_parsed_result.person_position

            # 如果用户已经提供了饰品细节图，则直接使用
            # 如果用户没有提供饰品细节图且VL模型提取到了有效的细节区域，则裁剪出细节图
            if not accessory_detail_img_path:
                if vl_parsed_result.detail_bbox:
                    detail_bbox = vl_parsed_result.detail_bbox
                    accessory_detail_img = self.crop_detail_image(
                        accessory_img_path, detail_bbox)
                    # 在accessory_img_path相同根目录下保存裁剪的细节图，保持原始图像格式
                    original_suffix = Path(accessory_img_path).suffix
                    accessory_detail_img_path = str(Path(accessory_img_path).with_name(
                        Path(accessory_img_path).stem + "_detail" + original_suffix))
                    accessory_detail_img.save(accessory_detail_img_path)

            # 记录解析错误信息
            if len(vl_parsed_result.parse_errors) > 0:
                logging.warning(
                    f"解析过程中存在如下错误，可能会导致解析精度出现下降: {vl_parsed_result.parse_errors}")
            # 打印解析结果
            logging.info(
                f"VL模型解析完成！解析结果为：饰品类型: {accessory_type}，佩戴位置: {person_position}，细节图路径: {accessory_detail_img_path if accessory_detail_img_path else '无'}")
        else:
            # 不使用VL模型时，直接使用用户传入的参数
            accessory_type = user_accessory_type
            person_position = user_person_position

        # 结合VL模型解析结果（如有）和用户输入，调用试戴图像生成模型
        # 通过回调通知调用方：图像生成开始
        if status_callback:
            await status_callback("试戴图像生成中...", 50)

        logging.info(
            f"正在调用试戴图像生成模型...\n饰品类型: {accessory_type}\n佩戴位置: {person_position}\n细节图路径: {accessory_detail_img_path if accessory_detail_img_path else '无'}")
        try:
            result = await self.img_generator.generate_try_on_img(
                accessory_img_path=accessory_img_path,
                person_img_path=person_img_path,
                accessory_type=accessory_type,
                person_position=person_position,
                accessory_detail_img_path=accessory_detail_img_path,
                model=img_gen_model_name,
            )
        except Exception as e:
            logging.error(f"调用试戴图像生成模型失败: {e}")
            raise e

        # 在结果中添加VL模型识别的信息，便于后端使用
        result["accessory_type"] = accessory_type
        result["person_position"] = person_position

        return result
