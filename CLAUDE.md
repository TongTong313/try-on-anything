# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

这是一个随心穿戴系统（Try On Anything），使用AI技术将各类物品（饰品、衣服等）自然地合成到人物照片上。在v1.0.0版本中，首先实现了饰品虚拟试戴功能。系统采用**前后端分离架构**：
- **后端**：Python FastAPI，提供RESTful API
- **前端**：Vue 3 + Element Plus，提供用户界面
- **核心算法**：使用视觉语言模型(VLM)进行饰品和位置检测，使用通义万象(WanX)进行图像生成

## Claude code智能体执行规则

- 请始终使用中文与我交流
- 请严格遵循我的指示，在没有让你生成或修改代码文件的时候，你不允许修改文件内容，**必须**征求我的同意
- 在指明修改部分文件时，请只修改我指定的部分，如果你发现其他需要修改的部分，**必须**先征求我的同意，我同意后方可修改
- 请尽量避免生成markdown、txt、docs等格式的文档，除非我明确要求生成这些格式的文档
- 在生成代码时，请务必包含详尽的中文注释方便我理解代码
- 代码要尽可能简练、易读、具备高可用性，拒绝过度设计
- 你的修改有可能就会导致readme等文档内容过时，请在修改代码后，检查README.md等文档内容是否需要更新，如果需要，请征求我的同意后再进行更新

## Development Commands

### Environment Setup
```bash
# 安装Python依赖 (推荐使用uv)
uv sync

# 安装前端依赖
cd frontend && npm install
```

### Running the Application
```bash
# 一键启动前后端 (推荐)
python scripts/start.py

# 或分别启动
# 后端: uvicorn backend.app.main:app --reload --port 8000
# 前端: cd frontend && npm run dev
```

### Running Tests
```bash
# 测试Pipeline
python tests/test_accessory_try_on_pipeline.py

# 测试VL模型
python tests/test_qwen_vl.py

# 测试生成器
python tests/test_generator.py
```

### Environment Variables
- `DASHSCOPE_API_KEY`: 通义千问VLM和通义万象图像生成所需的API密钥（也可在前端设置页面配置）

## Architecture

### 项目结构

```
try-on-anything/
├── backend/                    # 后端服务 (FastAPI)
│   └── app/
│       ├── main.py            # 应用入口，CORS配置，定时清理
│       ├── config.py          # 配置管理
│       ├── api/tryon.py       # API路由端点
│       ├── schemas/tryon.py   # Pydantic数据模型
│       └── services/          # 业务逻辑层
│           ├── task_manager.py # 任务管理器
│           └── tryon.py       # 试戴服务
├── src/accessory_try_on/      # 核心算法库
│   ├── models/                # 模型客户端
│   │   ├── wan.py            # 通义万象API客户端
│   │   └── qwen_vl.py        # Qwen VL视觉语言模型客户端
│   ├── generators/            # 生成器
│   │   ├── base.py           # 基础生成器
│   │   └── tryon.py          # 试戴图像生成器
│   ├── pipelines/             # 处理管道
│   │   └── accessory_try_on_pipeline.py  # 主Pipeline
│   └── utils/                 # 工具函数
├── frontend/                   # 前端应用 (Vue 3)
│   └── src/
│       ├── views/             # 页面组件
│       ├── components/        # 可复用组件
│       ├── api/tryon.js       # API调用接口
│       └── locales/           # 国际化 (中/英)
├── tests/                      # 测试文件
└── scripts/start.py           # 一键启动脚本
```

### Key Components

**后端API端点** (`backend/app/api/tryon.py`):
- `POST /api/tryon/submit` - 提交试戴任务
- `GET /api/tryon/status/{task_id}` - 查询任务状态
- `GET /api/tryon/result/{task_id}` - 获取任务结果
- `DELETE /api/tryon/task/{task_id}` - 删除任务
- `PUT /api/tryon/resubmit/{task_id}` - 重新提交任务
- `POST /api/tryon/test-connection` - 测试API Key连接

**核心Pipeline** (`src/accessory_try_on/pipelines/accessory_try_on_pipeline.py`):
- `AccessoryTryOnPipeline` 类：完整的试戴处理流程
- 使用VL模型识别饰品类型和佩戴位置
- 调用通义万象生成试戴效果图

**模型客户端**:
- `QwenVLClient`: Qwen VL视觉语言模型，支持流式输出和思考模式
- `WanModelClient`: 通义万象图像生成API，支持异步请求

### Image Processing

- 通义万象API自动选择标准输出尺寸
- 支持的宽高比：1:1, 2:3, 3:2, 3:4, 4:3, 9:16, 16:9, 21:9
- 支持的图片格式：`.jpg`, `.jpeg`, `.png`, `.webp`
- 最大文件大小：30MB

## 任务管理

后端配置 (`backend/app/config.py`):
- 任务存储目录：`./backend/tasks/`
- 任务超时时间：300秒
- 任务过期时间：24小时（自动清理）
- 最大任务数量：20个（超过自动删除最早的）

## Important Notes

- **无需GPU**：当前方案使用云端API，无需本地GPU资源
- **异步操作**：VLM分析和图像生成均使用async/await模式
- **中文提示词**：系统主要使用中文提示词以获得更好的效果
- **国际化支持**：前端支持中英文切换
- **任务状态**：pending → processing → completed/failed
