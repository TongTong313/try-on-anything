# ============ WAN 模型相关常量 ============
# 图像尺寸限制
MIN_IMAGE_SIZE_FOR_WAN = 384  # Wan模型 API 要求的最小图像尺寸
MAX_IMAGE_SIZE_FOR_WAN = 5000  # Wan模型 API 要求的最大图像尺寸

# HTTP 请求超时配置
HTTP_DOWNLOAD_TIMEOUT = 30.0  # 图像下载超时时间（秒）
HTTP_REQUEST_TIMEOUT = 60.0  # API 请求超时时间（秒）

# 任务轮询配置
DEFAULT_POLL_INTERVAL = 5.0  # 默认轮询间隔（秒）
DEFAULT_MAX_WAIT_TIME = 300.0  # 默认最大等待时间（秒）

# ============ VL 模型相关常量 ============
# Token 配置
VL_MODEL_MAX_TOKENS = 1024 * 8  # VL 模型最大输出 token 数
VL_MODEL_THINKING_BUDGET = 1024 * 8  # VL 模型思考预算 token 数

# ============ 图像生成相关常量 ============
# 支持的输出尺寸列表（宽度, 高度）
SUPPORTED_OUTPUT_SIZES = [
    (1280, 1280),  # 1:1
    (800, 1200),  # 2:3
    (1200, 800),  # 3:2
    (960, 1280),  # 3:4
    (1280, 960),  # 4:3
    (720, 1280),  # 9:16
    (1280, 720),  # 16:9
    (1344, 576)  # 21:9
]
