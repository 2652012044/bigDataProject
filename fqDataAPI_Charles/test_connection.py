"""
测试脚本 - 验证设备和 uiautomator2 连接
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.device import DeviceManager
from core.app_controller import AppController
from core.logger import setup_logger


def test_device_connection():
    """测试设备连接"""
    logger = setup_logger("test")
    
    logger.info("=" * 60)
    logger.info("测试设备连接和 uiautomator2")
    logger.info("=" * 60)
    
    # 第一步：连接设备
    logger.info("\n[1] 连接 ADB 设备...")
    device_mgr = DeviceManager()
    
    if not device_mgr.connect():
        logger.error("✗ 设备连接失败")
        return False
    
    logger.info("✓ 设备已连接")
    
    # 第二步：获取设备信息
    logger.info("\n[2] 获取设备信息...")
    info = device_mgr.get_device_info()
    
    for key, value in info.items():
        logger.info(f"  {key}: {value}")
    
    # 第三步：获取屏幕尺寸
    logger.info("\n[3] 获取屏幕尺寸...")
    width, height = device_mgr.get_screen_size()
    logger.info(f"✓ 屏幕分辨率: {width}x{height}")
    
    # 第四步：连接 uiautomator2
    logger.info("\n[4] 连接 uiautomator2...")
    try:
        app = AppController(device_mgr)
        logger.info("✓ uiautomator2 已连接")
    except Exception as e:
        logger.error(f"✗ uiautomator2 连接失败: {e}")
        return False
    
    # 第五步：检查番茄小说 App
    logger.info("\n[5] 检查番茄小说 App...")
    try:
        from uiautomator2 import connect
        d = connect(device_mgr.serial)
        
        # 获取已安装应用列表
        result = d.shell("pm list packages | grep dragon")
        if result:
            logger.info("✓ 番茄小说 App 已安装")
            logger.info(f"  {result.strip()}")
        else:
            logger.warning("✗ 未找到番茄小说 App，请确保已安装")
    except Exception as e:
        logger.error(f"检查 App 失败: {e}")
    
    logger.info("\n" + "=" * 60)
    logger.info("✓ 测试完成！所有连接正常")
    logger.info("=" * 60)
    logger.info("\n下一步: 运行 'python main.py' 开始自动化操作")
    
    return True


if __name__ == "__main__":
    try:
        success = test_device_connection()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n用户中止")
        sys.exit(1)
    except Exception as e:
        print(f"\n测试异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
