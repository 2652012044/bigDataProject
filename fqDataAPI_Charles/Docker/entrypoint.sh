#!/usr/bin/env bash
# ============================================================
#  容器启动入口脚本
#  职责：
#    1. 等待 Android 模拟器准备就绪
#    2. 通过 ADB TCP 连接模拟器
#    3. 初始化 uiautomator2（安装 ATX 服务）
#    4. 执行用户传入的命令（默认 bash）
# ============================================================

set -e

ANDROID_DEVICE="${ANDROID_DEVICE:-android-emulator:5555}"
MAX_WAIT=180   # 最多等待 180 秒

echo "=================================================="
echo " 番茄小说采集容器启动"
echo " Android 设备地址: ${ANDROID_DEVICE}"
echo "=================================================="

# ----------------------------------------------------------
# 1. 等待模拟器 ADB 端口可达
# ----------------------------------------------------------
HOST="${ANDROID_DEVICE%%:*}"
PORT="${ANDROID_DEVICE##*:}"
PORT="${PORT:-5555}"

echo "[1/3] 等待模拟器 ${HOST}:${PORT} 可连接..."
ELAPSED=0
until nc -z "$HOST" "$PORT" 2>/dev/null; do
    if [ "$ELAPSED" -ge "$MAX_WAIT" ]; then
        echo "  错误: 等待模拟器超时（${MAX_WAIT}s），请检查 android-emulator 容器是否正常启动"
        exit 1
    fi
    echo "  模拟器未就绪，等待 5s... (${ELAPSED}/${MAX_WAIT}s)"
    sleep 5
    ELAPSED=$((ELAPSED + 5))
done
echo "  端口可达，继续..."

# ----------------------------------------------------------
# 2. ADB 连接模拟器
# ----------------------------------------------------------
echo "[2/3] ADB 连接 ${ANDROID_DEVICE}..."
adb connect "${ANDROID_DEVICE}" || true

# 等待 adb devices 显示设备为 device 状态（而非 offline/unauthorized）
ELAPSED=0
until adb -s "${ANDROID_DEVICE}" get-state 2>/dev/null | grep -q "device"; do
    if [ "$ELAPSED" -ge "$MAX_WAIT" ]; then
        echo "  错误: ADB 连接超时，当前设备列表:"
        adb devices
        exit 1
    fi
    echo "  等待 ADB 设备就绪... (${ELAPSED}/${MAX_WAIT}s)"
    sleep 5
    ELAPSED=$((ELAPSED + 5))
done
echo "  ADB 连接成功:"
adb devices

# ----------------------------------------------------------
# 3. 初始化 uiautomator2（首次运行需安装 ATX 服务）
# ----------------------------------------------------------
echo "[3/3] 初始化 uiautomator2 ATX 服务..."
python -m uiautomator2 init --serial "${ANDROID_DEVICE}" \
    && echo "  uiautomator2 初始化完成" \
    || echo "  警告: uiautomator2 初始化失败，部分功能可能不可用（如已初始化可忽略）"

# ----------------------------------------------------------
# 4. 配置 Android 模拟器系统代理指向 Charles
#    只有让 Android 系统流量经过 Charles，App 的 API 才会被抓到
# ----------------------------------------------------------
if [ -n "$CHARLES_PROXY" ]; then
    PROXY_HOST="${CHARLES_PROXY%%:*}"
    PROXY_PORT="${CHARLES_PROXY##*:}"
    echo "[4/4] 配置 Android 系统代理 -> ${PROXY_HOST}:${PROXY_PORT}..."
    adb -s "${ANDROID_DEVICE}" shell settings put global http_proxy "${PROXY_HOST}:${PROXY_PORT}" \
        && echo "  ✓ Android 系统代理已设置" \
        || echo "  警告: Android 系统代理设置失败，Charles 可能无法抓到 App 流量"
else
    echo "[4/4] 未指定 CHARLES_PROXY，跳过 Android 代理配置（Charles 将无法抓到 App 流量）"
fi

echo ""
echo "=================================================="
echo " 环境就绪，执行命令: $*"
echo "=================================================="
echo ""

# ----------------------------------------------------------
# 5. 执行传入命令（默认 bash）
# ----------------------------------------------------------
exec "$@"
