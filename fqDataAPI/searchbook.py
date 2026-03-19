"""
番茄小说 App 自动化控制主程序
"""
import sys
import json
import argparse
import re
import time
from pathlib import Path
import requests

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from core.device import DeviceManager
from core.app_controller import AppController
from core.logger import setup_logger
from core.wait_utils import (
    ui_signature,
    wait_for_any_selector,
    wait_for_text_in_any_selector,
    wait_for_ui_change,
)


CHARLES_CLEAR_URL = "http://control.charles/session/clear"
CHARLES_EXPORT_URL = "http://control.charles/session/export-json"
CHARLES_TIMEOUT_SECONDS = 10
SEARCH_INPUT_SELECTORS = [
    {"resourceId": "com.dragon.read:id/search_input"},
    {"resourceId": "com.dragon.read:id/edt_search"},
    {"resourceId": "com.dragon.read:id/search_src_text"},
    {"className": "android.widget.EditText", "focused": True},
    {"className": "android.widget.EditText"},
]


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


def _merge_dict_non_empty(old_data: dict, new_data: dict) -> dict:
    """Merge dict values preferring non-empty new fields."""
    merged = dict(old_data)
    for key, value in new_data.items():
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        merged[key] = value
    return merged


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


def _extract_book_id_from_comment_path(path: str):
    """Extract book id from /novel/commentapi/comment/list/{book_id}/... path."""
    if not isinstance(path, str):
        return None
    matched = re.match(r"^/novel/commentapi/comment/list/([^/?#]+)/?", path)
    if not matched:
        return None
    return matched.group(1)


def _repair_mojibake_text(value: str) -> str:
    """Try to repair UTF-8 text that was incorrectly decoded as latin-1."""
    if not isinstance(value, str):
        return value

    # Fast path: skip pure ASCII and avoid unnecessary decode attempts.
    if value.isascii():
        return value

    try:
        repaired = value.encode("latin-1").decode("utf-8")
    except Exception:
        return value

    # Keep repaired string only when it clearly improves readability.
    if any("\u4e00" <= ch <= "\u9fff" for ch in repaired):
        return repaired

    bad_markers = ("å", "ä", "æ", "ç", "é", "ï", "ã", "â", "¤")
    if sum(value.count(ch) for ch in bad_markers) > sum(repaired.count(ch) for ch in bad_markers):
        return repaired

    return value


def _repair_json_mojibake(node):
    """Recursively repair mojibake strings in parsed JSON objects."""
    if isinstance(node, dict):
        return {k: _repair_json_mojibake(v) for k, v in node.items()}
    if isinstance(node, list):
        return [_repair_json_mojibake(item) for item in node]
    if isinstance(node, str):
        return _repair_mojibake_text(node)
    return node


def export_and_extract_comment_files(logger, book_name: str) -> bool:
    """Export Charles and save comment-list related files to data/comtJson/{book_name}/."""
    output_dir = Path("data")
    export_path = output_dir / "charles_export_filtered.json"

    try:
        resp = requests.get(CHARLES_EXPORT_URL, timeout=CHARLES_TIMEOUT_SECONDS)
        resp.raise_for_status()
        export_json = resp.json()
    except Exception as e:
        logger.error("导出 Charles 抓包失败: %s", e)
        return False

    # Overwrite previous export file each run.
    _save_json(export_path, export_json)
    logger.info("✓ Charles 导出完成: %s", export_path)

    entries = _normalize_entries(export_json)
    matched = [
        entry
        for entry in entries
        if isinstance(entry.get("path"), str)
        and entry.get("path", "").startswith("/novel/commentapi/comment/list/")
    ]

    logger.info("comment/list 命中条数: %d", len(matched))
    if not matched:
        logger.warning("未找到 /novel/commentapi/comment/list/{书籍ID}/ 相关请求")
        return True

    grouped = {}
    for entry in matched:
        path = entry.get("path", "")
        book_id = _extract_book_id_from_comment_path(path)
        key = book_id or "unknown"
        grouped.setdefault(key, []).append(entry)

    target_book_id = max(grouped.keys(), key=lambda x: len(grouped[x]))
    selected_entries = grouped[target_book_id]
    logger.info("已选择书籍ID=%s 的评论请求，共 %d 条", target_book_id, len(selected_entries))

    folder_name = _sanitize_folder_name(book_name)
    folder = output_dir / "comtJson" / folder_name
    folder.mkdir(parents=True, exist_ok=True)

    for idx, entry in enumerate(selected_entries, start=1):
        entry_path = folder / f"entry_{idx}.json"
        _save_json(entry_path, entry)

        response_obj = entry.get("response") if isinstance(entry, dict) else None
        body_obj = response_obj.get("body") if isinstance(response_obj, dict) else None
        body_text = body_obj.get("text") if isinstance(body_obj, dict) else None

        if isinstance(body_text, str) and body_text.strip():
            try:
                body_json = json.loads(body_text)
                body_json = _repair_json_mojibake(body_json)
                _save_json(folder / f"body_{idx}.json", body_json)
            except Exception:
                (folder / f"body_{idx}.txt").write_text(body_text, encoding="utf-8")

    logger.info("✓ 评论相关文件已保存到: %s", folder)
    return True


def extract_book_info_from_comment_files(logger, book_name: str) -> bool:
    """Extract book profile and comment list from saved comment response bodies."""
    folder_name = _sanitize_folder_name(book_name)
    src_folder = Path("data") / "comtJson" / folder_name
    if not src_folder.exists():
        logger.warning("评论目录不存在，无法提取书籍信息: %s", src_folder)
        return False

    body_files = sorted(src_folder.glob("body_*.json"))
    if not body_files:
        logger.warning("未找到评论 body_*.json，跳过书籍信息提取")
        return False

    merged_book_info = {}
    max_comment_total = 0
    comment_map = {}

    for body_file in body_files:
        try:
            with body_file.open("r", encoding="utf-8") as f:
                body_json = json.load(f)
        except Exception as e:
            logger.warning("读取失败，已跳过 %s: %s", body_file, e)
            continue

        data = body_json.get("data") if isinstance(body_json, dict) else None
        if not isinstance(data, dict):
            continue

        common_list_info = data.get("common_list_info")
        if isinstance(common_list_info, dict):
            total = common_list_info.get("total")
            if isinstance(total, int) and total > max_comment_total:
                max_comment_total = total

        data_list = data.get("data_list")
        if not isinstance(data_list, list):
            continue

        for item in data_list:
            if not isinstance(item, dict):
                continue

            comment = item.get("comment")
            if not isinstance(comment, dict):
                continue

            common = comment.get("common") if isinstance(comment.get("common"), dict) else {}
            expand = comment.get("expand") if isinstance(comment.get("expand"), dict) else {}
            stat = comment.get("stat") if isinstance(comment.get("stat"), dict) else {}

            book_info = expand.get("book_info") if isinstance(expand.get("book_info"), dict) else {}
            reader_schema = book_info.get("reader_schema") if isinstance(book_info.get("reader_schema"), dict) else {}

            candidate_book_info = {
                "book_id": book_info.get("book_id") or expand.get("book_id"),
                "book_name": _pick_text(book_info.get("book_name")) or book_name,
                "author": _pick_text(book_info.get("author")),
                "score": _pick_text(book_info.get("score")) or book_info.get("score"),
                "read_count_text": _pick_text(book_info.get("read_count_text")) or book_info.get("read_count_text"),
                "word_number": _pick_text(reader_schema.get("word_number")) or reader_schema.get("word_number"),
                "tags": _pick_text(book_info.get("tags")) or book_info.get("tags"),
                "creation_status": _pick_text(book_info.get("creation_status")) or book_info.get("creation_status"),
                "serial_count": _pick_text(book_info.get("serial_count")) or book_info.get("serial_count"),
                "abstract": _pick_text(book_info.get("abstract")) or book_info.get("abstract"),
            }
            merged_book_info = _merge_dict_non_empty(merged_book_info, candidate_book_info)

            content = common.get("content") if isinstance(common.get("content"), dict) else {}
            user_info = common.get("user_info") if isinstance(common.get("user_info"), dict) else {}
            base_info = user_info.get("base_info") if isinstance(user_info.get("base_info"), dict) else {}

            comment_id = comment.get("comment_id")
            comment_record = {
                "comment_id": str(comment_id) if comment_id is not None else None,
                "text": _pick_text(content.get("text")) or content.get("text"),
                "create_timestamp": common.get("create_timestamp"),
                "user_name": _pick_text(base_info.get("user_name")) or base_info.get("user_name"),
                "user_id": base_info.get("user_id") or user_info.get("user_id"),
                "digg_count": stat.get("digg_count"),
                "reply_count": stat.get("reply_count"),
                "show_pv": stat.get("show_pv"),
            }

            if comment_record["comment_id"]:
                comment_map[comment_record["comment_id"]] = _merge_dict_non_empty(
                    comment_map.get(comment_record["comment_id"], {}), comment_record
                )

    comments = sorted(
        comment_map.values(),
        key=lambda x: (
            -(x.get("create_timestamp") or 0),
            x.get("comment_id") or "",
        ),
    )

    final_info = {
        "book_id": merged_book_info.get("book_id"),
        "book_name": merged_book_info.get("book_name") or book_name,
        "author": merged_book_info.get("author"),
        "score": merged_book_info.get("score"),
        "read_count_text": merged_book_info.get("read_count_text"),
        "word_number": merged_book_info.get("word_number"),
        "tags": merged_book_info.get("tags"),
        "creation_status": merged_book_info.get("creation_status"),
        "serial_count": merged_book_info.get("serial_count"),
        "abstract": merged_book_info.get("abstract"),
        "comment_total": max_comment_total if max_comment_total else len(comments),
        "comment_count_extracted": len(comments),
        "comments": comments,
    }

    info_dir = Path("data") / "bookInfo"
    info_dir.mkdir(parents=True, exist_ok=True)
    info_file_name = f"{folder_name}_info.json"
    info_path = info_dir / info_file_name
    _save_json(info_path, final_info)
    logger.info("✓ 书籍信息已保存: %s", info_path)
    return True


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
        if not wait_for_ui_change(controller.device, before_search_click, timeout=8):
            time.sleep(1)
        
        # 操作 2: 输入书籍名称
        logger.info(f"\n--- 操作 2: 输入书籍名称 '{book_name}' ---")
        
        # 使用 uiautomator2 输入文本
        controller.device.send_keys(book_name)
        if not wait_for_text_in_any_selector(
            controller.device,
            SEARCH_INPUT_SELECTORS,
            expected_text=book_name,
            timeout=5,
        ):
            logger.warning("首次输入未校验通过，重试输入一次...")
            controller.device.send_keys(book_name)

        if not wait_for_text_in_any_selector(
            controller.device,
            SEARCH_INPUT_SELECTORS,
            expected_text=book_name,
            timeout=5,
        ):
            logger.error("✗ 搜索框内容校验失败，终止点击搜索")
            return False

        logger.info("✓ 书籍名称输入并校验完成")
        
        # 操作 3: 点击搜索按钮
        logger.info("\n--- 操作 3: 点击搜索按钮 ---")
        time.sleep(0.3)  # 输入已校验，仅做短暂稳定等待
        
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

        # 操作 6: 等待评论接口触发并导出提取
        logger.info("\n--- 操作 6: 导出 Charles 并提取评论接口文件 ---")
        time.sleep(3)
        if not export_and_extract_comment_files(logger, book_name):
            logger.error("导出或提取评论文件失败")
            return False

        # 操作 7: 提取书籍信息并落盘
        logger.info("\n--- 操作 7: 提取书籍信息并保存 ---")
        extract_book_info_from_comment_files(logger, book_name)

        # 操作 8: 回退3次，返回主页面
        logger.info("\n--- 操作 8: 回退至主页面 ---")
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
