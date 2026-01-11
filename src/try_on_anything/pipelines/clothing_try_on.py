import textwrap
import re
import logging
from typing import Optional, Dict, Any
from pathlib import Path

from ..generators.clothing_try_on import ClothingTryOnImageGenerator
from ..clients import QwenVLClient
from ..pipelines.base import VLModelEnhancedTryOnPipeline
from ..common.types import VLModelParsedResult, StatusCallback


class ClothingTryOnPipeline(VLModelEnhancedTryOnPipeline):
    """服装试穿Pipeline，继承自 VLModelEnhancedTryOnPipeline
    
    Args:
        vl_client (QwenVLClient): VL模型客户端实例
        img_generator (ClothingTryOnImageGenerator): 图像生成器实例
        use_vl_model (bool, optional): 是否使用VL模型增强穿戴效果，默认值为 True
    """

    def __init__(
        self,
        img_generator: ClothingTryOnImageGenerator,
        vl_client: QwenVLClient,
        use_vl_model: bool = True,
    ):
        # 父类初始化
        super().__init__(img_generator=img_generator,
                         vl_client=vl_client,
                         use_vl_model=use_vl_model)

    @property
    def system_prompt_for_vl_model(self) -> str:
        return textwrap.dedent("""
            为了更好的实现服装试穿的效果，我需要你帮我做一些信息的预提取。我给你提供了一张服装的图像，你需要仔细分析这个服装的图像，按照以下格式返回信息：

            <clothing_type>
            服装类型名称，例如：上衣、裤子、鞋子等，如有不确定的，请返回""（空字符串）。
            </clothing_type>

            <person_position>
            服装的人物穿着位置，例如：上身、下身、脚上等，如有不确定的，请返回""（空字符串）。
            </person_position>

            注意：
            - 你必须严格按照上述格式返回结果，确保所有标签正确闭合且没有遗漏或错误。
            - 无论用户输入的是什么语言的提示词，你都必须输出中文便于我后续解析。

            示例：
            <clothing_type>上衣</clothing_type>
            <person_position>上身</person_position>
            """).strip()

    def _parse_vl_model_response(self, response: str) -> VLModelParsedResult:
        """解析VL模型的响应内容

        Args:
            response: VL模型返回的格式化字符串

        Returns:
            VLModelParsedResult: 解析结果对象
        """
        # 先定义变量存储解析结果
        parsed_type = None
        parsed_position = None
        parse_errors = []

        # 解析 clothing_type
        clothing_match = re.search(
            r'<clothing_type>\s*(.*?)\s*</clothing_type>', response, re.DOTALL)
        if clothing_match:
            parsed_type = clothing_match.group(1).strip()
        else:
            parse_errors.append("未找到 clothing_type 标签")

        # 解析 person_position
        position_match = re.search(
            r'<person_position>\s*(.*?)\s*</person_position>', response,
            re.DOTALL)
        if position_match:
            parsed_position = position_match.group(1).strip()
        else:
            parse_errors.append("未找到 person_position 标签")

        # 创建结果对象，如果解析失败则使用默认值
        result = VLModelParsedResult(
            type=parsed_type if parsed_type else "未知",
            person_position=parsed_position if parsed_position else "未知",
            parse_errors=parse_errors)

        return result

    async def run(
        self,
        clothing_img_path: str,
        person_img_path: str,
        clothing_type: Optional[str] = None,
        person_position: Optional[str] = None,
        vl_model_name: str = "qwen3-vl-plus",
        img_gen_model_name: str = "wan2.6-image",
        status_callback: Optional[StatusCallback] = None,
    ) -> Dict[str, Any]:
        """运行服装试穿Pipeline

        pipline流程：
            1. 用户输入服装图和人物图
            2. 如果启用VL模型，则先调用VL模型，提取服装类型、穿着位置
               如果不启用VL模型，则服装类型、穿着位置都默认为None
            3. 调用试穿图像生成模型

        Args:
            clothing_img_path (str): 服装图像路径
            person_img_path (str): 人物图像路径
            clothing_type (Optional[str], optional): 服装类型（例如：上衣、裤子、鞋子等）。
                如果提供，则直接使用；如果不提供且启用VL模型，则使用VL模型识别的结果。默认值为 None
            person_position (Optional[str], optional): 服装的人物穿着位置（例如：上身、下身、脚上等）。
                如果提供，则直接使用；如果不提供且启用VL模型，则使用VL模型识别的结果。默认值为 None
            vl_model_name (str, optional): VL模型名称。默认为 "qwen3-vl-plus"
            img_gen_model_name (str, optional): 生成模型名称。默认为 "wan2.6-image"
            status_callback (Optional[StatusCallback], optional): 状态回调函数，用于通知调用方当前执行状态。
                回调函数签名: async def callback(status: str, progress: int) -> None
                - status: 当前状态描述文本
                - progress: 当前进度百分比 (0-100)
                默认值为 None（不进行状态回调）

        Returns:
            Dict[str, Any]: 生成的试穿效果图结果，包含生成图像的URL或路径等信息

        Raises:
            FileNotFoundError: 当输入的图像文件不存在时
            ValueError: 当图像尺寸不符合要求或 VL 模型响应解析失败时
            RuntimeError: 当图像生成失败时
            TimeoutError: 当任务执行超时时

        Note:
            - 如果启用VL模型（use_vl_model=True），会自动分析服装图像
            - VL模型分析可能产生解析错误，这些错误会被记录到日志中
        """
        # 验证输入文件是否存在
        if not Path(clothing_img_path).exists():
            raise FileNotFoundError(f"服装图像文件不存在: {clothing_img_path}")
        if not Path(person_img_path).exists():
            raise FileNotFoundError(f"人物图像文件不存在: {person_img_path}")

        # 保存用户传入的参数（如果有的话，优先使用用户指定的值）
        user_clothing_type = clothing_type
        user_person_position = person_position

        if self.use_vl_model:
            # 如果启用VL模型，则先调用VL模型提取信息
            vl_parsed_result = await self._call_vl_model(
                img_path=clothing_img_path,
                vl_model_name=vl_model_name,
                status_callback=status_callback)

            # 使用VL模型提取的信息（如果用户没有手动指定，则使用VL模型识别的结果）
            clothing_type = user_clothing_type if user_clothing_type else vl_parsed_result.type
            person_position = user_person_position if user_person_position else vl_parsed_result.person_position

            # 记录解析错误信息
            if len(vl_parsed_result.parse_errors) > 0:
                logging.warning(
                    f"解析过程中存在如下错误，可能会导致解析精度出现下降: {vl_parsed_result.parse_errors}"
                )
            # 打印解析结果
            logging.info(
                f"VL模型解析完成！解析结果为：服装类型: {clothing_type}，佩戴位置: {person_position}"
            )
        else:
            # 不使用VL模型时，直接使用用户传入的参数
            clothing_type = user_clothing_type
            person_position = user_person_position

        # 结合VL模型解析结果（如有）和用户输入，调用试戴图像生成模型
        # 通过回调通知调用方：图像生成开始
        if status_callback:
            await status_callback("试穿图像生成中...", 50)

        logging.info(
            f"正在调用试穿图像生成模型...\n服装类型: {clothing_type}\n穿着位置: {person_position}")
        try:
            result = await self.img_generator.generate_try_on_img(
                clothing_img_path=clothing_img_path,
                person_img_path=person_img_path,
                clothing_type=clothing_type,
                person_position=person_position,
                model=img_gen_model_name,
            )
        except Exception as e:
            logging.error(f"调用试穿图像生成模型失败: {e}")
            raise e

        # 在结果中添加VL模型识别的信息，便于后端使用
        result["clothing_type"] = clothing_type
        result["person_position"] = person_position

        return result
