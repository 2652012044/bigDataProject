"""
获取分类列表脚本
"""
import sys
import time
from pathlib import Path

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from core.device import DeviceManager
from core.app_controller import AppController
from core.logger import setup_logger
from core.wait_utils import ui_signature, wait_for_ui_change


def main() -> bool:
    """主入口"""
    logger = setup_logger("get_type_list")

    logger.info("=" * 60)
    logger.info("获取分类列表脚本")
    logger.info("=" * 60)

    logger.info("\n[1] 初始化设备...")
    device_mgr = DeviceManager()
    if not device_mgr.connect():
        logger.error("设备连接失败，退出")
        return False
    logger.info("✓ 设备已连接")

    logger.info("\n[2] 初始化 App 控制器...")
    controller = AppController(device_mgr)

    try:
        logger.info("\n[3] 执行操作...")

        # 操作 1: 点击主页面的分类标签
        logger.info("\n--- 操作 1: 点击主页面分类 ---")
        clicked = False
        before_click_sig = ui_signature(controller.device)

        # 优先用资源ID点击
        if controller.device(resourceId="com.dragon.read:id/ia1").exists(timeout=2):
            controller.device(resourceId="com.dragon.read:id/ia1").click()
            clicked = True
            logger.info("✓ 已点击分类（resourceId）")
        elif controller.device(text="分类").exists(timeout=2):
            controller.device(text="分类").click()
            clicked = True
            logger.info("✓ 已点击分类（text）")
        else:
            # 兜底：使用坐标点击 bounds: [1506,66][1558,96] -> center: (1532,81)
            controller.device.click(1532, 81)
            clicked = True
            logger.info("✓ 已点击分类（坐标兜底）")

        if not clicked:
            logger.error("✗ 点击分类失败")
            return False

        # 操作 2: 等待3秒
        logger.info("\n--- 操作 2: 等待分类页加载 ---")
        if wait_for_ui_change(controller.device, before_click_sig, timeout=10):
            logger.info("✓ 分类页已加载")
        else:
            logger.warning("未检测到明显页面变化，执行短暂兜底等待")
            time.sleep(1)

        # 操作 3: 回退一次
        logger.info("\n--- 操作 3: 回退一次 ---")
        controller.device.press("back")
        logger.info("✓ 已执行回退")

        logger.info("\n✓ 所有操作完成")
        return True

    except Exception as e:
        logger.error(f"执行失败: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
