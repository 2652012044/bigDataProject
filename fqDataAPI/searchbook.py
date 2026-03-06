"""
番茄小说 App 自动化控制主程序
"""
import sys
import json
import argparse
from pathlib import Path
import requests

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from core.device import DeviceManager
from core.app_controller import AppController
from core.logger import setup_logger
from core.wait_utils import ui_signature, wait_for_any_selector, wait_for_ui_change


CHARLES_CLEAR_URL = "http://control.charles/session/clear"
CHARLES_TIMEOUT_SECONDS = 10


def clear_charles_session(logger) -> bool:
    """Clear existing Charles captured sessions before automation starts."""
    try:
        requests.get(CHARLES_CLEAR_URL, timeout=CHARLES_TIMEOUT_SECONDS)
        logger.info("✓ Charles 抓包已清空")
        return True
    except Exception as e:
        logger.warning(f"清空 Charles 抓包失败，继续执行: {e}")
        return False


def main(book_name):
    """主入口
    
    Args:
        book_name: 要搜索的书籍名称
    """
    logger = setup_logger("main")
    
    logger.info("=" * 60)
    logger.info("番茄小说 App 自动化控制程序")
    logger.info("=" * 60)
    logger.info(f"搜索书籍: {book_name}")

    logger.info("\n[0] 清空 Charles 抓包...")
    clear_charles_session(logger)
    
    # 初始化设备
    logger.info("\n[1] 初始化设备...")
    device_mgr = DeviceManager()
    
    if not device_mgr.connect():
        logger.error("设备连接失败，退出")
        return False
    
    logger.info("✓ 设备已连接")
    logger.info(f"  设备信息: {device_mgr.get_device_info()}")
    
    # 初始化 App 控制器
    logger.info("\n[2] 初始化 App 控制器...")
    controller = AppController(device_mgr)
    
    # 执行自动化操作
    logger.info("\n[3] 执行自动化操作...")
    logger.info("(假设番茄小说 App 已经打开)")
    
    try:
        # 操作 1: 点击搜索框
        logger.info("\n--- 操作 1: 点击搜索框 ---")
        before_search_click = ui_signature(controller.device)
        if controller.click_search_box():
            logger.info("✓ 搜索框点击成功")
        else:
            logger.error("✗ 搜索框点击失败")
            return False
        
        # 等待搜索框激活，避免页面未切换就继续输入
        logger.info("等待搜索框激活...")
        import time
        if not wait_for_ui_change(controller.device, before_search_click, timeout=8):
            time.sleep(1)
        
        # 操作 2: 输入书籍名称
        logger.info(f"\n--- 操作 2: 输入书籍名称 '{book_name}' ---")
        
        # 使用 uiautomator2 输入文本
        controller.device.send_keys(book_name)
        logger.info("✓ 书籍名称输入完成")
        
        # 操作 3: 点击搜索按钮
        logger.info("\n--- 操作 3: 点击搜索按钮 ---")
        time.sleep(0.3)  # 等待输入完成
        
        # 搜索按钮坐标: [1479,55][1555,107]
        # 中心点: x=(1479+1555)/2=1517, y=(55+107)/2=81
        search_button_x = 1517
        search_button_y = 81
        
        controller.device.click(search_button_x, search_button_y)
        logger.info("✓ 搜索按钮已点击")
        # 等待搜索结果加载，优先等到“书籍”标签出现
        wait_for_any_selector(
            controller.device,
            selectors=[{"text": "书籍"}, {"resourceId": "com.dragon.read:id/it"}],
            timeout=12,
        )

        # 操作 4: 切换到“书籍”标签，避免综合页误触作者入口
        logger.info("\n--- 操作 4: 切换到书籍标签 ---")
        if controller.device(text="书籍").exists(timeout=2):
            controller.device(text="书籍").click()
            logger.info("✓ 已切换到书籍标签")
            time.sleep(0.8)
        else:
            logger.warning("未找到书籍标签，继续尝试点击首条结果")

        # 操作 5: 点击第一条小说结果（优先点击左侧封面区域）
        logger.info("\n--- 操作 5: 点击第一条小说结果 ---")
        if controller.device(resourceId="com.dragon.read:id/it").exists(timeout=2):
            before_result_click = ui_signature(controller.device)
            controller.device(resourceId="com.dragon.read:id/it").click()
            logger.info("✓ 已点击第一条小说封面")
            wait_for_ui_change(controller.device, before_result_click, timeout=8)
        elif controller.device(resourceId="com.dragon.read:id/akn").exists(timeout=2):
            before_result_click = ui_signature(controller.device)
            controller.device(resourceId="com.dragon.read:id/akn").click()
            logger.info("✓ 已点击第一条搜索结果容器")
            wait_for_ui_change(controller.device, before_result_click, timeout=8)
        else:
            logger.error("✗ 未找到第一条搜索结果")
            return False

        # 操作 6: 等待3秒后回退3次，返回主页面
        logger.info("\n--- 操作 6: 等待后回退至主页面 ---")
        time.sleep(3)
        for i in range(3):
            controller.device.press("back")
            logger.info(f"✓ 已执行第 {i + 1}/3 次回退")
            time.sleep(0.5)
        
        logger.info("\n✓ 所有操作完成")
        
    except Exception as e:
        logger.error(f"自动化操作失败: {e}", exc_info=True)
        return False
    finally:
        # 清理
        logger.info("\n[4] 程序结束")
        logger.info("✓ 资源已释放")
    
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='番茄小说自动搜索程序')
    parser.add_argument('book_name', type=str, help='要搜索的书籍名称')
    
    args = parser.parse_args()
    
    success = main(args.book_name)
    sys.exit(0 if success else 1)
