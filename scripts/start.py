#!/usr/bin/env python3
"""
开发环境启动脚本
同时启动前后端服务，统一管理进程
"""

import subprocess
import sys
import signal
import os
import time
import logging
import threading
import argparse
from pathlib import Path
from datetime import datetime

# 保存原始代码页（用于退出时恢复）
_original_codepage = None


def setup_windows_encoding():
    """设置 Windows 终端编码为 UTF-8，并保存原始代码页"""
    global _original_codepage
    if sys.platform == 'win32':
        # 获取当前代码页
        try:
            result = subprocess.run(['chcp'],
                                    capture_output=True,
                                    text=True,
                                    shell=True)
            # 输出格式: "Active code page: 936"
            if result.stdout:
                match = result.stdout.strip().split(':')
                if len(match) > 1:
                    _original_codepage = match[1].strip()
        except Exception:
            _original_codepage = None

        # 设置控制台输出编码为UTF-8
        os.system('chcp 65001 > nul 2>&1')
        # 设置标准输出编码
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')


def restore_windows_encoding():
    """恢复 Windows 终端原始代码页"""
    global _original_codepage
    if sys.platform == 'win32' and _original_codepage:
        try:
            os.system(f'chcp {_original_codepage} > nul 2>&1')
        except Exception:
            pass


# ANSI 颜色代码
class Colors:
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


class ColoredFormatter(logging.Formatter):
    """带颜色的日志格式化器"""

    # 不同日志级别对应的颜色
    LEVEL_COLORS = {
        'DEBUG': Colors.CYAN,
        'INFO': Colors.GREEN,
        'WARNING': Colors.YELLOW,
        'ERROR': Colors.RED,
        'CRITICAL': Colors.RED + Colors.BOLD,
    }

    # 不同服务的颜色
    SERVICE_COLORS = {
        '后端': Colors.BLUE,
        '前端': Colors.GREEN,
        '系统': Colors.MAGENTA,
    }

    def format(self, record):
        # 为日志级别添加颜色
        levelname = record.levelname
        if levelname in self.LEVEL_COLORS:
            record.levelname = f"{self.LEVEL_COLORS[levelname]}{levelname}{Colors.RESET}"

        # 为服务名称添加颜色
        if hasattr(record, 'service'):
            service = record.service
            if service in self.SERVICE_COLORS:
                record.service = f"{self.SERVICE_COLORS[service]}{service}{Colors.RESET}"

        # 格式化消息
        result = super().format(record)
        return result


def setup_logging():
    """配置日志系统"""
    # 创建 logs 目录
    log_dir = Path(__file__).parent.parent / 'logs'
    log_dir.mkdir(exist_ok=True)

    # 生成日志文件名（按日期）
    log_file = log_dir / f"dev_{datetime.now().strftime('%Y%m%d')}.log"

    # 创建根 logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # 控制台处理器（带颜色）
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = ColoredFormatter(
        fmt='%(asctime)s [%(levelname)s] %(service)s - %(message)s',
        datefmt='%H:%M:%S')
    console_handler.setFormatter(console_formatter)

    # 文件处理器（不带颜色）
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        fmt='%(asctime)s [%(levelname)s] %(service)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S')
    file_handler.setFormatter(file_formatter)

    # 添加处理器
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    return root_logger


def get_logger(service_name):
    """获取指定服务的 logger"""
    logger = logging.getLogger(service_name)

    # 使用适配器添加服务名称
    class ServiceAdapter(logging.LoggerAdapter):

        def process(self, msg, kwargs):
            # 在 extra 中添加 service 字段
            if 'extra' not in kwargs:
                kwargs['extra'] = {}
            kwargs['extra']['service'] = self.extra['service']
            return msg, kwargs

    return ServiceAdapter(logger, {'service': service_name})


def check_dependencies(logger):
    """检查必要的依赖是否存在"""
    errors = []

    logger.info("开始检查依赖...")

    # 检查 uv 是否安装
    try:
        result = subprocess.run(['uv', '--version'],
                                capture_output=True,
                                check=True,
                                text=True)
        logger.debug(f"uv 版本: {result.stdout.strip()}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        errors.append("uv 未安装或不在 PATH 中，请先安装uv")

    # 检查 npm 是否安装
    try:
        result = subprocess.run(['npm', '--version'],
                                capture_output=True,
                                check=True,
                                text=True,
                                shell=True)
        logger.debug(f"npm 版本: {result.stdout.strip()}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        errors.append("npm 未安装或不在 PATH 中，请先安装 Node.js")

    # 检查前端目录是否存在
    project_root = Path(__file__).parent.parent
    frontend_dir = project_root / 'frontend'
    if not frontend_dir.exists():
        errors.append(f"前端目录不存在: {frontend_dir}")

    # 检查前端 node_modules 是否存在
    if frontend_dir.exists():
        node_modules = frontend_dir / 'node_modules'
        if not node_modules.exists():
            logger.warning("检测到前端依赖未安装，正在安装...")
            try:
                subprocess.run(['npm', 'install'],
                               cwd=frontend_dir,
                               check=True)
                logger.info("前端依赖安装完成")
            except subprocess.CalledProcessError:
                errors.append("前端依赖安装失败，请手动运行: cd frontend && npm install")

    # 检查环境变量
    if not os.getenv('DASHSCOPE_API_KEY'):
        logger.warning("DASHSCOPE_API_KEY 环境变量未设置")
        logger.warning("请设置后再启动，否则后端服务可能无法正常工作")

    if errors:
        logger.error("检查依赖时发现以下错误:")
        for error in errors:
            logger.error(f"  [X] {error}")
        return False

    logger.info("依赖检查通过 [OK]")
    return True


def read_process_output(name, process, logger):
    """读取进程输出的线程函数，自动解析日志级别"""
    import re
    # 匹配日志级别的正则表达式
    level_pattern = re.compile(r'^\[(\w+)\]\s*(.*)$')

    try:
        for line in iter(process.stdout.readline, ''):
            if line:
                # 过滤掉空行和特殊字符
                line = line.rstrip()
                if line:
                    # 尝试解析日志级别
                    match = level_pattern.match(line)
                    if match:
                        level_str = match.group(1).upper()
                        message = match.group(2)
                        # 根据级别选择对应的日志方法
                        if level_str == 'WARNING':
                            logger.warning(message)
                        elif level_str == 'ERROR':
                            logger.error(message)
                        elif level_str == 'DEBUG':
                            logger.debug(message)
                        else:
                            logger.info(message)
                    else:
                        # 没有匹配到级别，默认使用 info
                        logger.info(line)
            if process.poll() is not None:
                break
    except Exception as e:
        logger.error(f"读取输出时发生错误: {e}")


def start_services(logger: logging.Logger,
                   host: str = "0.0.0.0",
                   port: int = 8000):
    """启动前后端服务

    Args:
        logger (logging.Logger): 日志记录器
        host (str): 后端服务监听的主机地址
        port (int): 后端服务监听的端口
    """
    processes = []
    threads = []
    project_root = Path(__file__).parent.parent

    try:
        # 启动后端服务
        backend_logger = get_logger('后端')
        backend_logger.info("正在启动后端服务...")

        # 获取虚拟环境中的Python路径
        if sys.platform == 'win32':
            python_path = project_root / '.venv' / 'Scripts' / 'python.exe'
        else:
            python_path = project_root / '.venv' / 'bin' / 'python'

        backend_cmd = [
            str(python_path), '-m', 'uvicorn', 'backend.app.main:app',
            '--host', host, '--port',
            str(port)
        ]

        backend_process = subprocess.Popen(backend_cmd,
                                           cwd=project_root,
                                           stdout=subprocess.PIPE,
                                           stderr=subprocess.STDOUT,
                                           text=True,
                                           bufsize=1,
                                           encoding='utf-8',
                                           errors='replace')
        processes.append(('后端', backend_process, backend_logger))

        # 启动后端日志读取线程
        backend_thread = threading.Thread(target=read_process_output,
                                          args=('后端', backend_process,
                                                backend_logger),
                                          daemon=True)
        backend_thread.start()
        threads.append(backend_thread)

        # 等待后端启动
        time.sleep(2)

        # 启动前端服务
        frontend_logger = get_logger('前端')
        frontend_logger.info("正在启动前端服务...")

        frontend_dir = project_root / 'frontend'
        frontend_cmd = ['npm', 'run', 'dev']

        frontend_process = subprocess.Popen(frontend_cmd,
                                            cwd=frontend_dir,
                                            stdout=subprocess.PIPE,
                                            stderr=subprocess.STDOUT,
                                            text=True,
                                            bufsize=1,
                                            encoding='utf-8',
                                            errors='replace',
                                            shell=True)
        processes.append(('前端', frontend_process, frontend_logger))

        # 启动前端日志读取线程
        frontend_thread = threading.Thread(target=read_process_output,
                                           args=('前端', frontend_process,
                                                 frontend_logger),
                                           daemon=True)
        frontend_thread.start()
        threads.append(frontend_thread)

        # 显示启动信息
        logger.info("=" * 60)
        logger.info("[OK] 服务启动成功！")
        # 如果host是0.0.0.0，显示为localhost更友好
        display_host = "localhost" if host == "0.0.0.0" else host
        logger.info(
            f"{Colors.BLUE}  后端地址: http://{display_host}:{port}{Colors.RESET}")
        logger.info(
            f"{Colors.BLUE}  API 文档: http://{display_host}:{port}/docs{Colors.RESET}"
        )
        logger.info(
            f"{Colors.GREEN}  前端地址: http://localhost:5173{Colors.RESET}")
        logger.info("=" * 60)
        logger.info("按 Ctrl+C 可同时停止所有服务")
        logger.info("")

        # 监控进程状态
        while True:
            time.sleep(1)

            # 检查是否有进程异常退出
            for name, process, proc_logger in processes:
                if process.poll() is not None:
                    proc_logger.error(
                        f"{name}服务异常退出，退出码: {process.returncode}")
                    raise KeyboardInterrupt

    except KeyboardInterrupt:
        logger.info("")
        logger.info("正在停止所有服务...")

    finally:
        # 停止所有进程
        for name, process, proc_logger in processes:
            if process.poll() is None:  # 进程还在运行
                proc_logger.info(f"正在停止{name}服务...")
                process.terminate()
                try:
                    process.wait(timeout=5)
                    proc_logger.info(f"{name}服务已停止")
                except subprocess.TimeoutExpired:
                    proc_logger.warning(f"强制终止{name}服务...")
                    process.kill()
                    proc_logger.info(f"{name}服务已强制终止")

        logger.info("所有服务已停止")


def main():
    """主函数"""
    # 设置 Windows 编码（保存原始代码页）
    setup_windows_encoding()

    try:
        # 解析命令行参数
        parser = argparse.ArgumentParser(
            description='随心穿戴v1.1.0 - 开发环境启动脚本',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog='''
示例:
  # 使用默认配置启动
  python scripts/start.py

  # 自定义后端服务地址和端口
  python scripts/start.py --host 127.0.0.1 --port 8080

  # 仅修改端口
  python scripts/start.py --port 9000
        ''')

        parser.add_argument('--host',
                            type=str,
                            default='0.0.0.0',
                            help='后端服务监听的主机地址 (默认: 0.0.0.0)')

        parser.add_argument('--port',
                            type=int,
                            default=8000,
                            help='后端服务监听的端口 (默认: 8000)')

        args = parser.parse_args()

        # 设置日志系统
        setup_logging()
        system_logger = get_logger('系统')

        system_logger.info("=" * 60)
        system_logger.info("  随心穿戴v1.1.0 - 开发环境启动脚本")
        system_logger.info("=" * 60)
        system_logger.info("")

        # 检查依赖
        if not check_dependencies(system_logger):
            sys.exit(1)

        system_logger.info("")

        # 启动服务
        start_services(system_logger, host=args.host, port=args.port)

    finally:
        # 恢复原始代码页
        restore_windows_encoding()


if __name__ == '__main__':
    main()
