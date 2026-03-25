"""
重启番茄小说 App。
支持显式 --serial 参数，也可通过 ANDROID_SERIAL 环境变量隐式指定设备。
无论 App 是否已启动，均执行强制停止后重新启动。
"""
import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.device import DeviceManager
from core.logger import setup_logger
from core.wait_utils import wait_for_app_ready

PACKAGE_NAME = "com.dragon.read"
MAIN_ACTIVITY = "com.dragon.read.pages.main.MainFragmentActivity"
LAUNCH_WAIT_SECONDS = 300   # 等待 App 完成启动的秒数


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="重启番茄小说 App")
    parser.add_argument(
        "--serial", "-s",
        type=str,
        default=None,
        help="ADB 设备序号，省略时优先读取 ANDROID_SERIAL 环境变量，否则自动检测",
    )
    parser.add_argument(
        "--wait", "-w",
        type=int,
        default=LAUNCH_WAIT_SECONDS,
        help=f"重启后等待 App 就绪的秒数（默认 {LAUNCH_WAIT_SECONDS}）",
    )
    return parser.parse_args()


def restart_app(serial: str | None = None, wait: int = LAUNCH_WAIT_SECONDS) -> bool:
    """
    重启番茄小说。
    可独立调用也可被其他模块 import 使用。

    Args:
        serial: ADB 设备序号，None 时依赖环境变量或自动检测。
        wait:   重启后等待秒数。

    Returns:
        True 表示成功，False 表示失败。
    """
    logger = setup_logger("restart_fqnovel")
    logger.info("=" * 50)
    logger.info("重启番茄小说 App")
    logger.info("=" * 50)

    # ── 连接设备 ──
    device_mgr = DeviceManager(serial=serial)
    if not device_mgr.connect():
        logger.error("设备连接失败，无法重启 App")
        return False
    logger.info("✓ 设备已连接: %s", device_mgr.serial)

    # ── 连接 uiautomator2 ──
    try:
        import uiautomator2 as u2
    except ImportError:
        logger.error("uiautomator2 未安装，请运行: pip install uiautomator2")
        return False

    try:
        device = u2.connect(device_mgr.serial)
    except Exception as e:
        logger.error("uiautomator2 连接失败: %s", e)
        return False

    # ── 强制停止 ──
    logger.info("正在强制停止 %s …", PACKAGE_NAME)
    try:
        device.app_stop(PACKAGE_NAME)
        time.sleep(1)
        logger.info("✓ App 已停止")
    except Exception as e:
        logger.warning("停止 App 时出错（忽略）: %s", e)

    # ── 启动 ──
    logger.info("正在启动 %s …", PACKAGE_NAME)
    try:
        device.app_start(PACKAGE_NAME, stop=False)
    except Exception as e:
        logger.error("启动 App 失败: %s", e)
        return False

    # ── 等待主界面就绪（基于 UI 检测，而非固定秒数）──
    logger.info("等待 App 主界面就绪（最多 %d 秒）…", wait)
    ready = wait_for_app_ready(device, timeout=wait)
    if ready:
        try:
            current = device.app_current()
            logger.info("✓ 番茄小说主界面已就绪: %s", (current or {}).get("activity", ""))
        except Exception:
            logger.info("✓ 番茄小说主界面已就绪")
        return True
    else:
        logger.warning("等待主界面超时（%d 秒），App 可能仍在加载", wait)
        return False


if __name__ == "__main__":
    args = parse_args()
    success = restart_app(serial=args.serial, wait=args.wait)
    sys.exit(0 if success else 1)
