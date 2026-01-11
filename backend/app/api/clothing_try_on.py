# -*- coding: utf-8 -*-
"""
服装试穿相关API路由
"""
from typing import Optional
from fastapi import UploadFile, File, Form, Header, HTTPException
import httpx
from pydantic import BaseModel

from ..schemas import TaskType, TryOnSubmitResponse
from ..services import task_manager, clothing_try_on_service
from ..config import Config
from .base import BaseTryOnRouter
from .utils import find_existing_images

config = Config()


class ClothingTryOnRouter(BaseTryOnRouter):
    """服装试穿API路由"""

    def __init__(self):
        super().__init__(prefix="/clothing-try-on", tags=["服装试穿"])

    @property
    def task_type(self) -> TaskType:
        return TaskType.CLOTHING

    @property
    def service(self):
        return clothing_try_on_service

    async def submit_task(
        self,
        clothing_image: UploadFile = File(..., description="服装图片"),
        person_image: UploadFile = File(..., description="人物图片"),
        clothing_type: Optional[str] = Form(None, description="服装类型"),
        person_position: Optional[str] = Form(None, description="穿着位置"),
        use_vl_model: bool = Form(True, description="是否使用VL模型"),
        vl_model: str = Form("qwen3-vl-plus", description="VL模型名称"),
        img_gen_model: str = Form("wan2.6-image", description="图像生成模型名称"),
        vl_model_api_key: Optional[str] = Header(None, alias="X-VL-API-Key"),
        img_gen_model_api_key: Optional[str] = Header(None, alias="X-Image-API-Key"),
    ):
        """提交服装试穿任务"""
        # 创建任务
        task_info, deleted_task_id = await task_manager.create_task(self.task_type)

        # 处理并保存图片
        images = {
            "clothing": clothing_image,
            "person": person_image
        }
        saved_paths = await self._process_and_save_images(task_info, images)

        # 启动异步任务
        self.service.start_task(
            task_info=task_info,
            clothing_image_path=saved_paths["clothing"],
            person_image_path=saved_paths["person"],
            clothing_type=clothing_type,
            person_position=person_position,
            use_vl_model=use_vl_model,
            vl_model_api_key=vl_model_api_key,
            img_gen_model_api_key=img_gen_model_api_key,
            vl_model=vl_model,
            img_gen_model=img_gen_model,
        )

        return TryOnSubmitResponse(
            task_id=task_info.task_id,
            task_type=self.task_type,
            message="任务已提交，请使用task_id查询状态",
            deleted_task_id=deleted_task_id
        )

    async def resubmit_task(
        self,
        task_id: str,
        clothing_image: Optional[UploadFile] = File(None),
        person_image: Optional[UploadFile] = File(None),
        clothing_type: Optional[str] = Form(None),
        person_position: Optional[str] = Form(None),
        use_vl_model: bool = Form(True),
        vl_model: str = Form("qwen3-vl-plus"),
        img_gen_model: str = Form("wan2.6-image"),
        vl_model_api_key: Optional[str] = Header(None, alias="X-VL-API-Key"),
        img_gen_model_api_key: Optional[str] = Header(None, alias="X-Image-API-Key"),
    ):
        """重新提交服装试穿任务"""
        # 检查任务文件夹
        task_dir = config.TASKS_DIR / task_id
        if not task_dir.exists():
            raise HTTPException(status_code=404, detail="任务不存在，无法重新提交")

        # 获取或创建任务信息
        task_info = await task_manager.get_task(task_id)
        if task_info:
            task_info = await task_manager.reset_task(task_id)
        else:
            task_info = await task_manager.create_task_with_id(task_id, self.task_type)

        # 查找已有图片
        existing = find_existing_images(task_dir, count=2)
        existing_dict = {
            "clothing": existing[0],
            "person": existing[1]
        }

        # 处理并保存图片
        images = {
            "clothing": clothing_image,
            "person": person_image
        }
        saved_paths = await self._process_and_save_images(task_info, images, existing_dict)

        # 验证必需的图片
        if not saved_paths.get("clothing"):
            raise HTTPException(status_code=400, detail="未找到服装图片，请上传")
        if not saved_paths.get("person"):
            raise HTTPException(status_code=400, detail="未找到人物图片，请上传")

        # 启动异步任务
        self.service.start_task(
            task_info=task_info,
            clothing_image_path=saved_paths["clothing"],
            person_image_path=saved_paths["person"],
            clothing_type=clothing_type,
            person_position=person_position,
            use_vl_model=use_vl_model,
            vl_model_api_key=vl_model_api_key,
            img_gen_model_api_key=img_gen_model_api_key,
            vl_model=vl_model,
            img_gen_model=img_gen_model,
        )

        return TryOnSubmitResponse(
            task_id=task_info.task_id,
            task_type=self.task_type,
            message="任务已重新提交，请使用task_id查询状态",
            deleted_task_id=None
        )


# 测试连接相关（保持不变）
class TestConnectionRequest(BaseModel):
    """测试连接请求体"""
    api_key: str


class TestConnectionResponse(BaseModel):
    """测试连接响应体"""
    success: bool
    message: str


# 创建路由实例
clothing_router = ClothingTryOnRouter()
router = clothing_router.router

# 注册 submit 和 resubmit 端点
router.add_api_route(
    "/submit",
    clothing_router.submit_task,
    methods=["POST"],
    response_model=TryOnSubmitResponse
)
router.add_api_route(
    "/resubmit/{task_id}",
    clothing_router.resubmit_task,
    methods=["PUT"],
    response_model=TryOnSubmitResponse
)


@router.post("/test-connection", response_model=TestConnectionResponse)
async def test_connection(request: TestConnectionRequest):
    """测试API Key连接"""
    api_key = request.api_key
    if not api_key or not api_key.strip():
        return TestConnectionResponse(success=False, message="API Key不能为空")

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
                return TestConnectionResponse(success=False, message="API Key无效或已过期")
            else:
                return TestConnectionResponse(
                    success=False,
                    message=f"连接失败，状态码: {response.status_code}"
                )
    except httpx.TimeoutException:
        return TestConnectionResponse(success=False, message="连接超时，请检查网络")
    except Exception as e:
        return TestConnectionResponse(success=False, message=f"连接失败: {str(e)}")
