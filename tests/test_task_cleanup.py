# -*- coding: utf-8 -*-
"""
测试任务自动清理功能

测试思路：
1. 不需要真的等待24小时
2. 通过修改任务的 created_at 时间来模拟任务过期
3. 或者传入很小的 max_age_hours 参数来测试
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta

# 添加项目根目录到 Python 路径
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from backend.app.services.task_manager import TaskManager, TaskInfo
from backend.app.schemas import TaskStatus


def test_cleanup_by_modifying_created_time():
    """
    测试方法1：通过修改任务的 created_at 时间来模拟过期
    模拟任务创建于25小时前，然后调用清理方法
    """
    print("=" * 60)
    print("测试1：通过修改 created_at 时间模拟24小时后过期")
    print("=" * 60)

    # 创建任务管理器实例（使用独立实例避免影响全局）
    manager = TaskManager()

    # 创建3个任务
    task1, _ = manager.create_task()
    task2, _ = manager.create_task()
    task3, _ = manager.create_task()

    print(f"创建了3个任务:")
    print(f"  - 任务1: {task1.task_id}")
    print(f"  - 任务2: {task2.task_id}")
    print(f"  - 任务3: {task3.task_id}")

    # 修改任务1和任务2的创建时间为25小时前（超过24小时阈值）
    old_time = datetime.now() - timedelta(hours=25)
    task1.created_at = old_time
    task2.created_at = old_time
    # task3 保持当前时间，不应该被删除

    print(f"\n修改任务创建时间:")
    print(f"  - 任务1 created_at: {task1.created_at} (25小时前)")
    print(f"  - 任务2 created_at: {task2.created_at} (25小时前)")
    print(f"  - 任务3 created_at: {task3.created_at} (刚创建)")

    # 执行清理（默认清理超过24小时的任务）
    print(f"\n执行清理（max_age_hours=24）...")
    cleaned_count = asyncio.run(manager.cleanup_old_tasks(max_age_hours=24))

    print(f"清理完成，删除了 {cleaned_count} 个任务")

    # 验证结果
    remaining_tasks = list(manager._tasks.keys())
    print(f"\n剩余任务数量: {len(remaining_tasks)}")

    # 检查任务1和任务2是否被删除
    task1_deleted = task1.task_id not in manager._tasks
    task2_deleted = task2.task_id not in manager._tasks
    task3_exists = task3.task_id in manager._tasks

    print(f"\n验证结果:")
    print(f"  - 任务1 (25小时前) 已删除: {task1_deleted} {'[OK]' if task1_deleted else '[FAIL]'}")
    print(f"  - 任务2 (25小时前) 已删除: {task2_deleted} {'[OK]' if task2_deleted else '[FAIL]'}")
    print(f"  - 任务3 (刚创建) 仍存在: {task3_exists} {'[OK]' if task3_exists else '[FAIL]'}")

    # 清理测试创建的文件夹
    if task3.task_id in manager._tasks:
        manager.delete_task(task3.task_id)

    success = task1_deleted and task2_deleted and task3_exists
    print(f"\n测试1 {'通过 [OK]' if success else '失败 [FAIL]'}")
    return success


def test_cleanup_with_small_max_age():
    """
    测试方法2：传入很小的 max_age_hours 参数
    传入 max_age_hours=0，让所有任务立即过期
    """
    print("\n" + "=" * 60)
    print("测试2：传入 max_age_hours=0 让任务立即过期")
    print("=" * 60)

    manager = TaskManager()

    # 创建2个任务
    task1, _ = manager.create_task()
    task2, _ = manager.create_task()

    print(f"创建了2个任务:")
    print(f"  - 任务1: {task1.task_id}")
    print(f"  - 任务2: {task2.task_id}")
    print(f"当前任务数量: {len(manager._tasks)}")

    # 执行清理，传入 max_age_hours=0，所有任务都应该被删除
    print(f"\n执行清理（max_age_hours=0，即立即过期）...")
    cleaned_count = asyncio.run(manager.cleanup_old_tasks(max_age_hours=0))

    print(f"清理完成，删除了 {cleaned_count} 个任务")
    print(f"剩余任务数量: {len(manager._tasks)}")

    success = cleaned_count == 2 and len(manager._tasks) == 0
    print(f"\n测试2 {'通过 [OK]' if success else '失败 [FAIL]'}")
    return success


def test_cleanup_edge_cases():
    """
    测试方法3：边界情况测试
    测试在24小时边界附近的任务
    注意：清理条件是 > max_age_hours，所以23.9小时不删除，24.1小时删除
    """
    print("\n" + "=" * 60)
    print("测试3：边界情况 - 24小时边界附近的任务")
    print("=" * 60)

    manager = TaskManager()

    # 创建3个任务
    task_23h, _ = manager.create_task()  # 23小时前，不应该被删除
    task_23_9h, _ = manager.create_task()  # 23.9小时前，不应该被删除
    task_24_1h, _ = manager.create_task()  # 24.1小时前，应该被删除

    # 设置不同的创建时间（使用更精确的边界值）
    task_23h.created_at = datetime.now() - timedelta(hours=23)
    task_23_9h.created_at = datetime.now() - timedelta(hours=23, minutes=54)  # 23小时54分，不超过24小时
    task_24_1h.created_at = datetime.now() - timedelta(hours=24, minutes=6)   # 24小时6分，超过24小时

    print(f"创建了3个任务:")
    print(f"  - 任务A (23小时前): {task_23h.task_id[:8]}...")
    print(f"  - 任务B (23小时54分前): {task_23_9h.task_id[:8]}...")
    print(f"  - 任务C (24小时6分前): {task_24_1h.task_id[:8]}...")

    # 执行清理
    print(f"\n执行清理（max_age_hours=24）...")
    cleaned_count = asyncio.run(manager.cleanup_old_tasks(max_age_hours=24))

    print(f"清理完成，删除了 {cleaned_count} 个任务")

    # 验证结果
    task_23h_exists = task_23h.task_id in manager._tasks
    task_23_9h_exists = task_23_9h.task_id in manager._tasks
    task_24_1h_deleted = task_24_1h.task_id not in manager._tasks

    print(f"\n验证结果:")
    print(f"  - 任务A (23小时前) 仍存在: {task_23h_exists} {'[OK]' if task_23h_exists else '[FAIL]'}")
    print(f"  - 任务B (23小时54分前) 仍存在: {task_23_9h_exists} {'[OK]' if task_23_9h_exists else '[FAIL]'}")
    print(f"  - 任务C (24小时6分前) 已删除: {task_24_1h_deleted} {'[OK]' if task_24_1h_deleted else '[FAIL]'}")

    # 清理剩余任务
    for task_id in list(manager._tasks.keys()):
        manager.delete_task(task_id)

    success = task_23h_exists and task_23_9h_exists and task_24_1h_deleted
    print(f"\n测试3 {'通过 [OK]' if success else '失败 [FAIL]'}")
    return success


def test_cleanup_with_task_folder():
    """
    测试方法4：验证任务文件夹也被正确删除
    """
    print("\n" + "=" * 60)
    print("测试4：验证任务文件夹也被正确删除")
    print("=" * 60)

    manager = TaskManager()

    # 创建任务
    task, _ = manager.create_task()
    task_dir = task.task_dir

    print(f"创建任务: {task.task_id}")
    print(f"任务文件夹: {task_dir}")
    print(f"文件夹存在: {task_dir.exists()}")

    # 修改创建时间为25小时前
    task.created_at = datetime.now() - timedelta(hours=25)

    # 执行清理
    print(f"\n执行清理...")
    cleaned_count = asyncio.run(manager.cleanup_old_tasks(max_age_hours=24))

    # 验证文件夹是否被删除
    folder_deleted = not task_dir.exists()
    task_deleted = task.task_id not in manager._tasks

    print(f"\n验证结果:")
    print(f"  - 任务已从内存删除: {task_deleted} {'[OK]' if task_deleted else '[FAIL]'}")
    print(f"  - 任务文件夹已删除: {folder_deleted} {'[OK]' if folder_deleted else '[FAIL]'}")

    success = task_deleted and folder_deleted
    print(f"\n测试4 {'通过 [OK]' if success else '失败 [FAIL]'}")
    return success


if __name__ == "__main__":
    print("任务自动清理功能测试")
    print("=" * 60)
    print("说明：通过修改任务的 created_at 时间来模拟时间流逝，")
    print("      无需真正等待24小时即可测试清理功能。")
    print("=" * 60 + "\n")

    results = []

    # 运行所有测试
    results.append(("测试1: 修改created_at模拟过期", test_cleanup_by_modifying_created_time()))
    results.append(("测试2: max_age_hours=0立即过期", test_cleanup_with_small_max_age()))
    results.append(("测试3: 边界情况测试", test_cleanup_edge_cases()))
    results.append(("测试4: 文件夹删除验证", test_cleanup_with_task_folder()))

    # 打印总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)

    all_passed = True
    for name, passed in results:
        status = "[OK] 通过" if passed else "[FAIL] 失败"
        print(f"  {name}: {status}")
        if not passed:
            all_passed = False

    print("=" * 60)
    if all_passed:
        print("所有测试通过！")
    else:
        print("部分测试失败，请检查代码。")

    sys.exit(0 if all_passed else 1)
