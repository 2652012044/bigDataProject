"""总控面板 — 显示 mitmproxy 代理和逍遥模拟器的运行状态及连接关系

运行方式:
    python control.py
"""

import os
import socket
import subprocess
import threading
import time
import tkinter as tk
import tkinter.simpledialog
import urllib.request
from datetime import datetime

# ─────────────────────────── 配置（按需修改）───────────────────────────

SLOTS = [
    {
        "name":           "实例 1",
        "proxy_port":     8080,
        "emulator_serial": "127.0.0.1:21503",
        "expected_proxy": "172.19.32.1:8080",
    },
    {
        "name":           "实例 2",
        "proxy_port":     8081,
        "emulator_serial": "127.0.0.1:21513",
        "expected_proxy": "172.19.32.1:8081",
    },
    {
        "name":           "实例 3",
        "proxy_port":     8082,
        "emulator_serial": "127.0.0.1:21523",
        "expected_proxy": "172.19.32.1:8082",
    },
]

REFRESH_INTERVAL_MS = 5000   # 自动刷新间隔（毫秒）
HOST_IP    = "172.19.32.1"   # 宿主机对模拟器可见的 IP
ADDON_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "Docker", "mitmproxy_addon.py",
)

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
        port   = s["proxy_port"]
        serial = s["emulator_serial"]

        port_up   = _port_open(port)
        addon     = _addon_ok(port) if port_up else False
        emu_st    = devs.get(serial, "离线")
        emu_ok    = (emu_st == "device")
        proxy_val = _emu_proxy(serial) if emu_ok else ""
        proxy_match = (proxy_val == s["expected_proxy"])

        result.append({
            "name":           s["name"],
            "proxy_port":     port,
            "port_up":        port_up,
            "addon":          addon,
            "serial":         serial,
            "emu_ok":         emu_ok,
            "emu_st":         emu_st,
            "proxy_val":      proxy_val,
            "proxy_match":    proxy_match,
            "expected_proxy": s["expected_proxy"],
            "all_ok": port_up and addon and emu_ok and proxy_match,
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


# ─────────────────────────── GUI ───────────────────────────

class ControlPanel(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("番茄小说采集 — 总控面板")
        self.configure(bg=BG)
        self.resizable(True, False)  # 允许横向拉伸
        self.minsize(680, 200)

        self._refreshing    = False
        self._job           = None
        self._cards         = []              # list of widget-dicts, one per slot
        self._procs: dict   = {}              # slot_idx → subprocess.Popen
        self._last_statuses = [None] * len(SLOTS)   # 上一次采集结果

        self._build_ui()
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

    def _build_body(self):
        # ── Canvas + Scrollbar，窗口高度限制在屏幕 85% 以内 ──
        max_h = int(self.winfo_screenheight() * 0.85) - 110  # 减去 header+footer

        container = tk.Frame(self, bg=BG)
        container.pack(fill="both", expand=True)

        self._canvas = tk.Canvas(
            container, bg=BG, bd=0, highlightthickness=0, width=660
        )
        scrollbar = tk.Scrollbar(
            container, orient="vertical", command=self._canvas.yview
        )
        self._canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)

        body = tk.Frame(self._canvas, bg=BG, padx=14, pady=8)
        self._body_id = self._canvas.create_window((0, 0), window=body, anchor="nw")

        for i, slot in enumerate(SLOTS):
            w = self._make_card(body, slot, i)
            w["outer"].pack(fill="x", pady=5)
            self._cards.append(w)

        # 计算内容真实高度，决定是否需要滚动条
        body.update_idletasks()
        content_h = body.winfo_reqheight()
        canvas_h  = min(content_h, max_h)
        self._canvas.configure(height=canvas_h)

        body.bind(
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
        toggle_btn = tk.Button(
            title_row,
            text="开启代理",
            font=("Microsoft YaHei UI", 8),
            bg=ITEM, fg=GREEN,
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

        return {
            "outer":  outer,
            "badge":  badge,
            "toggle": toggle_btn,
            "arrow":  arrow_lbl,
            "link":   link_lbl,
            **proxy_w,
            **emu_w,
        }

    def _make_proxy_box(self, parent, port: int):
        box = tk.Frame(parent, bg=ITEM, padx=12, pady=8)
        tk.Label(
            box, text="MITMPROXY",
            font=("Consolas", 7, "bold"),
            bg=ITEM, fg=SUB,
        ).pack(anchor="w")
        p_port = tk.Label(
            box, text=f":{port}",
            font=("Consolas", 16, "bold"),
            bg=ITEM, fg=BLUE,
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
        return box, {"e_st": e_st, "e_pr": e_pr}

    # ────── 状态应用 ──────

    def _apply_status(self, statuses):
        for i, s in enumerate(statuses):
            w = self._cards[i]

            # mitmproxy 运行状态
            if s["port_up"]:
                w["p_run"].config(text="● 运行中", fg=GREEN)
            else:
                w["p_run"].config(text="● 未运行", fg=RED)

            # addon 健康状态
            if not s["port_up"]:
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
            elif s["port_up"] and s["emu_ok"]:
                w["arrow"].config(fg=YELLOW)
                w["badge"].config(text="⚠ 配置异常", fg=YELLOW)
            else:
                w["arrow"].config(fg=RED)
                w["badge"].config(text="✗ 离线", fg=RED)

            # 箭头下方的连接地址标注
            if s["port_up"] and s["emu_ok"]:
                w["link"].config(text=s["expected_proxy"])
            else:
                w["link"].config(text="")

            # 记录最新状态，供 _toggle_proxy 使用
            self._last_statuses[i] = s

            # 还原 toggle 按钮文字与状态
            currently_on = s["port_up"] and s["proxy_match"]
            if currently_on:
                w["toggle"].config(state="normal", text="关闭代理", fg=RED)
            else:
                w["toggle"].config(state="normal", text="开启代理", fg=GREEN)

        now = datetime.now().strftime("%H:%M:%S")
        self._foot_time.config(
            text=f"最后刷新: {now}   刷新间隔: {REFRESH_INTERVAL_MS // 1000}s"
        )
        self._hdr_right.config(text="")

    # ────── 代理切换 ──────

    def _ask_port(self, default_port: int):
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
        currently_on = bool(st and st.get("port_up") and st.get("proxy_match"))
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
        """开启指定 slot 的代理：启动 mitmdump 并配置模拟器代理。"""
        port = self._ask_port(SLOTS[idx]["proxy_port"])
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


# ─────────────────────────── 入口 ───────────────────────────

if __name__ == "__main__":
    ControlPanel().mainloop()
