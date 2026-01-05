# -*- coding: utf-8 -*-
"""
试戴相关API路由
"""
import uuid
import aiofiles
import httpx
from pathlib import Path
from typing import Optional
import logging
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Header
from pydantic import BaseModel

from ..config import Config
from ..schemas import (
    TaskStatus,
    TryOnSubmitResponse,
    TaskStatusResponse,
    TryOnResultResponse,
    TaskDeleteResponse,
)
from ..services import task_manager, tryon_service
from io import BytesIO
from PIL import Image

router = APIRouter(prefix="/tryon", tags=["试戴"])

# 声明配置实例
config = Config()


def _validate_file(file: UploadFile) -> None:
    """验证上传文件

    Args:
        file (UploadFile): 上传的文件
    """
    # 检查文件扩展名
    ext = Path(file.filename).suffix.lower()
    if ext not in config.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式: {ext}，支持的格式: {config.ALLOWED_EXTENSIONS}")


async def _validate_file_size(content: bytes, filename: str) -> None:
    """验证文件内容是否为有效图片，并检查文件大小

    Args:
        content (bytes): 文件内容
        filename (str): 文件名（用于错误提示）
    """
    # 检查文件大小
    if len(content) > config.MAX_FILE_SIZE:
        max_size_mb = config.MAX_FILE_SIZE / (1024 * 1024)
        raise HTTPException(
            status_code=413,
            detail=f"文件 {filename} 过大，最大允许 {max_size_mb:.0f}MB")

    # 验证文件内容是否为有效图片
    try:
        img = Image.open(BytesIO(content))
        img.verify()  # 验证图片完整性
    except Exception:
        raise HTTPException(status_code=400, detail=f"文件 {filename} 不是有效的图片文件")


def _generate_filename(original_filename: str) -> str:
    """生成唯一文件名：通过uuid4生成唯一文件名，并保留原始文件扩展名

    Args:
        original_filename (str): 原始文件名
    Returns:
        str: 唯一文件名
    """
    ext = Path(original_filename).suffix.lower()
    return f"{uuid.uuid4()}{ext}"


def _find_existing_images(task_dir: Path) -> tuple:
    """从任务文件夹中查找已有的图片文件

    根据文件命名规则，任务文件夹中的图片按创建顺序排列：
    - 第一个图片是饰品图片（accessory）
    - 第二个图片是人物图片（person）
    - 结果图片通常包含 'result' 或在子目录中

    Args:
        task_dir (Path): 任务文件夹路径
    Returns:
        tuple: (accessory_path, person_path) 如果找到则返回路径，否则返回 None
    """
    if not task_dir or not task_dir.exists():
        return None, None

    # 获取所有图片文件，按修改时间排序
    image_extensions = {'.jpg', '.jpeg', '.png', '.webp'}
    image_files = []

    for file in task_dir.iterdir():
        if file.is_file() and file.suffix.lower() in image_extensions:
            # 排除结果图片（通常文件名包含 result 或 output）
            if 'result' not in file.name.lower(
            ) and 'output' not in file.name.lower():
                image_files.append(file)

    # 按修改时间排序（最早的在前）
    image_files.sort(key=lambda f: f.stat().st_mtime)

    accessory_path = image_files[0] if len(image_files) > 0 else None
    person_path = image_files[1] if len(image_files) > 1 else None

    return accessory_path, person_path


@router.post("/submit", response_model=TryOnSubmitResponse)
async def submit_tryon_task(
    accessory_image: UploadFile = File(..., description="饰品图片"),
    person_image: UploadFile = File(..., description="人物图片"),
    accessory_detail_image: Optional[UploadFile] = File(
        None, description="饰品细节图（可选）"),
    accessory_type: Optional[str] = Form(None, description="饰品类型，如'项链'、'手表'"),
    person_position: Optional[str] = Form(None, description="佩戴位置，如'脖子'、'手腕'"),
    use_vl_model: bool = Form(True, description="是否使用VL模型自动识别"),
    vl_model: str = Form("qwen3-vl-plus", description="VL模型名称"),
    img_gen_model: str = Form("wan2.6-image", description="图像生成模型名称"),
    vl_model_api_key: Optional[str] = Header(None,
                                             alias="X-VL-API-Key",
                                             description="VL模型API Key"),
    img_gen_model_api_key: Optional[str] = Header(None,
                                                  alias="X-Image-API-Key",
                                                  description="图像生成模型API Key"),
):
    """
    提交试穿任务

    上传饰品图片和人物图片，可选上传饰品细节图。返回任务提交响应，包括任务ID和删除任务ID。

    Args:
        accessory_image (UploadFile): 饰品图片
        person_image (UploadFile): 人物图片
        accessory_detail_image (UploadFile, optional): 饰品细节图，默认值为 None
        accessory_type (str, optional): 饰品类型，如'项链'、'手表'
        person_position (str, optional): 佩戴位置，如'脖子'、'手腕'
        use_vl_model (bool, optional): 是否使用VL模型自动识别
        vl_model (str, optional): VL模型名称
        img_gen_model (str, optional): 图像生成模型名称
        vl_model_api_key (str, optional): VL模型API Key
        img_gen_model_api_key (str, optional): 图像生成模型API Key

    Returns:
        TryOnSubmitResponse: 任务提交响应
    """
    # 验证文件
    _validate_file(accessory_image)
    _validate_file(person_image)
    if accessory_detail_image:
        _validate_file(accessory_detail_image)

    # 创建任务（如果超出上限会自动删除最早的任务）
    task_info, deleted_task_id = await task_manager.create_task()

    # 保存上传的文件到任务文件夹
    accessory_filename = _generate_filename(accessory_image.filename)
    person_filename = _generate_filename(person_image.filename)

    accessory_path = task_info.task_dir / accessory_filename
    person_path = task_info.task_dir / person_filename

    # 读取并验证饰品图片是否超过大小限制
    accessory_content = await accessory_image.read()
    await _validate_file_size(accessory_content, accessory_image.filename)
    async with aiofiles.open(accessory_path, "wb") as f:
        await f.write(accessory_content)

    # 读取并验证人物图片
    person_content = await person_image.read()
    await _validate_file_size(person_content, person_image.filename)
    async with aiofiles.open(person_path, "wb") as f:
        await f.write(person_content)

    # 处理可选的细节图
    detail_path = None
    if accessory_detail_image:
        detail_filename = _generate_filename(accessory_detail_image.filename)
        detail_path = task_info.task_dir / detail_filename
        detail_content = await accessory_detail_image.read()
        await _validate_file_size(detail_content,
                                  accessory_detail_image.filename)
        async with aiofiles.open(detail_path, "wb") as f:
            await f.write(detail_content)

    # 启动异步任务
    tryon_service.start_task(
        task_info=task_info,
        accessory_image_path=str(accessory_path),
        person_image_path=str(person_path),
        accessory_detail_image_path=str(detail_path) if detail_path else None,
        accessory_type=accessory_type,
        person_position=person_position,
        use_vl_model=use_vl_model,
        vl_model_api_key=vl_model_api_key,
        img_gen_model_api_key=img_gen_model_api_key,
        vl_model=vl_model,
        img_gen_model=img_gen_model,
    )

    return TryOnSubmitResponse(task_id=task_info.task_id,
                               message="任务已提交，请使用task_id查询状态",
                               deleted_task_id=deleted_task_id)


@router.get("/status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """
    查询任务状态

    根据任务ID查询当前处理状态和进度。

    Args:
        task_id (str): 任务ID
    """
    task_info = await task_manager.get_task(task_id)
    if not task_info:
        raise HTTPException(status_code=404, detail="任务不存在")

    return TaskStatusResponse(
        task_id=task_info.task_id,
        status=task_info.status,
        message=task_info.message,
        progress=task_info.progress,
    )


@router.get("/result/{task_id}", response_model=TryOnResultResponse)
async def get_task_result(task_id: str):
    """
    获取任务结果

    根据任务ID获取试穿结果，包括生成的效果图URL。

    Args:
        task_id (str): 任务ID
    """
    task_info = await task_manager.get_task(task_id)
    if not task_info:
        logging.error(f"任务 {task_id} 不存在，无法获取结果")
        raise HTTPException(status_code=404, detail="任务不存在")

    # 构建响应
    response = TryOnResultResponse(
        task_id=task_info.task_id,
        status=task_info.status,
        accessory_type=task_info.accessory_type,
        person_position=task_info.person_position,
    )

    # 添加原图URL（使用任务文件夹路径）
    if task_info.accessory_image_path:
        filename = Path(task_info.accessory_image_path).name
        response.accessory_image_url = f"/api/tasks/{task_id}/{filename}"

    if task_info.person_image_path:
        filename = Path(task_info.person_image_path).name
        response.person_image_url = f"/api/tasks/{task_id}/{filename}"

    # 如果任务完成，添加结果图URL
    if task_info.status == TaskStatus.COMPLETED and task_info.result:
        # 从结果中提取下载的图片路径
        downloaded_images = task_info.result.get("downloaded_images", [])
        if downloaded_images:
            result_filename = Path(downloaded_images[0]).name
            response.result_image_url = f"/api/tasks/{task_id}/{result_filename}"

    # 如果任务失败，添加错误信息
    if task_info.status == TaskStatus.FAILED:
        response.error_message = task_info.error_message

    return response


@router.delete("/task/{task_id}", response_model=TaskDeleteResponse)
async def delete_task(task_id: str):
    """
    删除任务

    根据任务ID删除任务及其相关文件。

    Args:
        task_id (str): 任务ID
    Returns:
        TaskDeleteResponse: 任务删除响应
    """
    success = await task_manager.delete_task(task_id)
    if success:
        return TaskDeleteResponse(task_id=task_id,
                                  success=True,
                                  message="任务已删除")
    else:
        raise HTTPException(status_code=404, detail="任务不存在")


@router.put("/resubmit/{task_id}", response_model=TryOnSubmitResponse)
async def resubmit_tryon_task(
    task_id: str,
    accessory_image: Optional[UploadFile] = File(
        None, description="饰品图片（可选，不传则使用原有图片）"),
    person_image: Optional[UploadFile] = File(
        None, description="人物图片（可选，不传则使用原有图片）"),
    accessory_detail_image: Optional[UploadFile] = File(
        None, description="饰品细节图（可选）"),
    accessory_type: Optional[str] = Form(None, description="饰品类型，如'项链'、'手表'"),
    person_position: Optional[str] = Form(None, description="佩戴位置，如'脖子'、'手腕'"),
    use_vl_model: bool = Form(True, description="是否使用VL模型自动识别"),
    vl_model: str = Form("qwen3-vl-plus", description="VL模型名称"),
    img_gen_model: str = Form("wan2.6-image", description="图像生成模型名称"),
    vl_model_api_key: Optional[str] = Header(None,
                                             alias="X-VL-API-Key",
                                             description="VL模型API Key"),
    img_gen_model_api_key: Optional[str] = Header(None,
                                                  alias="X-Image-API-Key",
                                                  description="图像生成模型API Key"),
):
    """
    重新提交试穿任务

    在现有任务上重新执行，支持两种模式：
    1. 上传新图片：使用新上传的图片执行
    2. 不上传图片：使用任务文件夹中已有的图片重新执行

    Args:
        task_id (str): 要重新提交的任务ID
        accessory_image (UploadFile, optional): 饰品图片，不传则使用原有图片
        person_image (UploadFile, optional): 人物图片，不传则使用原有图片
        其他参数同 submit_tryon_task
        accessory_detail_image (UploadFile, optional): 饰品细节图（可选）
        accessory_type (str, optional): 饰品类型，如'项链'、'手表'
        person_position (str, optional): 佩戴位置，如'脖子'、'手腕'
        use_vl_model (bool, optional): 是否使用VL模型自动识别
        vl_model (str, optional): VL模型名称
        img_gen_model (str, optional): 图像生成模型名称
        vl_model_api_key (str, optional): VL模型API Key
        img_gen_model_api_key (str, optional): 图像生成模型API Key

    Returns:
        TryOnSubmitResponse: 任务提交响应（使用原有task_id）
    """
    # 验证上传的文件（如果有）
    if accessory_image:
        _validate_file(accessory_image)
    if person_image:
        _validate_file(person_image)
    if accessory_detail_image:
        _validate_file(accessory_detail_image)

    # 检查任务文件夹是否存在
    task_dir = config.TASKS_DIR / task_id
    if not task_dir.exists():
        raise HTTPException(status_code=404, detail="任务不存在，无法重新提交")

    # 获取或创建任务信息
    task_info = await task_manager.get_task(task_id)
    if task_info:
        # 任务存在，重置状态
        task_info = await task_manager.reset_task(task_id)
    else:
        # 任务不存在（后端重启过），使用原有task_id创建新任务
        task_info = await task_manager.create_task_with_id(task_id)

    # 查找已有的图片文件
    existing_accessory_path, existing_person_path = _find_existing_images(
        task_dir)

    # 确定最终使用的图片路径
    accessory_path = None
    person_path = None

    # 处理饰品图片
    if accessory_image:
        # 上传了新图片，保存新文件
        accessory_filename = _generate_filename(accessory_image.filename)
        accessory_path = task_info.task_dir / accessory_filename
        accessory_content = await accessory_image.read()
        await _validate_file_size(accessory_content, accessory_image.filename)
        async with aiofiles.open(accessory_path, "wb") as f:
            await f.write(accessory_content)
    elif existing_accessory_path:
        # 使用已有图片
        accessory_path = existing_accessory_path
    else:
        raise HTTPException(status_code=400, detail="未找到饰品图片，请上传")

    # 处理人物图片
    if person_image:
        # 上传了新图片，保存新文件
        person_filename = _generate_filename(person_image.filename)
        person_path = task_info.task_dir / person_filename
        person_content = await person_image.read()
        await _validate_file_size(person_content, person_image.filename)
        async with aiofiles.open(person_path, "wb") as f:
            await f.write(person_content)
    elif existing_person_path:
        # 使用已有图片
        person_path = existing_person_path
    else:
        raise HTTPException(status_code=400, detail="未找到人物图片，请上传")

    # 处理可选的细节图
    detail_path = None
    if accessory_detail_image:
        detail_filename = _generate_filename(accessory_detail_image.filename)
        detail_path = task_info.task_dir / detail_filename
        detail_content = await accessory_detail_image.read()
        await _validate_file_size(detail_content,
                                  accessory_detail_image.filename)
        async with aiofiles.open(detail_path, "wb") as f:
            await f.write(detail_content)

    # 启动异步任务
    tryon_service.start_task(
        task_info=task_info,
        accessory_image_path=str(accessory_path),
        person_image_path=str(person_path),
        accessory_detail_image_path=str(detail_path) if detail_path else None,
        accessory_type=accessory_type,
        person_position=person_position,
        use_vl_model=use_vl_model,
        vl_model_api_key=vl_model_api_key,
        img_gen_model_api_key=img_gen_model_api_key,
        vl_model=vl_model,
        img_gen_model=img_gen_model,
    )

    return TryOnSubmitResponse(task_id=task_info.task_id,
                               message="任务已重新提交，请使用task_id查询状态",
                               deleted_task_id=None)


class TestConnectionRequest(BaseModel):
    """测试连接请求体"""
    api_key: str


class TestConnectionResponse(BaseModel):
    """测试连接响应体"""
    success: bool
    message: str


@router.post("/test-connection", response_model=TestConnectionResponse)
async def test_connection(request: TestConnectionRequest):
    """
    测试API Key连接

    使用提供的API Key调用DashScope API验证连接是否正常。
    """
    api_key = request.api_key
    if not api_key or not api_key.strip():
        return TestConnectionResponse(success=False, message="API Key不能为空")

    # 调用DashScope API验证API Key
    # 使用一个简单的模型列表请求来验证
    url = "https://dashscope.aliyuncs.com/compatible-mode/v1/models"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, headers=headers)

            if response.status_code == 200:
                return TestConnectionResponse(success=True, message="连接成功")
            elif response.status_code == 401:
                return TestConnectionResponse(success=False,
                                              message="API Key无效或已过期")
            else:
                return TestConnectionResponse(
                    success=False, message=f"连接失败，状态码: {response.status_code}")
    except httpx.TimeoutException:
        return TestConnectionResponse(success=False, message="连接超时，请检查网络")
    except Exception as e:
        return TestConnectionResponse(success=False, message=f"连接失败: {str(e)}")
