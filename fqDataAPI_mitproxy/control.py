"""总控面板 — 显示 mitmproxy 代理和逍遥模拟器的运行状态及连接关系

运行方式:
    python control.py
"""

import json
import os
import socket
import subprocess
import sys
import threading
import time
import tkinter as tk
import tkinter.filedialog
import tkinter.messagebox
import tkinter.simpledialog
import urllib.request
from datetime import datetime

# ─────────────────────────── 通用配置 ───────────────────────────

REFRESH_INTERVAL_MS = 5000          # 自动刷新间隔（毫秒）
HOST_IP             = "172.19.32.1" # 宿主机对模拟器可见的 IP
BASE_PROXY_PORT     = 8080          # 分配代理时的默认起始端口
ADDON_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "Docker", "mitmproxy_addon.py",
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ─────────────────────────── 可执行作业定义 ───────────────────────────

TASK_DEFS = {
    "getCategoryListAPI":   {"label": "获取分类列表", "param_key": None,          "script": "getCategoryListAPI.py"},
    "searchbook":           {"label": "搜索书籍",     "param_key": "book_name",   "script": "searchbook.py"},
    "getBookListByTypeAPI": {"label": "获取类型书单", "param_key": "type",        "script": "getBookListByTypeAPI.py",
                             "extra_args": [{"key": "scroll_timeout_seconds", "hint": "滚动超时秒数(默认180)"}]},
    "getUserAPI":           {"label": "获取用户信息", "param_key": "author_name", "script": "getUserAPI.py"},
}
TASK_KEYS    = list(TASK_DEFS.keys())
LABEL_TO_KEY = {v["label"]: k for k, v in TASK_DEFS.items()}

PROGRESS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "progress")


def _make_job_label(configs: list) -> str:
    """从作业配置列表生成简短的内容标签（用于进度文件名）。"""
    if not configs:
        return "未知作业"
    seen, seen_set = [], set()
    for c in configs:
        lbl = TASK_DEFS.get(c.get("task_key", ""), {}).get("label", c.get("task_key", ""))
        if lbl not in seen_set:
            seen_set.add(lbl)
            seen.append(lbl)
    label = "_".join(seen)
    for ch in '\\/:*?"<>|':
        label = label.replace(ch, "")
    return label or "未知作业"


def _detect_via_memuc() -> list:
    """通过 memuc list -r 获取正在运行的逍遥模拟器实例。"""
    try:
        r = subprocess.run(
            ["memuc", "list", "-r"],
            capture_output=True, text=True, timeout=5,
        )
        if r.returncode != 0 or not r.stdout.strip():
            return []
        result = []
        for line in r.stdout.strip().splitlines():
            parts = line.strip().split(",")
            if not parts or not parts[0].isdigit():
                continue
            idx = int(parts[0])
            serial = f"127.0.0.1:{21503 + idx * 10}"
            result.append({
                "name":            f"实例 {idx}",
                "emulator_serial": serial,
                "instance_idx":    idx,
                "proxy_port":      None,
                "expected_proxy":  None,
            })
        return sorted(result, key=lambda x: x["instance_idx"])
    except Exception:
        return []


def _detect_via_adb() -> list:
    """通过 adb devices 端口号推断逍遥模拟器实例（MEmu 端口范围 21503~22000）。"""
    try:
        r = subprocess.run(
            ["adb", "devices"], capture_output=True, text=True, timeout=5
        )
        result = []
        for line in r.stdout.strip().splitlines()[1:]:
            if "\t" not in line:
                continue
            serial, _ = line.split("\t", 1)
            serial = serial.strip()
            if not serial.startswith("127.0.0.1:"):
                continue
            try:
                port = int(serial.split(":")[1])
            except ValueError:
                continue
            if 21500 <= port <= 22000:
                idx = round((port - 21503) / 10)
                result.append({
                    "name":            f"实例 {idx}",
                    "emulator_serial": serial,
                    "instance_idx":    idx,
                    "proxy_port":      None,
                    "expected_proxy":  None,
                })
        return sorted(result, key=lambda x: x["instance_idx"])
    except Exception:
        return []


def detect_memu_instances() -> list:
    """
    检测当前运行的逍遥模拟器实例。
    优先用 memuc list -r，失败则从 adb devices 端口号推断。
    返回 slot 字典列表，proxy_port 默认 None（未分配代理）。
    """
    instances = _detect_via_memuc()
    return instances if instances else _detect_via_adb()


# 运行期 Slot 列表（启动时及重新扫描时由 detect_memu_instances 填充）
SLOTS: list = []

# ─────────────────────────── 颜色主题 ───────────────────────────

BG      = "#1e1e2e"
CARD    = "#2a2a3e"
ITEM    = "#313244"
HDR     = "#181825"
GREEN   = "#50fa7b"
RED     = "#ff5555"
YELLOW  = "#f1fa8c"
BLUE    = "#89b4fa"
TEXT    = "#cdd6f4"
SUB     = "#6c7086"
BORDER  = "#45475a"

# ─────────────────────────── 状态检测（后台线程调用）───────────────────────────

def _port_open(port: int) -> bool:
    """检查本机端口是否正在监听。"""
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=1.0):
            return True
    except OSError:
        return False


def _addon_ok(port: int) -> bool:
    """通过代理请求 mitmproxy addon 控制接口，验证 addon 是否正常。"""
    try:
        proxy_url = f"http://127.0.0.1:{port}"
        handler = urllib.request.ProxyHandler({"http": proxy_url, "https": proxy_url})
        opener = urllib.request.build_opener(handler)
        opener.addheaders = [("User-Agent", "control-panel/1.0")]
        resp = opener.open("http://mitm.capture/session/export-json", timeout=3)
        return resp.status == 200
    except Exception:
        return False


def _adb_devices() -> dict:
    """返回 {serial: status} 的已连接 ADB 设备字典。"""
    try:
        r = subprocess.run(
            ["adb", "devices"], capture_output=True, text=True, timeout=5
        )
        out = {}
        for line in r.stdout.strip().splitlines()[1:]:
            if "\t" in line:
                serial, status = line.split("\t", 1)
                out[serial.strip()] = status.strip()
        return out
    except Exception:
        return {}


def _emu_proxy(serial: str) -> str:
    """读取模拟器的 http_proxy 全局设置值。"""
    try:
        r = subprocess.run(
            ["adb", "-s", serial, "shell",
             "settings", "get", "global", "http_proxy"],
            capture_output=True, text=True, timeout=5,
        )
        return r.stdout.strip()
    except Exception:
        return ""


def collect_status():
    """采集全部 SLOT 的运行状态，返回状态字典列表。"""
    devs = _adb_devices()
    result = []
    for s in SLOTS:
        port   = s["proxy_port"]       # None 表示当前 slot 尚未分配代理
        serial = s["emulator_serial"]

        if port is not None:
            port_up = _port_open(port)
            addon   = _addon_ok(port) if port_up else False
        else:
            port_up = False
            addon   = False

        emu_st      = devs.get(serial, "离线")
        emu_ok      = (emu_st == "device")
        proxy_val   = _emu_proxy(serial) if emu_ok else ""
        exp         = s.get("expected_proxy")
        proxy_match = bool(exp and proxy_val == exp)

        result.append({
            "name":           s["name"],
            "proxy_port":     port,
            "proxy_assigned": port is not None,
            "port_up":        port_up,
            "addon":          addon,
            "serial":         serial,
            "emu_ok":         emu_ok,
            "emu_st":         emu_st,
            "proxy_val":      proxy_val,
            "proxy_match":    proxy_match,
            "expected_proxy": exp,
            "all_ok": port is not None and port_up and addon and emu_ok and proxy_match,
        })
    return result


def _kill_on_port(port: int) -> None:
    """尝试强制终止正在监听指定端口的进程（Windows）。"""
    try:
        r = subprocess.run(
            ["netstat", "-ano"],
            capture_output=True, text=True, timeout=5,
        )
        for line in r.stdout.splitlines():
            if f":{port} " in line and "LISTENING" in line:
                parts = line.split()
                pid = parts[-1]
                subprocess.run(
                    ["taskkill", "/F", "/PID", pid],
                    capture_output=True, timeout=5,
                )
    except Exception:
        pass


# ─────────────────────────── 作业运行器 ───────────────────────────

class RunnerState:
    IDLE    = "idle"
    RUNNING = "running"
    PAUSED  = "paused"
    DONE    = "done"
    STOPPED = "stopped"


class JobRunner:
    """顺序执行作业单元的后台运行器。"""

    MAX_LOG_LINES = 5000   # 日志缓冲区最大行数

    def __init__(self, serial: str, units: list, proxy_port: "int | None" = None,
                 on_update=None, on_log=None,
                 job_id: str = "", job_label: str = "", slot_name: str = "",
                 configs: "list | None" = None, start_from: int = 0):
        """
        units:      [{"task_key": str, "param": str | None}, ...]
        on_update:  callable(runner)，每次状态变化时从工作线程触发。
        on_log:     callable(runner, text)，有新日志行时从工作线程触发。
        job_id:     作业唯一编号（yyyymmdd_HHMMSS），用于进度文件命名。
        job_label:  作业内容标签，与 job_id 共同构成文件名。
        slot_name:  所属模拟器槽位名称，记录到进度文件。
        configs:    原始作业配置列表，记录到进度文件以便恢复。
        start_from: 从第 N 个单元开始执行（恢复未完成作业时使用）。
        """
        self.serial     = serial
        self.proxy_port = proxy_port
        self.units      = list(units)
        self.total      = len(units)
        self.current    = start_from
        self.state      = RunnerState.IDLE
        self.on_update  = on_update
        self.on_log     = on_log
        self.job_id     = job_id
        self.job_label  = job_label
        self.slot_name  = slot_name
        self.configs    = configs if configs is not None else []
        self.log_lines: list[str] = []  # 日志缓冲区
        self._log_lock = threading.Lock()
        self._stop_event  = threading.Event()
        self._pause_event = threading.Event()
        self._pause_event.set()   # 未暂停时置位
        self._thread   = None

    # ── 控制接口 ──

    def start(self):
        if self.state in (RunnerState.RUNNING, RunnerState.DONE):
            return
        if self.state == RunnerState.PAUSED:
            self.resume()
            return
        self._stop_event.clear()
        self._pause_event.set()
        self.state   = RunnerState.RUNNING
        self._notify()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def pause(self):
        if self.state != RunnerState.RUNNING:
            return
        self._pause_event.clear()
        self.state = RunnerState.PAUSED
        self._notify()

    def resume(self):
        if self.state != RunnerState.PAUSED:
            return
        self.state = RunnerState.RUNNING
        self._pause_event.set()
        self._notify()

    def stop(self):
        self._stop_event.set()
        self._pause_event.set()   # 解除暂停让线程可以检查停止标志
        if self.state not in (RunnerState.DONE, RunnerState.STOPPED):
            self.state = RunnerState.STOPPED
            self._notify()

    # ── 内部 ──

    def _notify(self):
        if self.on_update:
            try:
                self.on_update(self)
            except Exception:
                pass

    def save_progress(self):
        """将当前作业进度保存到 progress/{job_id}_{job_label}.json。"""
        if not self.job_id:
            return
        try:
            os.makedirs(PROGRESS_DIR, exist_ok=True)
            filename = f"{self.job_id}_{self.job_label}.json"
            path = os.path.join(PROGRESS_DIR, filename)
            data = {
                "job_id":     self.job_id,
                "job_label":  self.job_label,
                "slot_name":  self.slot_name,
                "serial":     self.serial,
                "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "status":     self.state,
                "total":      self.total,
                "completed":  self.current,
                "units":      self.units,
                "configs":    self.configs,
            }
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _run(self):
        while self.current < self.total:
            if self._stop_event.is_set():
                break
            self._pause_event.wait()
            if self._stop_event.is_set():
                break
            self._execute_unit(self.units[self.current])
            self.current += 1
            self.save_progress()   # 每完成一个单元即保存进度
            self._notify()
        if not self._stop_event.is_set():
            self.state = RunnerState.DONE
            self.save_progress()   # 全部完成时保存最终状态
            self._notify()
        else:
            self.save_progress()   # 停止时保存当前进度

    # restartFqNovel.py 路径（与各任务脚本同目录）
    _RESTART_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "restartFqNovel.py")

    def _append_log(self, text: str):
        """追加日志行到缓冲区并触发回调。"""
        with self._log_lock:
            self.log_lines.append(text)
            if len(self.log_lines) > self.MAX_LOG_LINES:
                self.log_lines = self.log_lines[-self.MAX_LOG_LINES:]
        if self.on_log:
            try:
                self.on_log(self, text)
            except Exception:
                pass

    # 子进程输出中被视为"任务失败"的标志字符串（大小写不敏感）
    _ERROR_PATTERNS = ("[error]", "traceback (most recent")

    def _run_cmd(self, cmd: list, env: dict, timeout: int = 600) -> int:
        """执行子进程，实时捕获 stdout/stderr 到日志缓冲区。
        返回值：退出码（超时返回 -1；检测到严重错误标志时返回 -2）。
        """
        self._append_log(f"$ {' '.join(cmd)}")
        run_env = dict(env)
        run_env["PYTHONIOENCODING"] = "utf-8"
        run_env["PYTHONUTF8"] = "1"
        run_env["PYTHONUNBUFFERED"] = "1"   # 禁用子进程输出缓冲，确保实时刷新
        try:
            proc = subprocess.Popen(
                cmd, env=run_env,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                encoding="utf-8", errors="replace", bufsize=1,
                cwd=BASE_DIR,
            )
        except Exception as e:
            self._append_log(f"[ERROR] 启动进程失败: {e}")
            return -1

        deadline = time.time() + timeout
        error_detected = False
        try:
            for line in proc.stdout:
                stripped = line.rstrip("\n")
                self._append_log(stripped)
                lower = stripped.lower()
                if any(p in lower for p in self._ERROR_PATTERNS):
                    error_detected = True
                if time.time() > deadline:
                    proc.kill()
                    self._append_log("[TIMEOUT] 超时已终止")
                    return -1
            # 等待进程完全退出，最多给 10 秒（stdout 关闭后进程应当已退出）
            proc.wait(timeout=min(10, max(1, deadline - time.time())))
        except subprocess.TimeoutExpired:
            proc.kill()
            self._append_log("[TIMEOUT] 超时已终止")
            return -1
        except Exception as e:
            proc.kill()
            self._append_log(f"[ERROR] {e}")
            return -1

        rc = proc.returncode
        # 退出码非零 → 直接返回
        if rc != 0:
            return rc
        # 退出码为 0 但输出中含有严重错误标志 → 视为失败
        if error_detected:
            self._append_log("[JobRunner] 检测到 [ERROR] 输出，视为任务失败")
            return -2
        return 0

    def _restart_app(self):
        """调用 restartFqNovel.py 重启番茄小说。"""
        self._append_log(f"[JobRunner] ⟳ 重启番茄小说 (serial={self.serial})")
        env = os.environ.copy()
        env["ANDROID_SERIAL"] = self.serial
        rc = self._run_cmd(
            [
                sys.executable, self._RESTART_SCRIPT,
                "--serial", self.serial,
                "--wait", "300",
            ],
            env=env, timeout=360,
        )
        if rc != 0:
            self._append_log(f"[JobRunner] 重启 App 失败 (rc={rc})")

    def _execute_unit(self, unit: dict):
        task_key = unit["task_key"]
        param    = unit.get("param")
        tdef     = TASK_DEFS.get(task_key)
        if not tdef:
            return
        script_path = os.path.join(BASE_DIR, tdef["script"])
        env         = os.environ.copy()
        env["ANDROID_SERIAL"] = self.serial
        if self.proxy_port is not None:
            env["MITM_PROXY_PORT"] = str(self.proxy_port)
        cmd = [sys.executable, script_path]
        if param is not None:
            if isinstance(param, list):
                cmd.extend(str(a) for a in param)
            else:
                cmd.append(str(param))

        self._append_log(f"\n{'─'*40}")
        self._append_log(f"[{self.current+1}/{self.total}] {task_key}({param})")

        # 失败不跳过：持续重试直到成功，或用户手动停止队列。
        attempt = 1
        while not self._stop_event.is_set():
            if attempt > 1:
                self._append_log(f"[JobRunner] 第 {attempt} 次尝试 {task_key}({param})")

            rc = self._run_cmd(cmd, env, timeout=600)
            if rc == 0:
                if attempt > 1:
                    self._append_log(f"[JobRunner] {task_key} 在第 {attempt} 次尝试成功")
                return

            self._append_log(f"[JobRunner] 返回码 {rc}，准备重启 App 后继续重试")
            self._restart_app()
            if self._stop_event.is_set():
                return

            # 冷启动阶段给足预热时间，避免刚启动就立刻执行导致连续失败。
            warmup_seconds = min(30, 8 + attempt * 2)
            self._append_log(f"[JobRunner] 等待 App 稳定 {warmup_seconds}s 后重试")
            for _ in range(warmup_seconds):
                if self._stop_event.is_set():
                    return
                time.sleep(1)

            attempt += 1


# ─────────────────────────── GUI ───────────────────────────

class ControlPanel(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("番茄小说采集 — 总控面板")
        self.configure(bg=BG)
        self.resizable(True, True)
        self.minsize(680, 400)

        self._refreshing    = False
        self._job           = None
        self._cards         = []
        self._procs: dict   = {}              # slot_idx → subprocess.Popen
        self._last_statuses = []
        self._body_frame    = None            # 可重建的卡片容器
        self._max_canvas_h  = 400
        self._runners: dict        = {}          # slot_idx → JobRunner
        self._job_configs: dict    = {}          # slot_idx → [{task_key, params}]
        self._log_windows: dict    = {}          # slot_idx → LogWindow
        self._job_ids: dict        = {}          # slot_idx → job_id（恢复未完成作业时保存）
        self._job_resume_from: dict = {}         # slot_idx → int（从第N个单元继续）

        # 启动时清理残留的 mitmdump 进程
        self._kill_all_proxies(silent=True)

        # 初始扫描逍遥模拟器
        global SLOTS
        SLOTS = detect_memu_instances()
        self._last_statuses = [None] * len(SLOTS)

        self._build_ui()

        # 拦截关闭事件，关闭前清理代理
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._trigger_refresh()

    # ────── 构建界面 ──────

    def _build_ui(self):
        self._build_header()
        self._build_body()
        self._build_footer()

    def _build_header(self):
        h = tk.Frame(self, bg=HDR, pady=10)
        h.pack(fill="x")
        tk.Label(
            h,
            text="🎛  番茄小说采集  —  总控面板",
            font=("Microsoft YaHei UI", 13, "bold"),
            bg=HDR, fg=TEXT,
        ).pack(side="left", padx=16)
        self._hdr_right = tk.Label(
            h, text="",
            font=("Microsoft YaHei UI", 9),
            bg=HDR, fg=SUB,
        )
        self._hdr_right.pack(side="right", padx=20)
        tk.Button(
            h, text="🔍 扫描模拟器",
            font=("Microsoft YaHei UI", 9),
            bg=ITEM, fg=BLUE,
            activebackground=BORDER, activeforeground=TEXT,
            relief="flat", padx=10, pady=3, cursor="hand2",
            command=self._rescan_emulators,
        ).pack(side="right", padx=(0, 8))

        # ── 工具栏（参数提取） ──
        toolbar = tk.Frame(self, bg=CARD, pady=5)
        toolbar.pack(fill="x")
        tk.Label(
            toolbar, text="参数提取:",
            font=("Microsoft YaHei UI", 9), bg=CARD, fg=SUB,
        ).pack(side="left", padx=(16, 6))
        for text, cmd in [
            ("📂 分类提取",  self._extract_categories),
            ("📖 书名提取",  self._extract_books),
            ("👤 作者提取",  self._extract_authors),
        ]:
            tk.Button(
                toolbar, text=text,
                font=("Microsoft YaHei UI", 9),
                bg=ITEM, fg=TEXT,
                activebackground=BORDER, activeforeground=TEXT,
                relief="flat", padx=10, pady=3, cursor="hand2",
                command=cmd,
            ).pack(side="left", padx=(0, 6))

    def _build_body(self):
        self._max_canvas_h = int(self.winfo_screenheight() * 0.85) - 110

        container = tk.Frame(self, bg=BG)
        container.pack(fill="both", expand=True)

        self._canvas = tk.Canvas(
            container, bg=BG, bd=0, highlightthickness=0
        )
        scrollbar = tk.Scrollbar(
            container, orient="vertical", command=self._canvas.yview
        )
        self._canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)

        self._body_frame = tk.Frame(self._canvas, bg=BG, padx=14, pady=8)
        self._body_id = self._canvas.create_window(
            (0, 0), window=self._body_frame, anchor="nw"
        )

        self._fill_cards()

        self._body_frame.bind(
            "<Configure>",
            lambda e: self._canvas.configure(
                scrollregion=self._canvas.bbox("all")
            ),
        )
        # 让 canvas 宽度跟随 body
        self._canvas.bind(
            "<Configure>",
            lambda e: self._canvas.itemconfig(self._body_id, width=e.width),
        )
        # 鼠标滚轮支持
        self._canvas.bind_all("<MouseWheel>",
            lambda e: self._canvas.yview_scroll(-1 * (e.delta // 120), "units")
        )

    def _fill_cards(self):
        """清除并重建所有卡片（初始化及重新扫描后调用）。"""
        for widget in self._body_frame.winfo_children():
            widget.destroy()
        self._cards.clear()

        if not SLOTS:
            tk.Label(
                self._body_frame,
                text="未检测到正在运行的逍遥模拟器\n请启动模拟器后点击「🔍 扫描模拟器」",
                font=("Microsoft YaHei UI", 11),
                bg=BG, fg=SUB, justify="center",
            ).pack(pady=40)
            return

        for i, slot in enumerate(SLOTS):
            w = self._make_card(self._body_frame, slot, i)
            w["outer"].pack(fill="x", pady=5)
            self._cards.append(w)

    def _build_footer(self):
        f = tk.Frame(self, bg=HDR, pady=7)
        f.pack(fill="x", side="bottom")
        self._foot_time = tk.Label(
            f, text="尚未刷新",
            font=("Consolas", 9), bg=HDR, fg=SUB,
        )
        self._foot_time.pack(side="left", padx=18)
        tk.Button(
            f, text="立即刷新",
            font=("Microsoft YaHei UI", 9),
            bg=ITEM, fg=TEXT,
            activebackground=BORDER, activeforeground=TEXT,
            relief="flat", padx=12, pady=3, cursor="hand2",
            command=self._trigger_refresh,
        ).pack(side="right", padx=18)

    # ────── 卡片构建 ──────

    def _make_card(self, parent, slot: dict, idx: int) -> dict:
        """构建单个实例卡片，返回需要动态更新的控件字典。"""

        # 1px 边框（用外层 Frame 颜色模拟）
        outer = tk.Frame(parent, bg=BORDER, padx=1, pady=1)
        card  = tk.Frame(outer, bg=CARD, padx=14, pady=8)
        card.pack(fill="both")

        # ── 标题行 ──
        title_row = tk.Frame(card, bg=CARD)
        title_row.pack(fill="x", pady=(0, 6))
        tk.Label(
            title_row,
            text=f"◈  {slot['name']}",
            font=("Microsoft YaHei UI", 11, "bold"),
            bg=CARD, fg=TEXT,
        ).pack(side="left")
        badge = tk.Label(
            title_row, text="● 检测中",
            font=("Microsoft YaHei UI", 8),
            bg=CARD, fg=YELLOW,
        )
        badge.pack(side="right")
        _init_text  = "分配代理" if slot["proxy_port"] is None else "开启代理"
        _init_color = BLUE      if slot["proxy_port"] is None else GREEN
        toggle_btn = tk.Button(
            title_row,
            text=_init_text,
            font=("Microsoft YaHei UI", 8),
            bg=ITEM, fg=_init_color,
            activebackground=BORDER, activeforeground=TEXT,
            relief="flat", padx=10, pady=2, cursor="hand2",
            command=lambda i=idx: self._toggle_proxy(i),
        )
        toggle_btn.pack(side="right", padx=(0, 8))

        # ── 三列内容行：代理框 | 箭头 | 模拟器框 ──
        content = tk.Frame(card, bg=CARD)
        content.pack(fill="x")
        content.grid_columnconfigure(0, weight=4, minsize=200)
        content.grid_columnconfigure(1, weight=1, minsize=96)
        content.grid_columnconfigure(2, weight=4, minsize=210)
        content.grid_rowconfigure(0, weight=1)

        # 代理框
        proxy_box, proxy_w = self._make_proxy_box(content, slot["proxy_port"])
        proxy_box.grid(row=0, column=0, sticky="nsew")

        # 箭头列（内部用 place 居中）
        arrow_col = tk.Frame(content, bg=CARD)
        arrow_col.grid(row=0, column=1, sticky="nsew")
        arrow_inner = tk.Frame(arrow_col, bg=CARD)
        arrow_inner.place(relx=0.5, rely=0.5, anchor="center")
        arrow_lbl = tk.Label(
            arrow_inner, text="──►",
            font=("Consolas", 11), bg=CARD, fg=SUB,
        )
        arrow_lbl.pack()
        link_lbl = tk.Label(
            arrow_inner, text="",
            font=("Microsoft YaHei UI", 7),
            bg=CARD, fg=SUB,
            wraplength=90, justify="center",
        )
        link_lbl.pack(pady=(2, 0))

        # 模拟器框
        emu_box, emu_w = self._make_emu_box(content, slot)
        emu_box.grid(row=0, column=2, sticky="nsew")

        # ── 作业行（初始不显示，由 _apply_status 按需 pack）──
        job_sep = tk.Frame(card, bg=BORDER, height=1)
        job_row = tk.Frame(card, bg=CARD, pady=4)

        # 左：配置按钮 + 摘要
        job_cfg_btn = tk.Button(
            job_row, text="⚙ 作业",
            font=("Microsoft YaHei UI", 8),
            bg=ITEM, fg=SUB,
            activebackground=BORDER, activeforeground=TEXT,
            relief="flat", padx=8, pady=2, cursor="hand2",
            command=lambda i=idx: self._open_job_config(i),
        )
        job_cfg_btn.pack(side="left")
        job_log_btn = tk.Button(
            job_row, text="📋 日志",
            font=("Microsoft YaHei UI", 8),
            bg=ITEM, fg=SUB,
            activebackground=BORDER, activeforeground=TEXT,
            relief="flat", padx=8, pady=2, cursor="hand2",
            command=lambda i=idx: self._open_log(i),
        )
        job_log_btn.pack(side="left", padx=(4, 0))
        job_summary = tk.Label(
            job_row, text="暂无作业",
            font=("Microsoft YaHei UI", 8),
            bg=CARD, fg=SUB,
        )
        job_summary.pack(side="left", padx=(8, 0))

        # 右：控制按钮 + 进度
        job_ctrl = tk.Frame(job_row, bg=CARD)
        job_ctrl.pack(side="right")

        job_progress = tk.Label(
            job_ctrl, text="空闲",
            font=("Consolas", 8), bg=CARD, fg=SUB,
        )
        job_progress.pack(side="right", padx=(6, 0))

        job_stop_btn = tk.Button(
            job_ctrl, text="⏹",
            font=("Microsoft YaHei UI", 9),
            bg=ITEM, fg=RED,
            activebackground=BORDER, activeforeground=TEXT,
            relief="flat", padx=6, pady=1, cursor="hand2",
            command=lambda i=idx: self._stop_jobs(i),
            state="disabled",
        )
        job_stop_btn.pack(side="right", padx=(2, 0))

        job_pause_btn = tk.Button(
            job_ctrl, text="⏸",
            font=("Microsoft YaHei UI", 9),
            bg=ITEM, fg=YELLOW,
            activebackground=BORDER, activeforeground=TEXT,
            relief="flat", padx=6, pady=1, cursor="hand2",
            command=lambda i=idx: self._pause_resume_jobs(i),
            state="disabled",
        )
        job_pause_btn.pack(side="right", padx=(2, 0))

        job_start_btn = tk.Button(
            job_ctrl, text="▶",
            font=("Microsoft YaHei UI", 9),
            bg=ITEM, fg=GREEN,
            activebackground=BORDER, activeforeground=TEXT,
            relief="flat", padx=6, pady=1, cursor="hand2",
            command=lambda i=idx: self._start_jobs(i),
            state="disabled",
        )
        job_start_btn.pack(side="right", padx=(2, 0))

        # 证书按鈕绑定 idx（此处 emu_w 已包含 e_cert_btn）
        emu_w["e_cert_btn"].config(command=lambda i=idx: self._push_cert(i))

        return {
            "outer":        outer,
            "badge":        badge,
            "toggle":       toggle_btn,
            "arrow":        arrow_lbl,
            "link":         link_lbl,
            "job_sep":      job_sep,
            "job_row":      job_row,
            "job_summary":  job_summary,
            "job_progress": job_progress,
            "job_start":    job_start_btn,
            "job_pause":    job_pause_btn,
            "job_stop":     job_stop_btn,
            "job_cfg":      job_cfg_btn,
            "job_log":      job_log_btn,
            **proxy_w,
            **emu_w,
        }

    def _make_proxy_box(self, parent, port):
        box = tk.Frame(parent, bg=ITEM, padx=12, pady=8)
        tk.Label(
            box, text="MITMPROXY",
            font=("Consolas", 7, "bold"),
            bg=ITEM, fg=SUB,
        ).pack(anchor="w")
        _port_text  = f":{port}" if port is not None else "─"
        _port_color = BLUE if port is not None else SUB
        p_port = tk.Label(
            box, text=_port_text,
            font=("Consolas", 16, "bold"),
            bg=ITEM, fg=_port_color,
        )
        p_port.pack(anchor="w", pady=(1, 5))
        p_run = tk.Label(
            box, text="● 检测中",
            font=("Microsoft YaHei UI", 8),
            bg=ITEM, fg=YELLOW,
        )
        p_run.pack(anchor="w")
        p_add = tk.Label(
            box, text="addon  ─",
            font=("Microsoft YaHei UI", 7),
            bg=ITEM, fg=SUB,
        )
        p_add.pack(anchor="w", pady=(3, 0))
        return box, {"p_port": p_port, "p_run": p_run, "p_add": p_add}

    def _make_emu_box(self, parent, slot: dict):
        box = tk.Frame(parent, bg=ITEM, padx=12, pady=8)
        tk.Label(
            box, text="逍遥模拟器",
            font=("Microsoft YaHei UI", 7, "bold"),
            bg=ITEM, fg=SUB,
        ).pack(anchor="w")
        tk.Label(
            box, text=slot["emulator_serial"],
            font=("Consolas", 12, "bold"),
            bg=ITEM, fg=BLUE,
        ).pack(anchor="w", pady=(1, 5))
        e_st = tk.Label(
            box, text="● 检测中",
            font=("Microsoft YaHei UI", 8),
            bg=ITEM, fg=YELLOW,
        )
        e_st.pack(anchor="w")
        e_pr = tk.Label(
            box, text="代理  ─",
            font=("Microsoft YaHei UI", 7),
            bg=ITEM, fg=SUB,
        )
        e_pr.pack(anchor="w", pady=(3, 0))
        # 推送证书按钮（idx 在 _make_card 中通过 config 绑定）
        e_cert_btn = tk.Button(
            box, text="🛡 推送证书",
            font=("Microsoft YaHei UI", 7),
            bg=ITEM, fg=YELLOW,
            activebackground=BORDER, activeforeground=TEXT,
            relief="flat", padx=6, pady=1, cursor="hand2",
        )
        e_cert_btn.pack(anchor="w", pady=(4, 0))
        return box, {"e_st": e_st, "e_pr": e_pr, "e_cert_btn": e_cert_btn}

    # ────── 状态应用 ──────

    def _apply_status(self, statuses):
        # 卡片数量与状态数量不匹配（重新扫描期间），跳过本次
        if len(statuses) != len(self._cards):
            return

        for i, s in enumerate(statuses):
            w = self._cards[i]

            # 同步代理端口标签（端口可能被用户更改）
            if s["proxy_assigned"]:
                w["p_port"].config(text=f":{s['proxy_port']}", fg=BLUE)
            else:
                w["p_port"].config(text="─", fg=SUB)

            # mitmproxy 运行状态
            if not s["proxy_assigned"]:
                w["p_run"].config(text="─ 未分配", fg=SUB)
            elif s["port_up"]:
                w["p_run"].config(text="● 运行中", fg=GREEN)
            else:
                w["p_run"].config(text="● 未运行", fg=RED)

            # addon 健康状态
            if not s["proxy_assigned"] or not s["port_up"]:
                w["p_add"].config(text="addon  —", fg=SUB)
            elif s["addon"]:
                w["p_add"].config(text="addon  ✓ 正常", fg=GREEN)
            else:
                w["p_add"].config(text="addon  ✗ 无响应", fg=YELLOW)

            # 模拟器连接状态
            if s["emu_ok"]:
                w["e_st"].config(text="● 已连接", fg=GREEN)
            else:
                w["e_st"].config(text=f"● {s['emu_st']}", fg=RED)

            # 代理配置是否对准
            if not s["emu_ok"]:
                w["e_pr"].config(text="代理  —", fg=SUB)
            elif s["proxy_match"]:
                w["e_pr"].config(text=f"代理  ✓  {s['proxy_val']}", fg=GREEN)
            else:
                actual = s["proxy_val"] or "未设置"
                w["e_pr"].config(text=f"代理  ✗  {actual}", fg=YELLOW)

            # 箭头颜色 & 总体徽章
            if s["all_ok"]:
                w["arrow"].config(fg=GREEN)
                w["badge"].config(text="● 已就绪", fg=GREEN)
            elif not s["proxy_assigned"]:
                w["arrow"].config(fg=SUB)
                w["badge"].config(text="─ 待分配", fg=SUB)
            elif s["port_up"] and s["emu_ok"]:
                w["arrow"].config(fg=YELLOW)
                w["badge"].config(text="⚠ 配置异常", fg=YELLOW)
            else:
                w["arrow"].config(fg=RED)
                w["badge"].config(text="✗ 离线", fg=RED)

            # 箭头下方的连接地址标注
            if s["proxy_assigned"] and s["port_up"] and s["emu_ok"]:
                w["link"].config(text=s.get("expected_proxy") or "")
            else:
                w["link"].config(text="")

            # 记录最新状态，供 _toggle_proxy 使用
            self._last_statuses[i] = s

            # 还原 toggle 按钮文字与状态
            currently_on = s["port_up"] and s["proxy_match"]
            if not s["proxy_assigned"]:
                w["toggle"].config(state="normal", text="分配代理", fg=BLUE)
            elif currently_on:
                w["toggle"].config(state="normal", text="关闭代理", fg=RED)
            else:
                w["toggle"].config(state="normal", text="开启代理", fg=GREEN)

            # ── 作业行显示 / 隐藏 ──
            can_use_jobs = s["proxy_assigned"] and s["emu_ok"]
            if can_use_jobs:
                if not w["job_sep"].winfo_ismapped():
                    w["job_sep"].pack(fill="x", pady=(6, 0))
                    w["job_row"].pack(fill="x")
                self._update_job_row(i, w)
            else:
                if w["job_sep"].winfo_ismapped():
                    w["job_sep"].pack_forget()
                    w["job_row"].pack_forget()

        now = datetime.now().strftime("%H:%M:%S")
        self._foot_time.config(
            text=f"最后刷新: {now}   刷新间隔: {REFRESH_INTERVAL_MS // 1000}s"
        )
        self._hdr_right.config(text="")

    # ────── 代理切换 ──────
    def _ask_port(self, default_port: int = 8080) -> "int | None":
        """弹出深色主题对话框，让用户输入端口号；取消返回 None。"""
        dialog = tk.Toplevel(self)
        dialog.title("设置代理端口")
        dialog.configure(bg=BG)
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()
        result = [None]

        tk.Label(
            dialog, text="请输入 mitmproxy 监听端口:",
            font=("Microsoft YaHei UI", 10), bg=BG, fg=TEXT,
        ).pack(padx=24, pady=(16, 6))

        var   = tk.StringVar(value=str(default_port))
        entry = tk.Entry(
            dialog, textvariable=var,
            font=("Consolas", 13), bg=ITEM, fg=BLUE,
            insertbackground=TEXT, bd=0, width=10, justify="center",
        )
        entry.pack(padx=24, pady=4)
        entry.select_range(0, "end")
        entry.focus_set()

        err_lbl = tk.Label(dialog, text="", font=("Microsoft YaHei UI", 8),
                           bg=BG, fg=RED)
        err_lbl.pack()

        def on_ok(event=None):
            try:
                p = int(var.get().strip())
                if 1024 <= p <= 65535:
                    result[0] = p
                    dialog.destroy()
                else:
                    err_lbl.config(text="端口范围：1024 ~ 65535")
            except ValueError:
                err_lbl.config(text="请输入有效整数")

        def on_cancel(event=None):
            dialog.destroy()

        btn_row = tk.Frame(dialog, bg=BG)
        btn_row.pack(pady=14)
        tk.Button(
            btn_row, text="确认", command=on_ok,
            bg=ITEM, fg=GREEN, activebackground=BORDER,
            relief="flat", padx=16, pady=4, cursor="hand2",
        ).pack(side="left", padx=6)
        tk.Button(
            btn_row, text="取消", command=on_cancel,
            bg=ITEM, fg=RED, activebackground=BORDER,
            relief="flat", padx=16, pady=4, cursor="hand2",
        ).pack(side="left", padx=6)

        entry.bind("<Return>", on_ok)
        dialog.bind("<Escape>", on_cancel)

        self.update_idletasks()
        x = self.winfo_x() + (self.winfo_width()  - 300) // 2
        y = self.winfo_y() + (self.winfo_height() - 180) // 2
        dialog.geometry(f"300x180+{x}+{y}")

        self.wait_window(dialog)
        return result[0]

    def _toggle_proxy(self, idx: int):
        """切换指定 slot 的代理开关。"""
        st = self._last_statuses[idx]
        if st is None:
            return
        if not st.get("proxy_assigned"):
            # 未分配代理 → 先分配端口再开启
            self._enable_proxy(idx)
            return
        currently_on = bool(st.get("port_up") and st.get("proxy_match"))
        if currently_on:
            self._disable_proxy(idx)
        else:
            self._enable_proxy(idx)

    def _disable_proxy(self, idx: int):
        """关闭指定 slot 的代理：清除模拟器代理设置并终止 mitmdump 进程。"""
        serial = SLOTS[idx]["emulator_serial"]
        self._cards[idx]["toggle"].config(state="disabled", text="处理中…")

        def worker():
            try:
                for cmd in (
                    ["adb", "-s", serial, "shell",
                     "settings", "put", "global", "http_proxy", ":0"],
                    ["adb", "-s", serial, "shell",
                     "settings", "delete", "global", "http_proxy"],
                ):
                    try:
                        subprocess.run(cmd, timeout=5, capture_output=True)
                    except Exception:
                        pass
                proc = self._procs.pop(idx, None)
                if proc and proc.poll() is None:
                    proc.terminate()
                    try:
                        proc.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        proc.kill()
                else:
                    _kill_on_port(SLOTS[idx]["proxy_port"])
            finally:
                self.after(0, self._trigger_refresh)

        threading.Thread(target=worker, daemon=True).start()

    def _enable_proxy(self, idx: int):
        """分配/开启指定 slot 的代理：启动 mitmdump 并配置模拟器代理。"""
        current_port = SLOTS[idx]["proxy_port"]
        default_port = current_port if current_port is not None else (BASE_PROXY_PORT + idx)
        port = self._ask_port(default_port)
        if port is None:
            return  # 用户取消

        self._cards[idx]["toggle"].config(state="disabled", text="启动中…")

        def worker():
            try:
                # 终止旧进程
                old = self._procs.pop(idx, None)
                if old and old.poll() is None:
                    old.terminate()
                    try:
                        old.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        old.kill()

                # 端口被占则强制清理
                if _port_open(port):
                    _kill_on_port(port)
                    time.sleep(0.6)

                # 启动 mitmdump
                proc = subprocess.Popen(
                    ["mitmdump", "-p", str(port), "-s", ADDON_PATH, "--quiet"],
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                )
                self._procs[idx] = proc

                # 等待端口就绪（最多 6 秒）
                for _ in range(12):
                    time.sleep(0.5)
                    if _port_open(port):
                        break

                # 更新 SLOTS 内存配置
                SLOTS[idx]["proxy_port"]     = port
                SLOTS[idx]["expected_proxy"] = f"{HOST_IP}:{port}"

                # 更新端口标签（回到主线程）
                self.after(0,
                    lambda p=port: self._cards[idx]["p_port"].config(text=f":{p}"))

                # 配置模拟器代理
                serial = SLOTS[idx]["emulator_serial"]
                subprocess.run(
                    ["adb", "-s", serial, "shell", "settings", "put",
                     "global", "http_proxy", f"{HOST_IP}:{port}"],
                    timeout=5, capture_output=True,
                )
            except Exception as e:
                print(f"[enable_proxy idx={idx}] 异常: {e}")
            finally:
                self.after(0, self._trigger_refresh)

        threading.Thread(target=worker, daemon=True).start()

    def _push_cert(self, idx: int):
        """将 mitmproxy CA 证书推送并安装到指定模拟器。

        证书查找优先级：
          1. Docker/c8750f0d.0  — 本地 mitmdump 证书的 Android 格式（subject_hash_old 预计算）
          2. Docker/mitmproxy-ca-cert.cer — 备用
          3. 用户手动选择

        安装步骤：
          1. adb push 证书文件到 /data/local/tmp/
          2. cp 到 /system/etc/security/cacerts/<hash>.0（需要 root 权限）
          3. chmod 644
          4. 重启 installd 使证书立即生效
        """
        serial   = SLOTS[idx]["emulator_serial"]
        cert_dir = os.path.join(BASE_DIR, "Docker")

        # 按优先级查找证书
        candidates = [
            (os.path.join(cert_dir, "c8750f0d.0"),          "c8750f0d.0"),
            (os.path.join(cert_dir, "mitmproxy-ca-cert.cer"), "mitmproxy-ca-cert.cer"),
        ]
        local_cert  = None
        remote_name = None
        for path, name in candidates:
            if os.path.isfile(path):
                local_cert  = path
                remote_name = name
                break

        # 均不存在则让用户手动选择
        if local_cert is None:
            local_cert = tkinter.filedialog.askopenfilename(
                parent=self,
                title="选择 mitmproxy CA 证书文件",
                filetypes=[("PEM/CRT/0 文件", "*.pem *.crt *.cer *.0"), ("所有文件", "*.*")],
                initialdir=BASE_DIR,
            )
            if not local_cert:
                return
            remote_name = os.path.basename(local_cert)

        btn = self._cards[idx].get("e_cert_btn")
        if btn:
            btn.config(state="disabled", text="推送中…")

        def worker():
            logs = []
            ok   = True
            try:
                tmp_path    = f"/data/local/tmp/{remote_name}"
                system_path = f"/system/etc/security/cacerts/{remote_name}"

                # step 1: push
                r = subprocess.run(
                    ["adb", "-s", serial, "push", local_cert, tmp_path],
                    capture_output=True, text=True, timeout=15,
                )
                logs.append(r.stdout.strip() or r.stderr.strip())
                if r.returncode != 0:
                    raise RuntimeError(f"push 失败: {r.stderr.strip()}")

                # step 2: remount /system
                subprocess.run(
                    ["adb", "-s", serial, "shell", "su -c 'mount -o remount,rw /system'"],
                    capture_output=True, timeout=10,
                )

                # step 3: cp to cacerts
                r = subprocess.run(
                    ["adb", "-s", serial, "shell",
                     f"su -c 'cp {tmp_path} {system_path}'"],
                    capture_output=True, text=True, timeout=10,
                )
                if r.returncode != 0:
                    raise RuntimeError(f"cp 失败: {r.stderr.strip()}")

                # step 4: chmod
                subprocess.run(
                    ["adb", "-s", serial, "shell",
                     f"su -c 'chmod 644 {system_path}'"],
                    capture_output=True, timeout=10,
                )

                # step 5: 重启安全存储服务使证书生效
                subprocess.run(
                    ["adb", "-s", serial, "shell",
                     "su -c 'stop installd; start installd'"],
                    capture_output=True, timeout=15,
                )

                msg = f"证书已成功安装到 {serial}\n{system_path}"
            except Exception as e:
                ok  = False
                msg = f"证书安装失败\n{e}\n请确认模拟器已 root 且 adb 已连接。"

            def done():
                if btn:
                    btn.config(state="normal", text="🛡 推送证书")
                if ok:
                    tkinter.messagebox.showinfo("证书安装成功", msg)
                else:
                    tkinter.messagebox.showerror("证书安装失败", msg)

            self.after(0, done)

        threading.Thread(target=worker, daemon=True).start()

    def _rescan_emulators(self):
        """重新扫描逍遥模拟器实例，保留已分配的代理端口，并重建卡片区域。"""
        global SLOTS
        # 保存当前的端口分配
        old_assignments = {
            s["emulator_serial"]: {
                "proxy_port":    s["proxy_port"],
                "expected_proxy": s["expected_proxy"],
            }
            for s in SLOTS
        }

        SLOTS = detect_memu_instances()

        # 恢复已分配的端口（已分配过的实例保留设置）
        for s in SLOTS:
            prev = old_assignments.get(s["emulator_serial"])
            if prev and prev["proxy_port"] is not None:
                s["proxy_port"]     = prev["proxy_port"]
                s["expected_proxy"] = prev["expected_proxy"]

        self._last_statuses = [None] * len(SLOTS)
        self._fill_cards()
        self._trigger_refresh()

        count = len(SLOTS)
        msg = f"检测到 {count} 个实例" if count else "未检测到运行中的模拟器"
        self._hdr_right.config(text=msg)

    # ────── 刷新调度 ──────

    def _kill_all_proxies(self, silent: bool = False):
        """强制终止所有由本面板启动的 mitmdump 进程，并按端口逐一清理。"""
        # 1) 终止由本进程记录的子进程
        for idx, proc in list(self._procs.items()):
            if proc and proc.poll() is None:
                try:
                    proc.terminate()
                    proc.wait(timeout=3)
                except Exception:
                    try:
                        proc.kill()
                    except Exception:
                        pass
        self._procs.clear()

        # 2) 按已分配的端口逐一强杀占用进程（处理面板外部起全的 mitmdump）
        for s in SLOTS:
            p = s.get("proxy_port")
            if p is not None:
                _kill_on_port(p)

        if not silent:
            self._hdr_right.config(text="已全部关闭")

    def _on_close(self):
        """关闭窗口前先清理全部代理进程。"""
        # 取消定时刷新
        if self._job:
            self.after_cancel(self._job)
            self._job = None
        # 停止所有作业运行器
        for runner in self._runners.values():
            runner.stop()
        self._kill_all_proxies(silent=True)
        self.destroy()

    # ────── 作业管理 ──────

    def _build_units(self, idx: int) -> list:
        """将作业配置列表展开为可执行的单元列表。"""
        units = []
        for c in self._job_configs.get(idx, []):
            params = c.get("params", [])
            if params:
                for p in params:
                    # p 可能是字符串（单参数）或列表（多参数），原样传入
                    units.append({"task_key": c["task_key"], "param": p})
            else:
                units.append({"task_key": c["task_key"], "param": None})
        return units

    def _on_runner_update(self, idx: int):
        """Runner 状态变化回调 → 在主线程刷新对应卡片的作业行。"""
        if idx < len(self._cards):
            w = self._cards[idx]
            if w.get("job_sep") and w["job_sep"].winfo_ismapped():
                self._update_job_row(idx, w)

    def _update_job_row(self, idx: int, w: dict):
        """根据当前配置和运行器状态，更新作业行各控件。"""
        configs  = self._job_configs.get(idx, [])
        runner   = self._runners.get(idx)
        state    = runner.state if runner else RunnerState.IDLE
        has_jobs = bool(configs)

        # 摘要文字
        if not has_jobs:
            w["job_summary"].config(text="暂无作业", fg=SUB)
        else:
            parts = []
            for c in configs:
                label = TASK_DEFS[c["task_key"]]["label"]
                cnt   = len(c["params"]) if c["params"] else 1
                parts.append(f"{label}×{cnt}")
            summary = "  ".join(parts)
            total_u = sum(len(c["params"]) if c["params"] else 1 for c in configs)
            if len(summary) > 52:
                summary = f"{len(configs)} 任务 / {total_u} 次执行"
            w["job_summary"].config(text=summary, fg=TEXT)

        # 按状态更新按钮与进度标签
        if state == RunnerState.IDLE:
            w["job_start"].config(state="normal" if has_jobs else "disabled", text="▶", fg=GREEN)
            w["job_pause"].config(state="disabled", text="⏸")
            w["job_stop"].config(state="disabled")
            w["job_progress"].config(text="空闲", fg=SUB)
        elif state == RunnerState.RUNNING:
            w["job_start"].config(state="disabled", text="▶", fg=GREEN)
            w["job_pause"].config(state="normal", text="⏸")
            w["job_stop"].config(state="normal")
            w["job_progress"].config(text=f"运行中 {runner.current}/{runner.total}", fg=GREEN)
        elif state == RunnerState.PAUSED:
            w["job_start"].config(state="normal", text="▶ 继续", fg=GREEN)
            w["job_pause"].config(state="disabled", text="⏸")
            w["job_stop"].config(state="normal")
            w["job_progress"].config(text=f"已暂停 {runner.current}/{runner.total}", fg=YELLOW)
        elif state == RunnerState.DONE:
            w["job_start"].config(state="normal" if has_jobs else "disabled", text="▶ 重跑", fg=GREEN)
            w["job_pause"].config(state="disabled", text="⏸")
            w["job_stop"].config(state="disabled")
            w["job_progress"].config(text=f"已完成 {runner.total}/{runner.total}", fg=GREEN)
        elif state == RunnerState.STOPPED:
            w["job_start"].config(state="normal" if has_jobs else "disabled", text="▶ 重跑", fg=GREEN)
            w["job_pause"].config(state="disabled", text="⏸")
            w["job_stop"].config(state="disabled")
            w["job_progress"].config(text=f"已停止 {runner.current}/{runner.total}", fg=RED)

    def _start_jobs(self, idx: int):
        """开始或恢复运行作业队列。"""
        runner = self._runners.get(idx)
        if runner and runner.state == RunnerState.PAUSED:
            runner.resume()
            return
        configs = self._job_configs.get(idx, [])
        if not configs:
            return
        if runner:
            runner.stop()
        serial     = SLOTS[idx]["emulator_serial"]
        proxy_port = SLOTS[idx]["proxy_port"]
        slot_name  = SLOTS[idx]["name"]
        units      = self._build_units(idx)

        # 使用从进度文件恢复的作业号；新作业则生成新编号
        job_id     = self._job_ids.pop(idx, None) or datetime.now().strftime("%Y%m%d_%H%M%S")
        job_label  = _make_job_label(configs)
        start_from = self._job_resume_from.pop(idx, 0)

        new_runner = JobRunner(
            serial, units,
            proxy_port=proxy_port,
            on_update=lambda r, i=idx: self.after(0, lambda: self._on_runner_update(i)),
            on_log=lambda r, text, i=idx: self.after(0, lambda: self._on_runner_log(i, text)),
            job_id=job_id,
            job_label=job_label,
            slot_name=slot_name,
            configs=configs,
            start_from=start_from,
        )
        self._runners[idx] = new_runner
        new_runner.start()

    def _pause_resume_jobs(self, idx: int):
        """暂停或恢复指定队列。"""
        runner = self._runners.get(idx)
        if not runner:
            return
        if runner.state == RunnerState.RUNNING:
            runner.pause()
        elif runner.state == RunnerState.PAUSED:
            runner.resume()

    def _stop_jobs(self, idx: int):
        """停止指定队列。"""
        runner = self._runners.get(idx)
        if runner:
            runner.stop()

    def _open_log(self, idx: int):
        """打开或激活日志窗口。"""
        win = self._log_windows.get(idx)
        if win and win.winfo_exists():
            win.lift()
            win.focus_force()
            return
        runner = self._runners.get(idx)
        initial = "".join(l + "\n" for l in runner.log_lines) if runner else ""
        name = SLOTS[idx]["name"] if idx < len(SLOTS) else f"slot {idx}"
        win = LogWindow(self, title=f"作业日志 — {name}", initial_text=initial)
        self._log_windows[idx] = win

    def _on_runner_log(self, idx: int, text: str):
        """Runner 日志回调 → 在主线程追加到日志窗口。"""
        win = self._log_windows.get(idx)
        if win and win.winfo_exists():
            win.append(text)

    # ────── 参数提取 ──────

    def _extract_categories(self):
        """从分类列表提取分类名称，导出为 getBookListByTypeAPI 参数。"""
        default_path = os.path.join(BASE_DIR, "data", "CategoryList.json")
        ParamExtractDialog(self, mode="category", default_path=default_path)

    def _extract_books(self):
        """从书籍列表提取书名，导出为 searchbook 参数。"""
        default_path = os.path.join(BASE_DIR, "data", "BookList.json")
        ParamExtractDialog(self, mode="book", default_path=default_path)

    def _extract_authors(self):
        """从书籍列表提取作者名，导出为 getUserAPI 参数。"""
        default_path = os.path.join(BASE_DIR, "data", "BookList.json")
        ParamExtractDialog(self, mode="author", default_path=default_path)

    def _open_job_config(self, idx: int):
        """打开作业配置对话框。"""
        current = self._job_configs.get(idx, [])
        dlg = JobDialog(self, idx, current)
        self.wait_window(dlg)
        if dlg.result is not None:
            runner = self._runners.get(idx)
            if runner and runner.state in (RunnerState.RUNNING, RunnerState.PAUSED):
                runner.stop()
                self._runners.pop(idx, None)
            result = dlg.result
            self._job_configs[idx] = result["configs"]
            if result.get("job_id"):
                # 从进度文件恢复：保存作业号和起始位置
                self._job_ids[idx]         = result["job_id"]
                self._job_resume_from[idx] = result.get("resume_from", 0)
            else:
                # 新作业：清除旧的作业号，下次启动时重新生成
                self._job_ids.pop(idx, None)
                self._job_resume_from.pop(idx, None)
            if idx < len(self._cards):
                self._update_job_row(idx, self._cards[idx])

    # ────── 刷新调度 ──────

    def _trigger_refresh(self):
        """手动或定时触发一次刷新。"""
        if self._job:
            self.after_cancel(self._job)
            self._job = None

        if self._refreshing:
            # 上次未结束，稍后重试
            self._job = self.after(500, self._trigger_refresh)
            return

        self._refreshing = True
        self._hdr_right.config(text="刷新中…")

        def worker():
            try:
                statuses = collect_status()
                self.after(0, lambda: self._apply_status(statuses))
            finally:
                self._refreshing = False
                self._job = self.after(REFRESH_INTERVAL_MS, self._trigger_refresh)

        threading.Thread(target=worker, daemon=True).start()


# ─────────────────────────── 作业配置对话框 ───────────────────────────

class JobDialog(tk.Toplevel):
    """作业配置对话框：添加、排序、删除作业任务。"""

    def __init__(self, master, slot_idx: int, current_configs: list):
        super().__init__(master)
        self.title(f"配置作业 — {SLOTS[slot_idx]['name']}")
        self.configure(bg=BG)
        self.resizable(True, True)
        self.transient(master)
        self.grab_set()

        self.result   = None
        self._configs = [dict(c) for c in current_configs]
        self._sel_idx = None
        self._job_id      = ""   # 从进度文件恢复时记录原作业号
        self._resume_from = 0    # 从进度文件恢复时记录已完成单元数

        self._build_ui()

        self.update_idletasks()
        w, h = 780, 540
        px = master.winfo_x() + max(0, (master.winfo_width()  - w) // 2)
        py = master.winfo_y() + max(0, (master.winfo_height() - h) // 2)
        self.geometry(f"{w}x{h}+{px}+{py}")
        self.minsize(600, 420)
        self.bind("<Escape>", lambda e: self.destroy())

    def _build_ui(self):
        # ── 主内容区 ──
        content = tk.Frame(self, bg=BG)
        content.pack(fill="both", expand=True, padx=16, pady=(14, 0))

        # ── 左面板：作业队列 ──
        left = tk.Frame(content, bg=BG)
        left.pack(side="left", fill="both", expand=True, padx=(0, 6))

        tk.Label(
            left, text="当前作业队列",
            font=("Microsoft YaHei UI", 9, "bold"), bg=BG, fg=TEXT,
        ).pack(anchor="w", pady=(0, 4))

        lb_outer = tk.Frame(left, bg=BORDER, padx=1, pady=1)
        lb_outer.pack(fill="both", expand=True)
        lb_scroll = tk.Scrollbar(lb_outer, bg=ITEM, troughcolor=HDR)
        self._listbox = tk.Listbox(
            lb_outer,
            font=("Microsoft YaHei UI", 9),
            bg=ITEM, fg=TEXT,
            selectbackground=BORDER, selectforeground=TEXT,
            yscrollcommand=lb_scroll.set,
            bd=0, activestyle="none", highlightthickness=0,
        )
        lb_scroll.config(command=self._listbox.yview)
        lb_scroll.pack(side="right", fill="y")
        self._listbox.pack(fill="both", expand=True)
        self._listbox.bind("<<ListboxSelect>>", self._on_select)

        lb_btn = tk.Frame(left, bg=BG)
        lb_btn.pack(fill="x", pady=(4, 0))
        for text, cmd in [("↑ 上移", self._move_up), ("↓ 下移", self._move_down), ("✕ 删除", self._delete_selected)]:
            tk.Button(
                lb_btn, text=text,
                font=("Microsoft YaHei UI", 8),
                bg=ITEM, fg=TEXT, activebackground=BORDER,
                relief="flat", padx=10, pady=3, cursor="hand2",
                command=cmd,
            ).pack(side="left", padx=(0, 4))

        # ── 垂直分隔线 ──
        tk.Frame(content, bg=BORDER, width=1).pack(side="left", fill="y", padx=6)

        # ── 右面板：添加作业 ──
        right = tk.Frame(content, bg=BG, width=310)
        right.pack(side="left", fill="both")
        right.pack_propagate(False)

        tk.Label(
            right, text="添加新作业",
            font=("Microsoft YaHei UI", 9, "bold"), bg=BG, fg=TEXT,
        ).pack(anchor="w", pady=(0, 6))

        # 任务类型下拉
        tk.Label(right, text="任务类型:", font=("Microsoft YaHei UI", 8), bg=BG, fg=SUB).pack(anchor="w")
        self._task_var = tk.StringVar(value=TASK_DEFS[TASK_KEYS[0]]["label"])
        opt = tk.OptionMenu(right, self._task_var, *[TASK_DEFS[k]["label"] for k in TASK_KEYS])
        opt.configure(
            bg=ITEM, fg=TEXT, activebackground=BORDER,
            font=("Microsoft YaHei UI", 9), bd=0, relief="flat",
            highlightthickness=0, width=22,
        )
        opt["menu"].configure(bg=ITEM, fg=TEXT, activebackground=BORDER, font=("Microsoft YaHei UI", 9))
        opt.pack(fill="x", pady=(2, 10))
        self._task_var.trace_add("write", self._on_task_change)

        # 参数输入
        self._param_label = tk.Label(
            right, text="批量参数 (JSON 数组):",
            font=("Microsoft YaHei UI", 8), bg=BG, fg=SUB,
        )
        self._param_label.pack(anchor="w")

        param_outer = tk.Frame(right, bg=BORDER, padx=1, pady=1)
        param_outer.pack(fill="x", pady=(2, 4))
        self._param_text = tk.Text(
            param_outer, height=7,
            font=("Consolas", 10),
            bg=ITEM, fg=BLUE,
            insertbackground=TEXT,
            bd=0, wrap="word", highlightthickness=0,
        )
        self._param_text.pack(fill="x")
        self._param_text.insert("1.0", '["参数1", "参数2"]')

        self._hint_lbl = tk.Label(
            right, text="",
            font=("Microsoft YaHei UI", 7),
            bg=BG, fg=SUB,
            wraplength=290, justify="left",
        )
        self._hint_lbl.pack(anchor="w", pady=(0, 6))

        tk.Button(
            right, text="📂  从 JSON 文件导入",
            font=("Microsoft YaHei UI", 8),
            bg=ITEM, fg=BLUE, activebackground=BORDER,
            relief="flat", padx=8, pady=3, cursor="hand2",
            command=self._import_json,
        ).pack(fill="x", pady=(0, 4))

        tk.Button(
            right, text="  +  添加到队列",
            font=("Microsoft YaHei UI", 9, "bold"),
            bg=ITEM, fg=GREEN, activebackground=BORDER,
            relief="flat", padx=8, pady=5, cursor="hand2",
            command=self._add_to_queue,
        ).pack(fill="x")

        # ── 底部工具栏 ──
        footer = tk.Frame(self, bg=HDR, pady=8)
        footer.pack(fill="x", side="bottom")
        for text, cmd, fg in [
            ("✓  确认", self._confirm, GREEN),
            ("🗑  清空所有", self._clear_all, YELLOW),
            ("📂  继续未完成作业", self._load_progress, BLUE),
            ("✗  取消", self.destroy, RED),
        ]:
            tk.Button(
                footer, text=text,
                font=("Microsoft YaHei UI", 9),
                bg=ITEM, fg=fg, activebackground=BORDER,
                relief="flat", padx=14, pady=4, cursor="hand2",
                command=cmd,
            ).pack(side="left", padx=8)

        self._refresh_listbox()
        self._on_task_change()

    # ── 任务类型切换 ──

    def _on_task_change(self, *_):
        label     = self._task_var.get()
        task_key  = LABEL_TO_KEY.get(label)
        tdef      = TASK_DEFS.get(task_key, {})
        has_param = tdef.get("param_key") is not None
        if has_param:
            pk = tdef["param_key"]
            extra = tdef.get("extra_args", [])
            self._param_label.config(fg=TEXT, text=f"批量参数 [{pk}]  (JSON 数组):")
            self._param_text.config(state="normal", fg=BLUE)
            if extra:
                extra_desc = "  ".join(f'{e["key"]}({e["hint"]})' for e in extra)
                hint = (
                    f'单参数格式：["值1", "值2"]\n'
                    f'多参数格式（含可选参数）：'
                    f'[["值1", 超时秒], ["值2"]]\n'
                    f'可选参数：{extra_desc}\n'
                    f'文件支持 ["v1","v2"] 或 {{"{pk}":["v1","v2"]}}'
                )
            else:
                hint = (
                    f'格式：["值1", "值2"]  或从 JSON 文件导入\n'
                    f'文件支持 ["v1","v2"] 或 {{"{pk}":["v1","v2"]}}'
                )
            self._hint_lbl.config(text=hint)
        else:
            self._param_label.config(fg=SUB, text="批量参数：(此任务无需参数，执行一次)")
            self._param_text.config(state="disabled", fg=SUB)
            self._hint_lbl.config(text="")

    # ── 导入 JSON 文件 ──

    def _import_json(self):
        path = tkinter.filedialog.askopenfilename(
            parent=self,
            title="选择 JSON 参数文件",
            filetypes=[("JSON 文件", "*.json"), ("所有文件", "*.*")],
        )
        if not path:
            return
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            task_key  = LABEL_TO_KEY.get(self._task_var.get())
            param_key = TASK_DEFS.get(task_key, {}).get("param_key")
            if isinstance(data, list):
                values = data
            elif isinstance(data, dict):
                if param_key and param_key in data:
                    values = data[param_key]
                else:
                    values = next((v for v in data.values() if isinstance(v, list)), list(data.values()))
            else:
                values = [data]
            self._param_text.config(state="normal")
            self._param_text.delete("1.0", "end")
            self._param_text.insert("1.0", json.dumps(values, ensure_ascii=False))
            if not param_key:
                self._param_text.config(state="disabled")
        except Exception as e:
            tkinter.messagebox.showerror("导入失败", str(e), parent=self)

    # ── 添加到队列 ──

    def _add_to_queue(self):
        label    = self._task_var.get()
        task_key = LABEL_TO_KEY.get(label)
        tdef     = TASK_DEFS.get(task_key)
        if not tdef:
            return
        if tdef["param_key"] is None:
            params = []
        else:
            raw = self._param_text.get("1.0", "end").strip()
            try:
                parsed = json.loads(raw)
                if not isinstance(parsed, list):
                    parsed = [parsed]
                # 每项可以是字符串（单参数）或列表（多参数，如 ["都市", 120]）
                params = []
                for item in parsed:
                    if isinstance(item, list):
                        cleaned = [str(a) for a in item if str(a).strip()]
                        if cleaned:
                            params.append(cleaned)
                    elif str(item).strip():
                        params.append(str(item))
            except json.JSONDecodeError as e:
                tkinter.messagebox.showerror("参数格式错误", f"请输入有效的 JSON 数组。\n{e}", parent=self)
                return
            if not params:
                tkinter.messagebox.showwarning("参数为空", "请至少输入一个参数值。", parent=self)
                return
        self._configs.append({"task_key": task_key, "params": params})
        self._refresh_listbox()

    # ── 列表操作 ──

    def _refresh_listbox(self):
        self._listbox.delete(0, "end")
        for i, c in enumerate(self._configs):
            label  = TASK_DEFS[c["task_key"]]["label"]
            params = c.get("params", [])
            if params:
                preview = ", ".join(str(p) for p in params[:3])
                if len(params) > 3:
                    preview += f"... (+{len(params) - 3})"
                text = f"{i+1}.  {label}  ×{len(params)}  [{preview}]"
            else:
                text = f"{i+1}.  {label}  (无参数，执行一次)"
            self._listbox.insert("end", text)
        self._sel_idx = None

    def _on_select(self, _event=None):
        sel = self._listbox.curselection()
        self._sel_idx = sel[0] if sel else None

    def _move_up(self):
        i = self._sel_idx
        if i is None or i == 0:
            return
        self._configs[i - 1], self._configs[i] = self._configs[i], self._configs[i - 1]
        self._refresh_listbox()
        self._listbox.selection_set(i - 1)
        self._sel_idx = i - 1

    def _move_down(self):
        i = self._sel_idx
        if i is None or i >= len(self._configs) - 1:
            return
        self._configs[i], self._configs[i + 1] = self._configs[i + 1], self._configs[i]
        self._refresh_listbox()
        self._listbox.selection_set(i + 1)
        self._sel_idx = i + 1

    def _delete_selected(self):
        i = self._sel_idx
        if i is None:
            return
        del self._configs[i]
        self._refresh_listbox()

    def _clear_all(self):
        self._configs.clear()
        self._job_id      = ""
        self._resume_from = 0
        self._refresh_listbox()

    def _load_progress(self):
        """从进度文件恢复未完成的作业。"""
        progress_dir = PROGRESS_DIR
        initialdir = progress_dir if os.path.isdir(progress_dir) else BASE_DIR
        path = tkinter.filedialog.askopenfilename(
            parent=self,
            title="选择未完成的作业进度文件",
            filetypes=[("JSON 文件", "*.json"), ("所有文件", "*.*")],
            initialdir=initialdir,
        )
        if not path:
            return
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            tkinter.messagebox.showerror("加载失败", str(e), parent=self)
            return
        if not isinstance(data, dict) or "configs" not in data:
            tkinter.messagebox.showerror("格式错误", "不是有效的作业进度文件", parent=self)
            return
        status    = data.get("status", "")
        completed = data.get("completed", 0)
        total     = data.get("total", 0)
        job_id    = data.get("job_id", "")
        job_label = data.get("job_label", "")
        if status == RunnerState.DONE:
            tkinter.messagebox.showinfo(
                "已完成",
                f"该作业已全部完成（{total}/{total}），无需继续。",
                parent=self,
            )
            return
        self._configs     = [dict(c) for c in data.get("configs", [])]
        self._job_id      = job_id
        self._resume_from = completed
        self._refresh_listbox()
        tkinter.messagebox.showinfo(
            "已加载进度",
            f"作业号：{job_id}\n内容：{job_label}\n进度：{completed}/{total}\n"
            f"将从第 {completed + 1} 个单元继续执行。",
            parent=self,
        )

    def _confirm(self):
        self.result = {
            "configs":     list(self._configs),
            "job_id":      self._job_id,
            "resume_from": self._resume_from,
        }
        self.destroy()


# ─────────────────────────── 参数提取对话框 ───────────────────────────

class ParamExtractDialog(tk.Toplevel):
    """从 JSON 数据文件中提取名称列表，让用户勾选后导出为作业参数 JSON。"""

    MODE_CFG = {
        "category": {
            "title": "分类提取 → getBookListByTypeAPI 参数",
            "file_label": "分类列表文件 (CategoryList.json):",
            "list_title": "分类名称",
            "show_timeout": True,
        },
        "book": {
            "title": "书名提取 → searchbook 参数",
            "file_label": "书籍列表文件 (BookList.json):",
            "list_title": "书籍名称",
            "show_timeout": False,
        },
        "author": {
            "title": "作者提取 → getUserAPI 参数",
            "file_label": "书籍列表文件 (BookList.json):",
            "list_title": "作者名称",
            "show_timeout": False,
        },
    }

    def __init__(self, master, mode: str, default_path: str):
        super().__init__(master)
        cfg = self.MODE_CFG[mode]
        self.title(cfg["title"])
        self.configure(bg=BG)
        self.resizable(True, True)
        self.transient(master)
        self.grab_set()
        self.minsize(520, 460)

        self._mode = mode
        self._items: list[str] = []
        self._check_vars: list[tk.BooleanVar] = []   # 不再使用，保留以兼容旧接口
        self._listbox: "tk.Listbox | None" = None     # 高性能列表控件

        # ── 文件选择行 ──
        file_row = tk.Frame(self, bg=BG)
        file_row.pack(fill="x", padx=14, pady=(12, 0))
        tk.Label(
            file_row, text=cfg["file_label"],
            font=("Microsoft YaHei UI", 9), bg=BG, fg=TEXT,
        ).pack(side="left")
        self._path_var = tk.StringVar(value=default_path)
        tk.Entry(
            file_row, textvariable=self._path_var,
            font=("Consolas", 9), bg=ITEM, fg=BLUE,
            insertbackground=TEXT, bd=0, width=40,
        ).pack(side="left", fill="x", expand=True, padx=(6, 4))
        tk.Button(
            file_row, text="浏览",
            font=("Microsoft YaHei UI", 8),
            bg=ITEM, fg=TEXT, activebackground=BORDER,
            relief="flat", padx=8, cursor="hand2",
            command=self._browse_file,
        ).pack(side="left")
        tk.Button(
            file_row, text="加载",
            font=("Microsoft YaHei UI", 8),
            bg=ITEM, fg=GREEN, activebackground=BORDER,
            relief="flat", padx=8, cursor="hand2",
            command=self._load_file,
        ).pack(side="left", padx=(4, 0))

        # ── 超时设置（仅分类模式） ──
        if cfg["show_timeout"]:
            to_row = tk.Frame(self, bg=BG)
            to_row.pack(fill="x", padx=14, pady=(8, 0))
            tk.Label(
                to_row, text="统一滚动超时秒数 (第二参数):",
                font=("Microsoft YaHei UI", 9), bg=BG, fg=TEXT,
            ).pack(side="left")
            self._timeout_var = tk.StringVar(value="180")
            tk.Entry(
                to_row, textvariable=self._timeout_var,
                font=("Consolas", 10), bg=ITEM, fg=BLUE,
                insertbackground=TEXT, bd=0, width=8, justify="center",
            ).pack(side="left", padx=(6, 0))
        else:
            self._timeout_var = None

        # ── 全选/反选/统计行 ──
        ctrl_row = tk.Frame(self, bg=BG)
        ctrl_row.pack(fill="x", padx=14, pady=(10, 2))
        tk.Label(
            ctrl_row, text=cfg["list_title"],
            font=("Microsoft YaHei UI", 9, "bold"), bg=BG, fg=TEXT,
        ).pack(side="left")
        self._count_lbl = tk.Label(
            ctrl_row, text="0 / 0",
            font=("Consolas", 9), bg=BG, fg=SUB,
        )
        self._count_lbl.pack(side="right")
        for text, cmd in [("反选", self._invert_sel), ("取消全选", self._desel_all), ("全选", self._sel_all)]:
            tk.Button(
                ctrl_row, text=text,
                font=("Microsoft YaHei UI", 8),
                bg=ITEM, fg=TEXT, activebackground=BORDER,
                relief="flat", padx=6, pady=1, cursor="hand2",
                command=cmd,
            ).pack(side="right", padx=(4, 0))

        # ── 范围选取行 ──
        range_row = tk.Frame(self, bg=BG)
        range_row.pack(fill="x", padx=14, pady=(0, 4))
        tk.Label(
            range_row, text="范围选取:",
            font=("Microsoft YaHei UI", 9), bg=BG, fg=TEXT,
        ).pack(side="left")
        tk.Label(
            range_row, text="第",
            font=("Microsoft YaHei UI", 9), bg=BG, fg=SUB,
        ).pack(side="left", padx=(6, 0))
        self._range_start_var = tk.StringVar(value="1")
        tk.Entry(
            range_row, textvariable=self._range_start_var,
            font=("Consolas", 9), bg=ITEM, fg=BLUE,
            insertbackground=TEXT, bd=0, width=6, justify="center",
        ).pack(side="left", padx=(2, 0))
        tk.Label(
            range_row, text="―至第",
            font=("Microsoft YaHei UI", 9), bg=BG, fg=SUB,
        ).pack(side="left", padx=(4, 0))
        self._range_end_var = tk.StringVar(value="60")
        tk.Entry(
            range_row, textvariable=self._range_end_var,
            font=("Consolas", 9), bg=ITEM, fg=BLUE,
            insertbackground=TEXT, bd=0, width=6, justify="center",
        ).pack(side="left", padx=(2, 0))
        tk.Label(
            range_row, text="条",
            font=("Microsoft YaHei UI", 9), bg=BG, fg=SUB,
        ).pack(side="left", padx=(2, 0))
        tk.Button(
            range_row, text="选取该范围",
            font=("Microsoft YaHei UI", 8),
            bg=ITEM, fg=YELLOW, activebackground=BORDER,
            relief="flat", padx=8, pady=1, cursor="hand2",
            command=self._select_range,
        ).pack(side="left", padx=(8, 0))

        # ── 列表区域（tk.Listbox 天生支持万级条目，性能远超 Checkbutton） ──
        list_outer = tk.Frame(self, bg=BORDER, padx=1, pady=1)
        list_outer.pack(fill="both", expand=True, padx=14, pady=(2, 6))
        lb_scroll_y = tk.Scrollbar(list_outer, orient="vertical", bg=ITEM, troughcolor=HDR)
        lb_scroll_x = tk.Scrollbar(list_outer, orient="horizontal", bg=ITEM, troughcolor=HDR)
        self._listbox = tk.Listbox(
            list_outer,
            selectmode="extended",
            font=("Microsoft YaHei UI", 9),
            bg=ITEM, fg=TEXT,
            selectbackground=BORDER, selectforeground=GREEN,
            activestyle="none", highlightthickness=0, bd=0,
            yscrollcommand=lb_scroll_y.set,
            xscrollcommand=lb_scroll_x.set,
            exportselection=False,
        )
        lb_scroll_y.config(command=self._listbox.yview)
        lb_scroll_x.config(command=self._listbox.xview)
        lb_scroll_y.pack(side="right", fill="y")
        lb_scroll_x.pack(side="bottom", fill="x")
        self._listbox.pack(fill="both", expand=True)
        self._listbox.bind("<<ListboxSelect>>", lambda _: self._update_count())
        self._listbox.bind("<MouseWheel>",
            lambda e: self._listbox.yview_scroll(-1 * (e.delta // 120), "units"))

        # ── 底部按钮 ──
        footer = tk.Frame(self, bg=HDR, pady=8)
        footer.pack(fill="x", side="bottom")
        tk.Button(
            footer, text="✓  导出 JSON",
            font=("Microsoft YaHei UI", 9, "bold"),
            bg=ITEM, fg=GREEN, activebackground=BORDER,
            relief="flat", padx=14, pady=4, cursor="hand2",
            command=self._export,
        ).pack(side="left", padx=12)
        tk.Button(
            footer, text="✗  关闭",
            font=("Microsoft YaHei UI", 9),
            bg=ITEM, fg=RED, activebackground=BORDER,
            relief="flat", padx=14, pady=4, cursor="hand2",
            command=self.destroy,
        ).pack(side="left")

        # 居中
        self.update_idletasks()
        w, h = 660, 560
        px = master.winfo_x() + max(0, (master.winfo_width()  - w) // 2)
        py = master.winfo_y() + max(0, (master.winfo_height() - h) // 2)
        self.geometry(f"{w}x{h}+{px}+{py}")
        self.bind("<Escape>", lambda e: self.destroy())

        # 自动加载默认文件
        if os.path.isfile(default_path):
            self._load_file()

    # ── 文件操作 ──

    def _browse_file(self):
        path = tkinter.filedialog.askopenfilename(
            parent=self, title="选择 JSON 文件",
            filetypes=[("JSON 文件", "*.json"), ("所有文件", "*.*")],
        )
        if path:
            self._path_var.set(path)

    def _load_file(self):
        path = self._path_var.get().strip()
        if not path or not os.path.isfile(path):
            tkinter.messagebox.showerror("错误", "文件不存在", parent=self)
            return
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            tkinter.messagebox.showerror("加载失败", str(e), parent=self)
            return

        items = self._extract_names(data)
        if not items:
            tkinter.messagebox.showwarning("无数据", "未能从文件中提取到任何名称", parent=self)
            return
        self._items = items
        self._rebuild_checklist()

    def _extract_names(self, data) -> list[str]:
        """根据模式从 JSON 数据中提取名称列表（去重且保持顺序）。"""
        seen = set()
        result = []

        if self._mode == "category":
            # CategoryList.json: [{"name": "玄幻", ...}, ...]
            if isinstance(data, list):
                for item in data:
                    name = item.get("name", "").strip() if isinstance(item, dict) else ""
                    if name and name not in seen:
                        seen.add(name)
                        result.append(name)
        else:
            # BookList.json: {"都市": [{"book_name": ..., "author": ...}, ...], ...}
            key = "book_name" if self._mode == "book" else "author"
            if isinstance(data, dict):
                for category_books in data.values():
                    if not isinstance(category_books, list):
                        continue
                    for book in category_books:
                        if not isinstance(book, dict):
                            continue
                        val = book.get(key, "").strip() if isinstance(book.get(key), str) else ""
                        if val and val not in seen:
                            seen.add(val)
                            result.append(val)
            elif isinstance(data, list):
                for book in data:
                    if not isinstance(book, dict):
                        continue
                    val = book.get(key, "").strip() if isinstance(book.get(key), str) else ""
                    if val and val not in seen:
                        seen.add(val)
                        result.append(val)
        return result

    # ── 列表构建 ──

    def _rebuild_checklist(self):
        """Listbox 方案：一次性将所有条目插入，默认全选。"""
        lb = self._listbox
        lb.delete(0, "end")
        if self._items:
            lb.insert("end", *self._items)
            lb.selection_set(0, "end")
        self._update_count()

    def _update_count(self):
        sel   = len(self._listbox.curselection())
        total = self._listbox.size()
        self._count_lbl.config(text=f"{sel} / {total}")

    def _sel_all(self):
        self._listbox.selection_set(0, "end")
        self._update_count()

    def _desel_all(self):
        self._listbox.selection_clear(0, "end")
        self._update_count()

    def _invert_sel(self):
        lb    = self._listbox
        sel   = set(lb.curselection())
        total = lb.size()
        lb.selection_clear(0, "end")
        for i in range(total):
            if i not in sel:
                lb.selection_set(i)
        self._update_count()

    def _select_range(self):
        try:
            start = int(self._range_start_var.get().strip())
            end   = int(self._range_end_var.get().strip())
        except ValueError:
            tkinter.messagebox.showerror("参数错误", "请输入整数范围", parent=self)
            return
        total = self._listbox.size()
        if total == 0:
            return
        start = max(1, start)
        end   = min(total, end)
        if start > end:
            tkinter.messagebox.showerror("参数错误", f"起始序号不能大于结束序号，当前共 {total} 条", parent=self)
            return
        self._listbox.selection_clear(0, "end")
        self._listbox.selection_set(start - 1, end - 1)
        self._listbox.see(start - 1)
        self._update_count()

    # ── 导出 ──

    def _export(self):
        sel_indices = self._listbox.curselection()
        selected    = [self._listbox.get(i) for i in sel_indices]
        if not selected:
            tkinter.messagebox.showwarning("未选择", "请至少选择一项", parent=self)
            return

        if self._mode == "category" and self._timeout_var:
            raw = self._timeout_var.get().strip()
            try:
                timeout_val = int(raw)
            except ValueError:
                tkinter.messagebox.showerror("参数错误", "滚动超时秒数必须为整数", parent=self)
                return
            # 生成 [["分类名", 超时], ...] 格式
            export_data = [[name, timeout_val] for name in selected]
        else:
            # 生成 ["名称1", "名称2", ...] 格式
            export_data = selected

        param_dir = os.path.join(BASE_DIR, "param")
        os.makedirs(param_dir, exist_ok=True)
        save_path = tkinter.filedialog.asksaveasfilename(
            parent=self,
            title="保存参数 JSON",
            defaultextension=".json",
            filetypes=[("JSON 文件", "*.json"), ("所有文件", "*.*")],
            initialdir=param_dir,
        )
        if not save_path:
            return
        try:
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            tkinter.messagebox.showinfo(
                "导出成功",
                f"已导出 {len(selected)} 项到:\n{save_path}",
                parent=self,
            )
        except Exception as e:
            tkinter.messagebox.showerror("导出失败", str(e), parent=self)


# ─────────────────────────── 日志查看窗口 ───────────────────────────

class LogWindow(tk.Toplevel):
    """实时显示作业控制台日志输出的窗口。"""

    def __init__(self, master, title: str = "作业日志", initial_text: str = ""):
        super().__init__(master)
        self.title(title)
        self.configure(bg=BG)
        self.resizable(True, True)
        self.transient(master)
        self.minsize(600, 350)

        # 工具栏
        toolbar = tk.Frame(self, bg=HDR, pady=4)
        toolbar.pack(fill="x")
        tk.Button(
            toolbar, text="清空",
            font=("Microsoft YaHei UI", 8),
            bg=ITEM, fg=RED, activebackground=BORDER,
            relief="flat", padx=10, pady=2, cursor="hand2",
            command=self._clear,
        ).pack(side="left", padx=8)
        self._auto_scroll_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            toolbar, text="自动滚动",
            variable=self._auto_scroll_var,
            font=("Microsoft YaHei UI", 8),
            bg=HDR, fg=TEXT, selectcolor=ITEM,
            activebackground=HDR, activeforeground=TEXT,
        ).pack(side="left", padx=4)
        self._line_count_lbl = tk.Label(
            toolbar, text="0 行",
            font=("Consolas", 8), bg=HDR, fg=SUB,
        )
        self._line_count_lbl.pack(side="right", padx=8)

        # 文本区
        text_frame = tk.Frame(self, bg=BORDER, padx=1, pady=1)
        text_frame.pack(fill="both", expand=True, padx=6, pady=(0, 6))
        scrollbar = tk.Scrollbar(text_frame, bg=ITEM, troughcolor=HDR)
        self._text = tk.Text(
            text_frame,
            font=("Consolas", 9),
            bg=ITEM, fg=TEXT,
            insertbackground=TEXT,
            bd=0, wrap="word",
            highlightthickness=0,
            state="disabled",
            yscrollcommand=scrollbar.set,
        )
        scrollbar.config(command=self._text.yview)
        scrollbar.pack(side="right", fill="y")
        self._text.pack(fill="both", expand=True)
        self._count = 0

        if initial_text:
            self._text.config(state="normal")
            self._text.insert("end", initial_text)
            self._text.config(state="disabled")
            self._count = initial_text.count("\n")
            self._line_count_lbl.config(text=f"{self._count} 行")
            self._text.see("end")

        # 居中
        self.update_idletasks()
        w, h = 800, 500
        px = master.winfo_x() + max(0, (master.winfo_width()  - w) // 2)
        py = master.winfo_y() + max(0, (master.winfo_height() - h) // 2)
        self.geometry(f"{w}x{h}+{px}+{py}")
        self.bind("<Escape>", lambda e: self.destroy())

    def append(self, text: str):
        """追加一行日志。"""
        self._text.config(state="normal")
        self._text.insert("end", text + "\n")
        self._text.config(state="disabled")
        self._count += 1
        self._line_count_lbl.config(text=f"{self._count} 行")
        if self._auto_scroll_var.get():
            self._text.see("end")

    def _clear(self):
        self._text.config(state="normal")
        self._text.delete("1.0", "end")
        self._text.config(state="disabled")
        self._count = 0
        self._line_count_lbl.config(text="0 行")


# ─────────────────────────── 入口 ───────────────────────────

if __name__ == "__main__":
    app = ControlPanel()
    app.state("zoomed")   # Windows 最大化（占满全屏，保留任务栏）
    app.mainloop()
