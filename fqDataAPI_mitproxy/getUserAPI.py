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


def _click_first_user_result(device, logger, author_name: str, max_rounds: int = 3) -> bool:
    """点击首条用户搜索结果（跨版本兼容策略）。

    优先按 content-desc 精确匹配用户名，其次尝试常见 resourceId，
    最后以比例坐标兜底，并在每轮失败后轻微上滑重试。
    """
    user_selectors = [
        {"resourceId": "com.dragon.read:id/it"},
        {"resourceId": "com.dragon.read:id/akn"},
        {"resourceId": "com.dragon.read:id/user_item"},
        {"resourceId": "com.dragon.read:id/search_user_item"},
    ]

    for round_idx in range(max_rounds):
        logger.info("尝试点击首条用户结果（第 %d/%d 轮）", round_idx + 1, max_rounds)

        # 优先：按 content-desc 精确匹配用户名
        try:
            if device(description=author_name).exists(timeout=2):
                before_click = ui_signature(device)
                device(description=author_name).click()
                if wait_for_ui_change(device, before_click, timeout=4):
                    logger.info("✓ 已点击用户条目 (description=%s)", author_name)
                    return True
        except Exception:
            pass

        # 备用：尝试常见 resourceId
        for sel in user_selectors:
            try:
                if not device(**sel).exists(timeout=1):
                    continue
                before_click = ui_signature(device)
                device(**sel).click()
                if wait_for_ui_change(device, before_click, timeout=4):
                    logger.info("✓ 已点击首条用户条目: %s", sel)
                    return True
            except Exception:
                continue

        # 兜底：比例坐标点击首条区域
        try:
            sw, sh = device.window_size()
            fallback_points = [
                (int(sw * 0.20), int(sh * 0.30)),
                (int(sw * 0.50), int(sh * 0.30)),
                (int(sw * 0.20), int(sh * 0.40)),
            ]
            for x, y in fallback_points:
                before_click = ui_signature(device)
                device.click(x, y)
                if wait_for_ui_change(device, before_click, timeout=3):
                    logger.info("✓ 已通过坐标兜底点击首条用户结果: (%d, %d)", x, y)
                    return True
        except Exception:
            pass

        # 下一轮前轻微上滑，兼容首条被吸顶/广告占位的情况
        if round_idx < max_rounds - 1:
            try:
                sw, sh = device.window_size()
                device.swipe(int(sw * 0.50), int(sh * 0.78), int(sw * 0.50), int(sh * 0.52), 0.2)
                time.sleep(0.4)
            except Exception:
                pass

    logger.error("✗ 未能点击首条用户搜索结果（已尝试 %d 轮）", max_rounds)
    return False


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
    logger.info("导出条目总数: %d", len(entries))
    matched = [
        entry
        for entry in entries
        if isinstance(entry.get("path"), str)
        and "/reading/user/basic_info/get" in entry.get("path", "")
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

        # 清空抓包，确保只抓本次流量
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
        # 额外稳定等待，确保输入法已弹出
        time.sleep(1.0)

        # 操作 2: 输入作者名称
        logger.info("\n--- 操作 2: 输入作者名称 '%s' ---", author_name)
        # 先清空搜索框，再输入，避免残留内容导致校验失败
        controller.device.clear_text()
        time.sleep(0.3)
        controller.device.send_keys(author_name)
        if not wait_for_text_in_any_selector(
            controller.device,
            SEARCH_INPUT_SELECTORS,
            expected_text=author_name,
            timeout=6,
        ):
            logger.warning("首次输入未校验通过，重试输入一次...")
            controller.device.clear_text()
            time.sleep(0.3)
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
        _search_btn_selectors = [
            {"resourceId": "com.dragon.read:id/search_btn"},
            {"resourceId": "com.dragon.read:id/btn_search"},
            {"resourceId": "com.dragon.read:id/iv_search"},
            {"text": "搜索", "className": "android.widget.TextView"},
            {"description": "搜索"},
        ]
        _btn_clicked = False
        for _sel in _search_btn_selectors:
            try:
                if controller.device(**_sel).exists(timeout=1):
                    controller.device(**_sel).click()
                    _btn_clicked = True
                    break
            except Exception:
                pass
        if not _btn_clicked:
            # 回退：按屏幕宽度比例点击（搜索按钮在右侧边缘约 98%，上方约 10% 处）
            _sw, _sh = controller.device.window_size()
            controller.device.click(int(_sw * 0.97), int(_sh * 0.09))
        logger.info("✓ 搜索按钮已点击")
        wait_for_any_selector(
            controller.device,
            selectors=[{"text": "用户"}, {"text": "书籍"}, {"resourceId": "com.dragon.read:id/it"}],
            timeout=12,
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
        if not _click_first_user_result(controller.device, logger, author_name, max_rounds=3):
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
