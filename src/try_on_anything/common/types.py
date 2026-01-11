from typing import Optional, Dict, Any, List, Callable, Awaitable
from pydantic import BaseModel

# 状态回调函数类型定义
# StatusCallback: 用于通知调用方当前Pipeline执行状态的回调函数
# 参数说明:
#   - status (str): 当前状态描述，如 "VL模型分析图像中..."、"试穿图像生成中..."
#   - progress (int): 当前进度百分比 (0-100)
# 返回值: 无返回值的协程（异步函数）
StatusCallback = Callable[[str, int], Awaitable[None]]


class VLModelParsedResult(BaseModel):
    """VL模型解析结果"""
    type: str  # 服装/饰品类型（必需字段）
    person_position: str  # 服装的人物穿着位置（必需字段）
    parse_errors: List[str] = []  # 解析错误信息


class VLModelAccessoryParsedResult(VLModelParsedResult):
    detail_bbox: Optional[Dict[str, float]] = None  # 饰品细节区域
