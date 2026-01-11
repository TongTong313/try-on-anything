import mimetypes
import base64
import logging
from pathlib import Path


def encode_image_for_vl(image_path: str) -> str:
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
