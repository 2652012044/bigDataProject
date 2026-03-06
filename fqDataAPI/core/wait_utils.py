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
