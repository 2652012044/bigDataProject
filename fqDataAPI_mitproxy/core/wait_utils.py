"""Utility wait helpers for flaky mobile UI loading scenarios."""

import hashlib
import time
from typing import Dict, List, Optional


def ui_signature(device) -> str:
    """Return current UI hierarchy signature."""
    xml = device.dump_hierarchy()
    return hashlib.md5(xml.encode("utf-8")).hexdigest()


def wait_for_ui_change(device, old_sig: str, timeout: float = 12.0, interval: float = 0.4) -> bool:
    """Wait until hierarchy changes from old signature."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if ui_signature(device) != old_sig:
            return True
        time.sleep(interval)
    return False


def wait_for_selector(device, selector: Dict[str, str], timeout: float = 12.0, interval: float = 0.4) -> bool:
    """Wait until one selector exists."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            if device(**selector).exists(timeout=0):
                return True
        except Exception:
            pass
        time.sleep(interval)
    return False


def wait_for_any_selector(
    device, selectors: List[Dict[str, str]], timeout: float = 12.0, interval: float = 0.4
) -> Optional[Dict[str, str]]:
    """Wait until any selector exists and return the matched selector."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        for selector in selectors:
            try:
                if device(**selector).exists(timeout=0):
                    return selector
            except Exception:
                continue
        time.sleep(interval)
    return None


_APP_PACKAGE = "com.dragon.read"

# 主界面可交互的标志性元素，任一出现即表示 App 主页已就绪
_HOME_READY_SELECTORS: List[Dict[str, str]] = [
    {"text": "书架"},
    {"text": "分类"},
    {"resourceId": "com.dragon.read:id/ia1"},           # 分类按钮
    {"resourceId": "com.dragon.read:id/search_input"},  # 搜索框
]


def wait_for_app_ready(device, timeout: float = 300.0, interval: float = 1.0) -> bool:
    """等待番茄小说主界面完全加载并可交互。

    轮询直到满足以下全部条件：
    - 当前包名为 com.dragon.read
    - Activity 不含 "splash" 或 "loading"（不在启动/闪屏页）
    - 屏幕上出现至少一个主界面常驻控件

    Args:
        device:  uiautomator2 设备对象
        timeout: 最长等待秒数（默认 300）
        interval: 轮询间隔（默认 1 秒）

    Returns:
        True 表示就绪，False 表示超时
    """
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            current = device.app_current() or {}
            pkg = current.get("package", "")
            act = current.get("activity", "").lower()
            if pkg == _APP_PACKAGE and "splash" not in act and "loading" not in act:
                for sel in _HOME_READY_SELECTORS:
                    try:
                        if device(**sel).exists(timeout=0):
                            return True
                    except Exception:
                        pass
        except Exception:
            pass
        time.sleep(interval)
    return False


def wait_for_text_in_any_selector(
    device,
    selectors: List[Dict[str, str]],
    expected_text: str,
    timeout: float = 8.0,
    interval: float = 0.2,
) -> Optional[Dict[str, str]]:
    """Wait until one selector's displayed text equals expected_text."""
    target = (expected_text or "").strip()
    if not target:
        return None

    deadline = time.time() + timeout
    while time.time() < deadline:
        for selector in selectors:
            try:
                obj = device(**selector)
                if not obj.exists(timeout=0):
                    continue

                current_text = None
                try:
                    current_text = obj.get_text()
                except Exception:
                    pass

                if not isinstance(current_text, str) or not current_text.strip():
                    try:
                        info = obj.info
                        if isinstance(info, dict):
                            raw = info.get("text")
                            if isinstance(raw, str):
                                current_text = raw
                    except Exception:
                        pass

                if isinstance(current_text, str) and current_text.strip() == target:
                    return selector
            except Exception:
                continue
        time.sleep(interval)

    return None
