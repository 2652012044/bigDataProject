"""
番茄小说 App 自动化 - 根据作者名搜索用户并提取用户基本信息
"""
import argparse
import json
import sys
import time
from pathlib import Path

import requests

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from core.app_controller import AppController
from core.device import DeviceManager
from core.logger import setup_logger
from core.proxy_capture import (
    clear_capture_session,
    export_capture_json,
    normalize_entries,
)
from core.wait_utils import (
    ui_signature,
    wait_for_any_selector,
    wait_for_text_in_any_selector,
    wait_for_ui_change,
)


SEARCH_BUTTON_X = 1517
SEARCH_BUTTON_Y = 81
SEARCH_INPUT_SELECTORS = [
    {"resourceId": "com.dragon.read:id/search_input"},
    {"resourceId": "com.dragon.read:id/edt_search"},
    {"resourceId": "com.dragon.read:id/search_src_text"},
    {"className": "android.widget.EditText", "focused": True},
    {"className": "android.widget.EditText"},
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="搜索作者并提取用户基本信息")
    parser.add_argument("author_name", type=str, help="作者/用户名称")
    return parser.parse_args()


def _sanitize_file_name(name: str) -> str:
    """将名称中的非法字符替换为下划线，用于文件名。"""
    if not name:
        return "unknown"
    invalid = '<>:"/\\|?*'
    safe = "".join("_" if ch in invalid else ch for ch in name.strip())
    return safe or "unknown"


def _save_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def export_and_extract_user_info(logger, author_name: str) -> bool:
    """导出抓包，提取 /reading/user/basic_info/get/ 的响应体并保存。"""
    output_dir = Path("data")
    export_path = output_dir / "capture_export_filtered.json"

    try:
        export_json = export_capture_json()
    except Exception as e:
        logger.error("导出 mitmproxy 抓包失败: %s", e)
        return False

    _save_json(export_path, export_json)
    logger.info("✓ mitmproxy 导出完成: %s", export_path)

    entries = normalize_entries(export_json)
    matched = [
        entry
        for entry in entries
        if isinstance(entry.get("path"), str)
        and "/reading/user/basic_info/get/" in entry.get("path", "")
    ]

    logger.info("user/basic_info/get 命中条数: %d", len(matched))
    if not matched:
        logger.warning("未找到 /reading/user/basic_info/get/ 相关请求")
        return False

    # 取最后一条（通常是点击用户后触发的那次）
    entry = matched[-1]
    response_obj = entry.get("response") if isinstance(entry, dict) else None
    body_obj = response_obj.get("body") if isinstance(response_obj, dict) else None
    body_text = body_obj.get("text") if isinstance(body_obj, dict) else None

    if not isinstance(body_text, str) or not body_text.strip():
        logger.error("响应体为空，无法提取用户信息")
        return False

    try:
        body_json = json.loads(body_text)
    except json.JSONDecodeError as e:
        logger.error("响应体 JSON 解析失败: %s", e)
        return False

    file_name = _sanitize_file_name(author_name)
    info_dir = output_dir / "userInfo"
    info_path = info_dir / f"{file_name}_info.json"
    _save_json(info_path, body_json)
    logger.info("✓ 用户信息已保存: %s", info_path)
    return True


def main(author_name: str) -> bool:
    logger = setup_logger("get_user_api")

    logger.info("=" * 60)
    logger.info("番茄小说 App 自动化 - 获取用户基本信息")
    logger.info("=" * 60)
    logger.info("搜索作者: %s", author_name)

    logger.info("\n[0] 预清空 mitmproxy 抓包（初始化前）...")
    clear_capture_session(logger)

    logger.info("\n[1] 初始化设备...")
    device_mgr = DeviceManager()
    if not device_mgr.connect():
        logger.error("设备连接失败，退出")
        return False
    logger.info("✓ 设备已连接")
    logger.info("  设备信息: %s", device_mgr.get_device_info())

    logger.info("\n[2] 初始化 App 控制器...")
    controller = AppController(device_mgr)

    try:
        logger.info("\n[3] 执行自动化操作...")

        # 正式开始前再次清空抓包，确保只抓本次流量
        logger.info("--- 清空 mitmproxy（自动化开始前）---")
        if not clear_capture_session(logger, required=True):
            return False
        logger.info("✓ mitmproxy 已就绪")

        # 操作 1: 点击搜索框
        logger.info("\n--- 操作 1: 点击搜索框 ---")
        before_search_click = ui_signature(controller.device)
        if not controller.click_search_box():
            logger.error("✗ 搜索框点击失败")
            return False
        logger.info("✓ 搜索框点击成功")

        # 等待搜索框激活
        if not wait_for_ui_change(controller.device, before_search_click, timeout=8):
            time.sleep(1)

        # 操作 2: 输入作者名称
        logger.info("\n--- 操作 2: 输入作者名称 '%s' ---", author_name)
        controller.device.send_keys(author_name)
        if not wait_for_text_in_any_selector(
            controller.device,
            SEARCH_INPUT_SELECTORS,
            expected_text=author_name,
            timeout=5,
        ):
            logger.warning("首次输入未校验通过，重试输入一次...")
            controller.device.send_keys(author_name)

        if not wait_for_text_in_any_selector(
            controller.device,
            SEARCH_INPUT_SELECTORS,
            expected_text=author_name,
            timeout=5,
        ):
            logger.error("✗ 搜索框内容校验失败，终止点击搜索")
            return False
        logger.info("✓ 输入并校验完成")

        # 操作 3: 点击搜索按钮
        logger.info("\n--- 操作 3: 点击搜索按钮 ---")
        time.sleep(0.3)
        before_search_submit = ui_signature(controller.device)
        controller.device.click(SEARCH_BUTTON_X, SEARCH_BUTTON_Y)
        logger.info("✓ 已点击搜索按钮")
        wait_for_ui_change(controller.device, before_search_submit, timeout=10)
        wait_for_any_selector(
            controller.device,
            selectors=[{"text": "用户"}, {"text": "书籍"}, {"resourceId": "com.dragon.read:id/it"}],
            timeout=10,
        )

        # 操作 4: 切换到"用户"标签
        logger.info("\n--- 操作 4: 切换到用户标签 ---")
        if controller.device(text="用户").exists(timeout=5):
            before_tab_click = ui_signature(controller.device)
            controller.device(text="用户").click()
            logger.info("✓ 已点击用户标签")
            wait_for_ui_change(controller.device, before_tab_click, timeout=8)
            time.sleep(1)
        else:
            logger.warning("未找到用户标签，尝试继续点击首条结果")

        # 操作 5: 点击第一条用户条目
        logger.info("\n--- 操作 5: 点击第一条用户条目 ---")
        clicked = False

        # 优先：用户列表条目以 content-desc 存储用户名，直接按名称点击
        if controller.device(description=author_name).exists(timeout=3):
            before_item_click = ui_signature(controller.device)
            controller.device(description=author_name).click()
            logger.info("✓ 已点击用户条目 (description=%s)", author_name)
            wait_for_ui_change(controller.device, before_item_click, timeout=8)
            clicked = True

        # 备用：尝试常见的列表条目 resourceId
        if not clicked:
            for rid in [
                "com.dragon.read:id/it",
                "com.dragon.read:id/akn",
                "com.dragon.read:id/user_item",
                "com.dragon.read:id/search_user_item",
            ]:
                if controller.device(resourceId=rid).exists(timeout=2):
                    before_item_click = ui_signature(controller.device)
                    controller.device(resourceId=rid).click()
                    logger.info("✓ 已点击第一条用户条目 (resourceId=%s)", rid)
                    wait_for_ui_change(controller.device, before_item_click, timeout=8)
                    clicked = True
                    break

        if not clicked:
            logger.error("✗ 未找到用户列表条目，终止操作")
            return False

        # 操作 6: 等待 3 秒（触发用户基本信息接口）
        logger.info("\n--- 操作 6: 等待 3 秒（等待接口触发）---")
        time.sleep(3)
        logger.info("✓ 等待完成")

        # 操作 7: 回退 3 次
        logger.info("\n--- 操作 7: 回退 3 次 ---")
        for i in range(3):
            controller.device.press("back")
            logger.info("✓ 已执行第 %d/3 次回退", i + 1)
            time.sleep(0.5)

        # 操作 8: 导出 mitmproxy 并提取用户信息
        logger.info("\n--- 操作 8: 导出 mitmproxy 并提取用户信息 ---")
        if not export_and_extract_user_info(logger, author_name):
            logger.error("导出或提取用户信息失败")
            return False

        logger.info("\n✓ 所有操作完成")
        return True

    except Exception as exc:
        logger.error("执行失败: %s", exc, exc_info=True)
        return False
    finally:
        logger.info("\n[4] 程序结束")


if __name__ == "__main__":
    args = parse_args()
    ok = main(args.author_name)
    sys.exit(0 if ok else 1)
