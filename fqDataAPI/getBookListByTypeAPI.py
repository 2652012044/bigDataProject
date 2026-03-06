"""Search by type, switch to book tab, scroll to bottom (or timeout), then go back 3 times."""

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import requests

# Add current directory to import path.
sys.path.insert(0, str(Path(__file__).parent))

from core.app_controller import AppController
from core.device import DeviceManager
from core.logger import setup_logger
from core.wait_utils import ui_signature, wait_for_any_selector, wait_for_ui_change


SEARCH_BUTTON_X = 1517
SEARCH_BUTTON_Y = 81
SCROLL_TIMEOUT_SECONDS = 180
STABLE_THRESHOLD = 4
CHARLES_CLEAR_URL = "http://control.charles/session/clear"
CHARLES_EXPORT_URL = "http://control.charles/session/export-json"
CHARLES_TIMEOUT_SECONDS = 10


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Search books by type and scroll results")
    parser.add_argument("type", type=str, help="Search keyword/type")
    parser.add_argument(
        "scroll_timeout_seconds",
        type=int,
        nargs="?",
        default=SCROLL_TIMEOUT_SECONDS,
        help="Scroll timeout in seconds (default: 180)",
    )
    return parser.parse_args()


def clear_charles_session(logger) -> bool:
    """Clear existing Charles captured sessions before automation starts."""
    try:
        requests.get(CHARLES_CLEAR_URL, timeout=CHARLES_TIMEOUT_SECONDS)
        logger.info("✓ Charles 抓包已清空")
        return True
    except Exception as e:
        logger.warning(f"清空 Charles 抓包失败，继续执行: {e}")
        return False


def _page_signature(controller: AppController) -> str:
    """Use hierarchy hash as page-state signature for bottom detection."""
    xml = controller.device.dump_hierarchy()
    return hashlib.md5(xml.encode("utf-8")).hexdigest()


def _scroll_down_once(controller: AppController) -> None:
    """Swipe up once to load next screenful of results."""
    w, h = controller.device.window_size()
    x = int(w * 0.5)
    y_start = int(h * 0.80)
    y_end = int(h * 0.30)
    controller.device.swipe(x, y_start, x, y_end, duration=0.2)


def _normalize_entries(export_json):
    """Normalize Charles export structure to entry list."""
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


def _sanitize_folder_name(name: str) -> str:
    """Make a safe folder suffix for Windows paths."""
    if not name:
        return "unknown"

    invalid = '<>:"/\\|?*'
    safe = "".join("_" if ch in invalid else ch for ch in name.strip())
    return safe or "unknown"


def _save_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _pick_text(value):
    """Pick text from str or {'text': ...} style field."""
    if isinstance(value, str):
        text = value.strip()
        return text or None
    if isinstance(value, dict):
        text = value.get("text")
        if isinstance(text, str):
            text = text.strip()
            return text or None
    return None


def _extract_book_info_from_dict(item: dict):
    """Extract rich book info from one dict if it looks like a book object."""
    book_id = item.get("book_id") or item.get("bookId") or item.get("bookid") or item.get("book_id_str")
    if book_id is None:
        return None

    book_name = (
        _pick_text(item.get("book_name"))
        or _pick_text(item.get("book_title"))
        or _pick_text(item.get("original_book_name"))
        or _pick_text(item.get("title"))
    )

    # Fallback from highlighted title structure.
    if not book_name and isinstance(item.get("search_high_light"), dict):
        book_name = _pick_text(item["search_high_light"].get("title"))

    author = _pick_text(item.get("author"))
    if not author and isinstance(item.get("author_info"), dict):
        author = _pick_text(item["author_info"].get("name"))

    info = {
        "book_id": str(book_id),
        "book_name": book_name,
        "author": author,
        "score": _pick_text(item.get("score")) or item.get("score"),
        "word_number": _pick_text(item.get("word_number")) or item.get("word_number"),
        "category": _pick_text(item.get("category")) or item.get("category"),
        "tags": _pick_text(item.get("tags")) or item.get("tags"),
        "creation_status": _pick_text(item.get("creation_status")) or item.get("creation_status"),
        "update_status": _pick_text(item.get("update_status")) or item.get("update_status"),
        "read_count": _pick_text(item.get("read_count")) or item.get("read_count"),
        "chapter_number": _pick_text(item.get("chapter_number")) or item.get("chapter_number"),
    }

    # Require at least a usable book name.
    if not info["book_name"]:
        return None
    return info


def _merge_book_info(old_info: dict, new_info: dict) -> dict:
    """Merge two book info dicts, preferring non-empty new fields."""
    merged = dict(old_info)
    for key, value in new_info.items():
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        merged[key] = value
    return merged


def _collect_book_infos(node, book_map: dict):
    """Recursively collect book objects from nested JSON."""
    if isinstance(node, dict):
        maybe_info = _extract_book_info_from_dict(node)
        if maybe_info:
            book_id = maybe_info["book_id"]
            if book_id in book_map:
                book_map[book_id] = _merge_book_info(book_map[book_id], maybe_info)
            else:
                book_map[book_id] = maybe_info

        for value in node.values():
            _collect_book_infos(value, book_map)

    elif isinstance(node, list):
        for item in node:
            _collect_book_infos(item, book_map)


def update_book_list_json(logger, folder_tag_name: str) -> bool:
    """Extract names from body_*.json and merge into data/BookList.json."""
    output_dir = Path("data")
    tag_name = _sanitize_folder_name(folder_tag_name)
    folder = output_dir / f"bookListTab_{tag_name}"
    if not folder.exists():
        logger.warning("目录不存在，无法提取书名: %s", folder)
        return False

    body_files = sorted(folder.glob("body_*.json"))
    if not body_files:
        logger.warning("未找到 body_*.json，跳过书名提取")
        return False

    # Ignore the first response body (usually tab/filter metadata, not stable book list data).
    if len(body_files) > 1:
        body_files = body_files[1:]
    else:
        logger.warning("仅存在一个 body 文件，跳过解析以避免使用首个响应体")
        return False

    book_map = {}
    for body_file in body_files:
        try:
            with body_file.open("r", encoding="utf-8") as f:
                body_json = json.load(f)
            _collect_book_infos(body_json, book_map)
        except Exception as e:
            logger.warning("解析失败，已跳过 %s: %s", body_file, e)

    book_list = sorted(
        book_map.values(),
        key=lambda x: ((x.get("book_name") or ""), (x.get("book_id") or "")),
    )
    logger.info("提取到书籍数量: %d", len(book_list))

    book_list_path = output_dir / "BookList.json"
    merged = {}
    if book_list_path.exists():
        try:
            with book_list_path.open("r", encoding="utf-8") as f:
                loaded = json.load(f)
            if isinstance(loaded, dict):
                merged = loaded
        except Exception as e:
            logger.warning("读取现有 BookList.json 失败，将重建: %s", e)

    # Merge policy: keep other tags, overwrite only current tag list.
    merged[folder_tag_name] = book_list
    _save_json(book_list_path, merged)
    logger.info("✓ 书籍信息列表已更新: %s (标签=%s)", book_list_path, folder_tag_name)
    return True


def export_and_extract_book_tab_files(logger, folder_tag_name: str) -> bool:
    """Export Charles session and save all search/tab entries by tag name."""
    output_dir = Path("data")
    export_path = output_dir / "charles_export_filtered.json"

    try:
        resp = requests.get(CHARLES_EXPORT_URL, timeout=CHARLES_TIMEOUT_SECONDS)
        resp.raise_for_status()
        export_json = resp.json()
    except Exception as e:
        logger.error("导出 Charles 抓包失败: %s", e)
        return False

    _save_json(export_path, export_json)
    logger.info("✓ Charles 导出完成: %s", export_path)

    entries = _normalize_entries(export_json)
    matched = [
        entry
        for entry in entries
        if isinstance(entry.get("path"), str)
        and entry.get("path", "").startswith("/reading/bookapi/search/tab/")
    ]

    logger.info("search/tab 命中条数: %d", len(matched))
    if not matched:
        logger.warning("未找到 /reading/bookapi/search/tab/ 请求")
        return True

    tag_name = _sanitize_folder_name(folder_tag_name)
    folder = output_dir / f"bookListTab_{tag_name}"
    folder.mkdir(parents=True, exist_ok=True)

    for idx, entry in enumerate(matched, start=1):
        entry_path = folder / f"entry_{idx}.json"
        _save_json(entry_path, entry)

        response_obj = entry.get("response") if isinstance(entry, dict) else None
        body_obj = response_obj.get("body") if isinstance(response_obj, dict) else None
        body_text = body_obj.get("text") if isinstance(body_obj, dict) else None

        if isinstance(body_text, str) and body_text.strip():
            try:
                body_json = json.loads(body_text)
                _save_json(folder / f"body_{idx}.json", body_json)
            except Exception:
                (folder / f"body_{idx}.txt").write_text(body_text, encoding="utf-8")

    logger.info("✓ 已保存所有 search/tab 文件到 data/bookListTab_{标签名称}/")
    return True


def main(book_type: str, scroll_timeout_seconds: int) -> bool:
    logger = setup_logger("get_book_list_by_type_api")

    logger.info("=" * 60)
    logger.info("按分类关键词抓取书籍列表")
    logger.info("=" * 60)
    logger.info("关键词(type): %s", book_type)
    logger.info("下拉超时(秒): %s", scroll_timeout_seconds)

    logger.info("\n[0] 清空 Charles 抓包...")
    clear_charles_session(logger)

    logger.info("\n[1] 初始化设备...")
    device_mgr = DeviceManager()
    if not device_mgr.connect():
        logger.error("设备连接失败，退出")
        return False
    logger.info("✓ 设备已连接")

    logger.info("\n[2] 初始化 App 控制器...")
    controller = AppController(device_mgr)

    try:
        logger.info("\n[3] 执行自动化操作...")

        logger.info("\n--- 操作 1: 点击搜索框 ---")
        before_search_click = ui_signature(controller.device)
        if not controller.click_search_box():
            logger.error("✗ 搜索框点击失败")
            return False
        logger.info("✓ 搜索框点击成功")

        logger.info("\n--- 操作 2: 输入 type 关键词 ---")
        if not wait_for_ui_change(controller.device, before_search_click, timeout=8):
            time.sleep(1)
        controller.device.send_keys(book_type)
        logger.info("✓ 输入完成")

        logger.info("\n--- 操作 3: 点击搜索按钮 ---")
        time.sleep(0.3)
        before_search_submit = ui_signature(controller.device)
        controller.device.click(SEARCH_BUTTON_X, SEARCH_BUTTON_Y)
        logger.info("✓ 已点击搜索按钮")
        wait_for_ui_change(controller.device, before_search_submit, timeout=10)
        wait_for_any_selector(
            controller.device,
            selectors=[{"text": "书籍"}, {"resourceId": "com.dragon.read:id/it"}],
            timeout=10,
        )

        logger.info("\n--- 操作 4: 切换到书籍标签 ---")
        if controller.device(text="书籍").exists(timeout=2):
            controller.device(text="书籍").click()
            logger.info("✓ 已切换到书籍标签")
            time.sleep(1)
        else:
            logger.warning("未找到书籍标签，继续后续滚动")

        logger.info("\n--- 操作 5: 持续下拉，直到到底或超时%s秒 ---", scroll_timeout_seconds)
        start_time = time.time()
        stable_count = 0
        last_sig = ""

        while True:
            if time.time() - start_time > scroll_timeout_seconds:
                logger.warning("达到超时(%s秒)，停止滚动", scroll_timeout_seconds)
                break

            sig = _page_signature(controller)
            if sig == last_sig:
                stable_count += 1
            else:
                stable_count = 0
            last_sig = sig

            if stable_count >= STABLE_THRESHOLD:
                logger.info("检测到页面连续未变化，判定已到底")
                break

            _scroll_down_once(controller)
            time.sleep(1.0)

        logger.info("\n--- 操作 6: 回退2次 ---")
        time.sleep(1)
        for i in range(2):
            controller.device.press("back")
            logger.info("✓ 已执行第 %d/2 次回退", i + 1)
            time.sleep(0.5)

        logger.info("\n--- 操作 7: 导出 Charles 并提取 search/tab 文件 ---")
        if not export_and_extract_book_tab_files(logger, book_type):
            logger.error("导出或提取失败")
            return False

        logger.info("\n--- 操作 8: 提取书籍名称列表并更新 BookList.json ---")
        update_book_list_json(logger, book_type)

        logger.info("\n✓ 所有操作完成")
        return True

    except Exception as exc:
        logger.error("执行失败: %s", exc, exc_info=True)
        return False


if __name__ == "__main__":
    args = parse_args()
    ok = main(args.type, args.scroll_timeout_seconds)
    sys.exit(0 if ok else 1)
