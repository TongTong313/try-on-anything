# -*- coding: utf-8 -*-
"""
FastAPI 应用主入口
随心穿戴后端服务
"""
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import Config
from .api.tryon import router as tryon_router
from .services.task_manager import task_manager

# 配置全局日志格式，统一算法模块的日志输出风格
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s'  # 保留日志级别信息
)

# 声明配置实例
config = Config()


async def cleanup_task():
    """定时清理过期任务和文件夹"""
    while True:
        await asyncio.sleep(3600)  # 每小时执行一次
        cleaned = await task_manager.cleanup_old_tasks()
        if cleaned > 0:
            print(f"已清理 {cleaned} 个过期任务")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时：创建清理任务
    cleanup_task_handle = asyncio.create_task(cleanup_task())
    yield
    # 关闭时：取消清理任务
    cleanup_task_handle.cancel()
    try:
        await cleanup_task_handle
    except asyncio.CancelledError:
        pass


# 创建FastAPI应用实例
app = FastAPI(
    title="随心穿戴API",
    description="基于AI的随心穿戴服务，v1.0.0版本支持饰品虚拟试戴，自动识别饰品类型和佩戴位置",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# 配置CORS中间件，允许前端跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载任务文件夹目录（每个任务一个子文件夹，包含uploads和results）
app.mount(
    "/api/tasks",
    StaticFiles(directory=str(config.TASKS_DIR)),
    name="tasks"
)

# 注册API路由
app.include_router(tryon_router, prefix="/api")


@app.get("/")
async def root():
    """根路径，返回API信息"""
    return {
        "name": "随心穿戴API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "healthy"}
