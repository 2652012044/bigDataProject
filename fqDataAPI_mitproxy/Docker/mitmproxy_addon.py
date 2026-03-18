import json
import os
import threading
import time
from typing import Any, Dict, List

from mitmproxy import http


CONTROL_HOST = "mitm.capture"
DEFAULT_CAPTURE_HOSTS = "api5-normal-sinfonlineb.fqnovel.com"


class CaptureController:
    def __init__(self) -> None:
        self._entries: List[Dict[str, Any]] = []
        self._lock = threading.Lock()
        self._debug_events = os.getenv("MITM_DEBUG_EVENTS", "0") == "1"
        raw_hosts = os.getenv("MITM_CAPTURE_HOSTS", DEFAULT_CAPTURE_HOSTS)
        self._capture_hosts = {
            host.strip().lower()
            for host in raw_hosts.split(",")
            if host.strip()
        }

    def _append_entry(self, entry: Dict[str, Any]) -> None:
        with self._lock:
            self._entries.append(entry)

    def _record_debug_event(self, event_type: str, flow: http.HTTPFlow, detail: str = "") -> None:
        if not self._debug_events:
            return

        host = flow.request.pretty_host if flow.request else "unknown"
        if host != CONTROL_HOST and not self._should_capture(host):
            return

        entry = {
            "event_type": event_type,
            "host": host,
            "method": flow.request.method if flow.request else None,
            "path": flow.request.path if flow.request else None,
            "url": flow.request.pretty_url if flow.request else None,
            "detail": detail,
            "times": {
                "start": time.time(),
                "end": time.time(),
            },
        }
        self._append_entry(entry)

    def _should_capture(self, host: str) -> bool:
        if not self._capture_hosts:
            return True
        return host.lower() in self._capture_hosts

    def request(self, flow: http.HTTPFlow) -> None:
        if flow.request.pretty_host != CONTROL_HOST:
            self._record_debug_event("request_start", flow)
            return

        if flow.request.path == "/session/clear":
            with self._lock:
                self._entries.clear()
            flow.response = http.Response.make(
                200,
                json.dumps({"ok": True, "sessions": 0}).encode("utf-8"),
                {"Content-Type": "application/json; charset=utf-8"},
            )
            return

        if flow.request.path == "/session/export-json":
            try:
                with self._lock:
                    payload = {"sessions": list(self._entries)}
                body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
                flow.response = http.Response.make(
                    200,
                    body,
                    {"Content-Type": "application/json; charset=utf-8"},
                )
            except Exception as exc:
                flow.response = http.Response.make(
                    500,
                    json.dumps({"ok": False, "error": str(exc)}).encode("utf-8"),
                    {"Content-Type": "application/json; charset=utf-8"},
                )
            return

        flow.response = http.Response.make(
            404,
            json.dumps({"ok": False, "message": "unknown control path"}).encode("utf-8"),
            {"Content-Type": "application/json; charset=utf-8"},
        )

    def response(self, flow: http.HTTPFlow) -> None:
        host = flow.request.pretty_host
        if host == CONTROL_HOST:
            return

        # 仅记录目标主机，其他流量仍可透传但不落盘。
        if not self._should_capture(host):
            return

        start_ts = getattr(flow.request, "timestamp_start", None)
        if start_ts is None:
            start_ts = getattr(flow, "timestamp_start", 0)

        end_ts = getattr(flow.response, "timestamp_end", None)
        if end_ts is None:
            end_ts = getattr(flow.response, "timestamp_start", None)
        if end_ts is None:
            end_ts = getattr(flow, "timestamp_start", 0)

        response_text = ""
        try:
            response_text = flow.response.get_text(strict=False)
        except Exception:
            response_text = ""

        entry = {
            "scheme": flow.request.scheme,
            "host": flow.request.pretty_host,
            "port": flow.request.port,
            "method": flow.request.method,
            "path": flow.request.path,
            "url": flow.request.pretty_url,
            "request": {
                "headers": dict(flow.request.headers.items(multi=True)),
                "body": {
                    "text": flow.request.get_text(strict=False) if flow.request.raw_content else "",
                },
            },
            "response": {
                "status_code": flow.response.status_code,
                "reason": flow.response.reason,
                "headers": dict(flow.response.headers.items(multi=True)),
                "body": {
                    "text": response_text,
                },
            },
            "times": {
                "start": start_ts,
                "end": end_ts,
            },
        }

        self._append_entry(entry)

    def error(self, flow: http.HTTPFlow) -> None:
        # 记录连接/握手失败等无法进入 response 的场景。
        err = flow.error.msg if flow.error else "unknown error"
        self._record_debug_event("flow_error", flow, detail=err)


addons = [CaptureController()]