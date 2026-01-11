# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

这是一个随心穿戴系统（Try On Anything），使用 AI 技术将各类物品（饰品、衣服等）自然地合成到人物照片上。在 v1.0.0 版本中实现了饰品虚拟试戴功能，在 v1.1.0 版本中新增了服装虚拟试穿功能。系统采用**前后端分离架构**：

- **后端**：Python FastAPI，提供 RESTful API
- **前端**：Vue 3 + Element Plus，提供用户界面
- **核心算法**：使用视觉语言模型(VLM)进行物品和位置检测，使用通义万象(WanX)进行图像生成

## Claude code 智能体执行规则

- 始终使用中文与我交流
- 严格遵循我的指示，在没有让你生成或修改代码文件的时候，你不允许修改文件内容
- 在指明修改部分文件时，请只修改我指定的部分，如果你发现其他需要修改的部分，**必须**先征求我的同意，我同意后方可修改
- 尽量避免生成 markdown、txt、docs 等格式的文档，除非我明确要求生成这些格式的文档
- 在生成代码时，务必包含详尽的**中文注释**方便我理解代码
- 代码要尽可能简练、易读、具备高可用性，拒绝过度设计
- 你的修改有可能就会导致 README.md、CHANGELOG.md、CLAUDE.md 等文档内容过时，请在修改代码后，检查这些文档内容是否需要更新，如果需要，**必须**先征求我的同意后再进行更新
- 执行过程中有任何不清楚的问题，**必须**先和我讨论确认后，方可进行下一步操作

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

- `DASHSCOPE_API_KEY`: 通义千问 VLM 和通义万象图像生成所需的 API 密钥（也可在前端设置页面配置）

## Architecture

### 项目结构

```
try-on-anything/
├── backend/                    # 后端服务 (FastAPI)
│   └── app/
│       ├── main.py            # 应用入口，CORS配置，定时清理
│       ├── config.py          # 配置管理
│       ├── api/               # API路由端点
│       │   ├── accessory_try_on.py  # 饰品试戴API
│       │   └── clothing_try_on.py   # 服装试穿API
│       ├── schemas/           # Pydantic数据模型
│       │   └── common.py      # 通用数据模型
│       └── services/          # 业务逻辑层
│           ├── task_manager.py       # 任务管理器
│           ├── accessory_try_on.py   # 饰品试戴服务
│           └── clothing_try_on.py    # 服装试穿服务
├── src/try_on_anything/       # 核心算法库
│   ├── clients/               # 模型客户端
│   │   ├── wan.py            # 通义万象API客户端
│   │   └── qwen_vl.py        # Qwen VL视觉语言模型客户端
│   ├── common/                # 公共模块
│   │   ├── types.py          # 类型定义
│   │   └── constants.py      # 常量定义
│   ├── generators/            # 生成器
│   │   ├── base.py           # 基础生成器
│   │   ├── accessory_try_on.py  # 饰品试戴图像生成器
│   │   └── clothing_try_on.py   # 服装试穿图像生成器
│   ├── pipelines/             # 处理管道
│   │   ├── base.py           # 基础Pipeline
│   │   ├── accessory_try_on.py  # 饰品试戴Pipeline
│   │   └── clothing_try_on.py   # 服装试穿Pipeline
│   └── utils/                 # 工具函数
│       └── image_utils.py    # 图像处理工具
├── frontend/                   # 前端应用 (Vue 3)
│   └── src/
│       ├── views/             # 页面组件
│       ├── components/        # 可复用组件
│       ├── api/               # API调用接口
│       │   ├── accessory-try-on.js  # 饰品试戴API
│       │   └── clothing-try-on.js   # 服装试穿API
│       └── locales/           # 国际化 (中/英)
├── tests/                      # 测试文件
└── scripts/start.py           # 一键启动脚本
```

### Key Components

**后端 API 端点**:

饰品试戴 API (`backend/app/api/accessory_try_on.py`):
- `POST /api/accessory-try-on/submit` - 提交饰品试戴任务
- `GET /api/accessory-try-on/status/{task_id}` - 查询任务状态
- `GET /api/accessory-try-on/result/{task_id}` - 获取任务结果
- `DELETE /api/accessory-try-on/task/{task_id}` - 删除任务
- `PUT /api/accessory-try-on/resubmit/{task_id}` - 重新提交任务
- `POST /api/accessory-try-on/test-connection` - 测试 API Key 连接

服装试穿 API (`backend/app/api/clothing_try_on.py`):
- `POST /api/clothing-try-on/submit` - 提交服装试穿任务
- `GET /api/clothing-try-on/status/{task_id}` - 查询任务状态
- `GET /api/clothing-try-on/result/{task_id}` - 获取任务结果
- `DELETE /api/clothing-try-on/task/{task_id}` - 删除任务
- `PUT /api/clothing-try-on/resubmit/{task_id}` - 重新提交任务
- `POST /api/clothing-try-on/test-connection` - 测试 API Key 连接

**核心 Pipeline**:

- `AccessoryTryOnPipeline` (`src/try_on_anything/pipelines/accessory_try_on.py`): 饰品试戴处理流程
  - 使用 VL 模型识别饰品类型和佩戴位置
  - 提取饰品细节区域并裁剪
  - 调用通义万象生成试戴效果图

- `ClothingTryOnPipeline` (`src/try_on_anything/pipelines/clothing_try_on.py`): 服装试穿处理流程
  - 使用 VL 模型识别服装类型和穿着位置
  - 调用通义万象生成试穿效果图

**模型客户端**:

- `QwenVLClient`: Qwen VL 视觉语言模型，支持流式输出和思考模式
- `WanModelClient`: 通义万象图像生成 API，支持异步请求

### Image Processing

- 通义万象 API 自动选择标准输出尺寸
- 支持的宽高比：1:1, 2:3, 3:2, 3:4, 4:3, 9:16, 16:9, 21:9
- 支持的图片格式：`.jpg`, `.jpeg`, `.png`, `.webp`
- 最大文件大小：30MB

## 任务管理

后端配置 (`backend/app/config.py`):

- 任务存储目录：`./backend/tasks/`
- 任务超时时间：300 秒
- 任务过期时间：24 小时（自动清理）
- 最大任务数量：20 个（超过自动删除最早的）

## Important Notes

- **无需 GPU**：当前方案使用云端 API，无需本地 GPU 资源
- **异步操作**：VLM 分析和图像生成均使用 async/await 模式
- **中文提示词**：系统主要使用中文提示词以获得更好的效果
- **国际化支持**：前端支持中英文切换
- **任务状态**：pending → processing → completed/failed
