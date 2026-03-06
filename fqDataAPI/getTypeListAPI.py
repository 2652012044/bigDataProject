"""Run getTypeList automation, export Charles session, and extract latest new_category entry."""

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

import requests

# Keep same import style as existing scripts in this workspace.
sys.path.insert(0, str(Path(__file__).parent))

from core.logger import setup_logger
from getTypeList import main as run_get_type_list


CHARLES_CLEAR_URL = "http://control.charles/session/clear"
CHARLES_TIMEOUT_SECONDS = 10


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run automation then export Charles session and extract latest target API entry."
    )
    parser.add_argument(
        "--charles-export-url",
        default="http://control.charles/session/export-json",
        help="Charles Web Interface export JSON URL",
    )
    parser.add_argument(
        "--target-host",
        default="api5-normal-sinfonlineb.fqnovel.com",
        help="Target host for filtering",
    )
    parser.add_argument(
        "--target-path",
        default="/reading/bookapi/new_category/front/v:version/",
        help="Target path for filtering",
    )
    parser.add_argument(
        "--output-dir",
        default="data",
        help="Directory to save exported and extracted files",
    )
    parser.add_argument(
        "--wait-seconds",
        type=float,
        default=2.0,
        help="Wait time after automation and before export",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="HTTP timeout when requesting Charles export",
    )
    return parser.parse_args()


def normalize_entries(export_json: Any) -> List[Dict[str, Any]]:
    """Normalize possible Charles JSON formats to a list of entries."""
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


def get_entry_start_ts(entry: Dict[str, Any]) -> str:
    """Get comparable start timestamp string for sorting."""
    times = entry.get("times")
    if isinstance(times, dict):
        start = times.get("start")
        if isinstance(start, str):
            return start
    return ""


def export_charles_json(url: str, timeout: int) -> Any:
    """Call Charles web interface export endpoint and return parsed JSON."""
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    return response.json()


def clear_charles_session(logger) -> bool:
    """Clear existing Charles captured sessions before automation starts."""
    try:
        requests.get(CHARLES_CLEAR_URL, timeout=CHARLES_TIMEOUT_SECONDS)
        logger.info("✓ Charles 抓包已清空")
        return True
    except Exception as e:
        logger.warning("清空 Charles 抓包失败，继续执行: %s", e)
        return False


def filter_target_entries(
    entries: List[Dict[str, Any]], target_host: str, target_path: str
) -> List[Dict[str, Any]]:
    """Filter by exact host and path prefix (to tolerate version path variants)."""
    path_prefix = "/reading/bookapi/new_category/front/"
    matched: List[Dict[str, Any]] = []

    for entry in entries:
        host = entry.get("host")
        path = entry.get("path")

        if host != target_host or not isinstance(path, str):
            continue

        if path == target_path or path.startswith(path_prefix):
            matched.append(entry)

    return matched


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def extract_type_list(body_json: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract all category tags into a flat list for downstream usage."""
    result: List[Dict[str, Any]] = []

    data_obj = body_json.get("data") if isinstance(body_json, dict) else None
    if not isinstance(data_obj, dict):
        return result

    tab_data = data_obj.get("category_tab_data")
    if not isinstance(tab_data, dict):
        return result

    tab_name = tab_data.get("tab_name")
    category_tab = tab_data.get("category_tab")
    cell_data = tab_data.get("cell_data")

    if not isinstance(cell_data, list):
        return result

    for cell in cell_data:
        if not isinstance(cell, dict):
            continue

        cell_name = cell.get("cell_name")
        show_type = cell.get("show_type")
        atoms = cell.get("atom_data")
        if not isinstance(atoms, list):
            continue

        for atom in atoms:
            if not isinstance(atom, dict):
                continue

            category_data = atom.get("category_data")
            if not isinstance(category_data, dict):
                continue

            result.append(
                {
                    "tab_name": tab_name,
                    "category_tab": category_tab,
                    "cell_name": cell_name,
                    "show_type": show_type,
                    "name": category_data.get("name"),
                    "category_id": category_data.get("category_id"),
                    "category_landpage_url": category_data.get("category_landpage_url"),
                    "style": category_data.get("style"),
                    "pic_url": category_data.get("pic_url"),
                }
            )

    return result


def main() -> int:
    args = parse_args()
    logger = setup_logger("get_type_list_api")

    logger.info("=" * 70)
    logger.info("Step 0/3: Clear Charles session")
    logger.info("=" * 70)
    clear_charles_session(logger)

    logger.info("=" * 70)
    logger.info("Step 1/3: Run getTypeList automation")
    logger.info("=" * 70)
    ok = run_get_type_list()
    if not ok:
        logger.error("Automation failed, abort export")
        return 1

    if args.wait_seconds > 0:
        logger.info("Wait %.1f seconds before export", args.wait_seconds)
        time.sleep(args.wait_seconds)

    logger.info("=" * 70)
    logger.info("Step 2/3: Export Charles JSON")
    logger.info("=" * 70)
    try:
        export_json = export_charles_json(args.charles_export_url, args.timeout)
    except Exception as exc:
        logger.error("Charles export failed: %s", exc)
        return 1

    output_dir = Path(args.output_dir)
    export_path = output_dir / "charles_export_filtered.json"
    save_json(export_path, export_json)
    logger.info("Export saved: %s", export_path)

    logger.info("=" * 70)
    logger.info("Step 3/3: Extract latest target entry")
    logger.info("=" * 70)
    entries = normalize_entries(export_json)
    logger.info("Total entries in export: %d", len(entries))

    matched = filter_target_entries(entries, args.target_host, args.target_path)
    logger.info("Matched target entries: %d", len(matched))

    if not matched:
        logger.error("No matched entry for host=%s path=%s", args.target_host, args.target_path)
        return 2

    matched_sorted = sorted(matched, key=get_entry_start_ts)
    last_entry = matched_sorted[-1]

    latest_entry_path = output_dir / "new_category_latest_entry.json"
    save_json(latest_entry_path, last_entry)

    # Save only response body text for direct downstream usage.
    response_obj = last_entry.get("response", {}) if isinstance(last_entry, dict) else {}
    body_obj = response_obj.get("body", {}) if isinstance(response_obj, dict) else {}
    body_text = body_obj.get("text") if isinstance(body_obj, dict) else None

    latest_body_path = output_dir / "new_category_latest_body.json"
    if isinstance(body_text, str) and body_text.strip():
        try:
            body_json = json.loads(body_text)
            save_json(latest_body_path, body_json)
            logger.info("Latest response body parsed and saved: %s", latest_body_path)

            type_list = extract_type_list(body_json)
            type_list_path = output_dir / "TypeList.json"
            save_json(type_list_path, type_list)
            logger.info("Extracted %d tags and saved: %s", len(type_list), type_list_path)
        except Exception:
            latest_body_path = output_dir / "new_category_latest_body.txt"
            latest_body_path.write_text(body_text, encoding="utf-8")
            logger.info("Latest response body saved as text: %s", latest_body_path)
    else:
        logger.warning("Latest entry has no response.body.text")

    logger.info("Latest entry saved: %s", latest_entry_path)
    logger.info("Done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
