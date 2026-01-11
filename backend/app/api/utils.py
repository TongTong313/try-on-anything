# -*- coding: utf-8 -*-
"""
API层通用工具函数
"""
import uuid
from pathlib import Path
from typing import Optional
from io import BytesIO
from PIL import Image
from fastapi import UploadFile, HTTPException

from ..config import Config

config = Config()


def validate_file(file: UploadFile) -> None:
    """验证上传文件格式

    Args:
        file: 上传的文件对象

    Raises:
        HTTPException: 文件格式不支持时抛出400错误
    """
    ext = Path(file.filename).suffix.lower()
    if ext not in config.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式: {ext}，支持的格式: {config.ALLOWED_EXTENSIONS}"
        )


async def validate_file_size(content: bytes, filename: str) -> None:
    """验证文件内容是否为有效图片，并检查文件大小

    Args:
        content: 文件内容字节
        filename: 文件名（用于错误提示）

    Raises:
        HTTPException: 文件过大或不是有效图片时抛出错误
    """
    # 检查文件大小
    if len(content) > config.MAX_FILE_SIZE:
        max_size_mb = config.MAX_FILE_SIZE / (1024 * 1024)
        raise HTTPException(
            status_code=413,
            detail=f"文件 {filename} 过大，最大允许 {max_size_mb:.0f}MB"
        )

    # 验证文件内容是否为有效图片
    try:
        img = Image.open(BytesIO(content))
        img.verify()
    except Exception:
        raise HTTPException(
            status_code=400,
            detail=f"文件 {filename} 不是有效的图片文件"
        )


def generate_filename(original_filename: str) -> str:
    """生成唯一文件名

    Args:
        original_filename: 原始文件名

    Returns:
        唯一文件名（UUID + 原始扩展名）
    """
    ext = Path(original_filename).suffix.lower()
    return f"{uuid.uuid4()}{ext}"


def find_existing_images(task_dir: Path, count: int = 2) -> list:
    """从任务文件夹中查找已有的图片文件

    Args:
        task_dir: 任务文件夹路径
        count: 需要查找的图片数量

    Returns:
        图片路径列表，如果找不到则对应位置为None
    """
    if not task_dir or not task_dir.exists():
        return [None] * count

    # 获取所有图片文件
    image_extensions = {'.jpg', '.jpeg', '.png', '.webp'}
    image_files = []

    for file in task_dir.iterdir():
        if file.is_file() and file.suffix.lower() in image_extensions:
            # 排除结果图片
            if 'result' not in file.name.lower() and 'output' not in file.name.lower():
                image_files.append(file)

    # 按修改时间排序
    image_files.sort(key=lambda f: f.stat().st_mtime)

    # 返回指定数量的图片路径
    result = []
    for i in range(count):
        result.append(image_files[i] if i < len(image_files) else None)

    return result
