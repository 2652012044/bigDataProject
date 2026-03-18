"""
UI 调试脚本 - 获取界面组件结构和截图
用于找到正确的选择器
"""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.device import DeviceManager
from core.app_controller import AppController
from core.logger import setup_logger


def debug_ui():
    """调试 UI 组件"""
    logger = setup_logger("debug_ui")
    
    logger.info("=" * 60)
    logger.info("UI 调试工具")
    logger.info("=" * 60)
    
    # 初始化
    device_mgr = DeviceManager()
    device_mgr.connect()
    
    controller = AppController(device_mgr)
    
    logger.info("\n[1] 获取界面截图...")
    screenshot_path = "screenshot_debug.png"
    try:
        controller.device.screenshot(screenshot_path)
        logger.info(f"✓ 截图已保存: {screenshot_path}")
    except Exception as e:
        logger.error(f"截图失败: {e}")
    
    logger.info("\n[2] 获取当前 Activity...")
    try:
        current = controller.device.app_current()
        logger.info(f"✓ 当前应用: {current}")
    except Exception as e:
        logger.error(f"获取 Activity 失败: {e}")
    
    logger.info("\n[3] 获取界面 XML 信息...")
    try:
        # 导出界面结构
        xml_content = controller.device.dump_hierarchy()
        
        # 保存 XML 文件
        xml_path = "hierarchy_debug.xml"
        with open(xml_path, 'w', encoding='utf-8') as f:
            f.write(xml_content)
        logger.info(f"✓ 界面结构已保存: {xml_path}")
        
        # 提取搜索相关的组件
        logger.info("\n[4] 搜索 '搜索' 相关的组件...")
        if "搜索" in xml_content:
            lines = xml_content.split('\n')
            for i, line in enumerate(lines):
                if "搜索" in line or "search" in line.lower():
                    # 打印前后几行以获取上下文
                    start = max(0, i - 2)
                    end = min(len(lines), i + 3)
                    logger.info("\n" + "\n".join(lines[start:end]))
                    logger.info("-" * 40)
        
        # 提取所有有 text 或 hint 属性的组件
        logger.info("\n[5] 所有可点击的组件:")
        import re
        # 查找包含 clickable="true" 的元素
        clickable_pattern = r'<(\w+)[^>]*clickable="true"[^>]*>'
        clickables = re.findall(clickable_pattern, xml_content)
        logger.info(f"可点击组件类型: {set(clickables)}")
        
        # 查找包含 resourceId 的元素
        logger.info("\n[6] 搜索框相关的 resourceId:")
        resource_pattern = r'resourceId="([^"]*search[^"]*)"'
        resources = re.findall(resource_pattern, xml_content, re.IGNORECASE)
        for res in resources:
            logger.info(f"  - {res}")
        
    except Exception as e:
        logger.error(f"获取界面信息失败: {e}", exc_info=True)
    
    logger.info("\n[7] 设备信息:")
    try:
        info = controller.device.info
        logger.info(f"✓ 分辨率: {info.get('displayWidth')}x{info.get('displayHeight')}")
        logger.info(f"✓ Android 版本: {info.get('release')}")
        logger.info(f"✓ 设备型号: {info.get('model')}")
    except Exception as e:
        logger.error(f"获取设备信息失败: {e}")
    
    logger.info("\n" + "=" * 60)
    logger.info("调试完成！")
    logger.info("=" * 60)
    logger.info("\n提示:")
    logger.info("1. 查看 screenshot_debug.png 了解当前界面")
    logger.info("2. 查看 hierarchy_debug.xml 获取完整的组件结构")
    logger.info("3. 根据 resourceId 或 text 更新选择器")


if __name__ == "__main__":
    try:
        debug_ui()
    except Exception as e:
        print(f"调试失败: {e}")
        import traceback
        traceback.print_exc()
