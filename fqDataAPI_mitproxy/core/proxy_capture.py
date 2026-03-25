"""
抓包代理控制模块。

默认通过 mitmproxy addon 暴露的控制接口完成两件事：
1. 清空当前抓包会话
2. 导出当前抓包会话 JSON
"""

import os
from typing import Any, Dict, List

import requests


CAPTURE_BACKEND_LABEL = os.getenv("CAPTURE_BACKEND_LABEL", "mitmproxy")
CAPTURE_CONTROL_HOST = os.getenv("CAPTURE_CONTROL_HOST", "mitm.capture")
CAPTURE_CONTROL_BASE_URL = os.getenv(
    "CAPTURE_CONTROL_BASE_URL", f"http://{CAPTURE_CONTROL_HOST}"
)
CAPTURE_CLEAR_URL = os.getenv(
    "CAPTURE_CLEAR_URL", f"{CAPTURE_CONTROL_BASE_URL.rstrip('/')}/session/clear"
)
CAPTURE_EXPORT_URL = os.getenv(
    "CAPTURE_EXPORT_URL", f"{CAPTURE_CONTROL_BASE_URL.rstrip('/')}/session/export-json"
)
CAPTURE_TIMEOUT_SECONDS = int(os.getenv("CAPTURE_CONTROL_TIMEOUT_SECONDS", "10"))

# mitmproxy 监听地址。控制接口请求必须走这里，不依赖系统代理。
_MITM_PROXY_HOST = os.getenv("MITM_PROXY_HOST", "127.0.0.1")
_MITM_PROXY_PORT = os.getenv("MITM_PROXY_PORT", "8080")
_CONTROL_PROXIES = {
    "http": f"http://{_MITM_PROXY_HOST}:{_MITM_PROXY_PORT}",
    "https": f"http://{_MITM_PROXY_HOST}:{_MITM_PROXY_PORT}",
}


def normalize_entries(export_json: Any) -> List[Dict[str, Any]]:
    """将导出结构统一为 entry 列表。"""
    if isinstance(export_json, list):
        return [item for item in export_json if isinstance(item, dict)]

    if isinstance(export_json, dict):
        log_obj = export_json.get("log")
        if isinstance(log_obj, dict):
            entries = log_obj.get("entries")
            if isinstance(entries, list):
                return [item for item in entries if isinstance(item, dict)]

        sessions = export_json.get("sessions")
        if isinstance(sessions, list):
            return [item for item in sessions if isinstance(item, dict)]

    return []


def clear_capture_session(logger, required: bool = False) -> bool:
    """清空当前抓包会话。"""
    try:
        requests.get(
            CAPTURE_CLEAR_URL,
            timeout=CAPTURE_TIMEOUT_SECONDS,
            proxies=_CONTROL_PROXIES,
        )
        logger.info("✓ %s 抓包已清空", CAPTURE_BACKEND_LABEL)
        return True
    except Exception as exc:
        if required:
            logger.error("清空 %s 抓包失败，终止执行: %s", CAPTURE_BACKEND_LABEL, exc)
        else:
            logger.warning("清空 %s 抓包失败，继续执行: %s", CAPTURE_BACKEND_LABEL, exc)
        return False


def export_capture_json(timeout: int | None = None) -> Any:
    """导出当前抓包会话 JSON。"""
    response = requests.get(
        CAPTURE_EXPORT_URL,
        timeout=timeout or CAPTURE_TIMEOUT_SECONDS,
        proxies=_CONTROL_PROXIES,
    )
    response.raise_for_status()
    return response.json()


def get_entry_start_key(entry: Dict[str, Any]) -> float:
    """返回可排序的开始时间，兼容字符串和数字。"""
    times = entry.get("times")
    if not isinstance(times, dict):
        return 0.0

    start = times.get("start")
    if isinstance(start, (int, float)):
        return float(start)

    if isinstance(start, str):
        try:
            return float(start)
        except ValueError:
            return 0.0

    return 0.0
