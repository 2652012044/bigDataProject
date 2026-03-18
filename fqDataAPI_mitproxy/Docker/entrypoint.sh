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
MITM_PROXY="${MITM_PROXY:-mitmproxy:8080}"
MITM_CERT_PATH="${MITM_CERT_PATH:-/mitmproxy/mitmproxy-ca-cert.cer}"
MAX_WAIT=180   # 最多等待 180 秒

echo "=================================================="
echo " 番茄小说采集容器启动"
echo " Android 设备地址: ${ANDROID_DEVICE}"
echo " mitmproxy 地址: ${MITM_PROXY}"
echo "=================================================="

wait_for_port() {
    local host="$1"
    local port="$2"
    local label="$3"

    ELAPSED=0
    until nc -z "$host" "$port" 2>/dev/null; do
        if [ "$ELAPSED" -ge "$MAX_WAIT" ]; then
            echo "  错误: 等待 ${label} 超时（${MAX_WAIT}s）"
            exit 1
        fi
        echo "  ${label} 未就绪，等待 5s... (${ELAPSED}/${MAX_WAIT}s)"
        sleep 5
        ELAPSED=$((ELAPSED + 5))
    done
}

install_mitm_certificate() {
    if [ ! -f "$MITM_CERT_PATH" ]; then
        echo "  警告: 未找到 mitmproxy 证书 ${MITM_CERT_PATH}，HTTPS 解密可能失败"
        return 0
    fi

    CERT_HASH=$(openssl x509 -inform PEM -subject_hash_old -in "$MITM_CERT_PATH" | head -1)
    if [ -z "$CERT_HASH" ]; then
        echo "  警告: 计算 mitmproxy 证书 hash 失败"
        return 0
    fi

    TEMP_CERT="/tmp/${CERT_HASH}.0"
    cp "$MITM_CERT_PATH" "$TEMP_CERT"

    adb -s "${ANDROID_DEVICE}" root >/dev/null 2>&1 || true
    adb -s "${ANDROID_DEVICE}" remount >/dev/null 2>&1 || true
    adb -s "${ANDROID_DEVICE}" push "$TEMP_CERT" "/sdcard/${CERT_HASH}.0" >/dev/null

    if adb -s "${ANDROID_DEVICE}" shell "cp /sdcard/${CERT_HASH}.0 /system/etc/security/cacerts/${CERT_HASH}.0 && chmod 644 /system/etc/security/cacerts/${CERT_HASH}.0" >/dev/null 2>&1; then
        echo "  ✓ mitmproxy CA 已安装到 Android 系统证书库"
        adb -s "${ANDROID_DEVICE}" shell rm "/sdcard/${CERT_HASH}.0" >/dev/null 2>&1 || true
        return 0
    fi

    echo "  警告: 自动安装 mitmproxy CA 失败，请手动检查模拟器是否允许写入系统证书库"
}

# ----------------------------------------------------------
# 1. 等待 mitmproxy 和模拟器端口可达
# ----------------------------------------------------------
HOST="${ANDROID_DEVICE%%:*}"
PORT="${ANDROID_DEVICE##*:}"
PORT="${PORT:-5555}"
PROXY_HOST="${MITM_PROXY%%:*}"
PROXY_PORT="${MITM_PROXY##*:}"
PROXY_PORT="${PROXY_PORT:-8080}"

echo "[1/5] 等待 mitmproxy ${PROXY_HOST}:${PROXY_PORT} 可连接..."
wait_for_port "$PROXY_HOST" "$PROXY_PORT" "mitmproxy"
echo "  mitmproxy 已就绪"

echo "[2/5] 等待模拟器 ${HOST}:${PORT} 可连接..."
wait_for_port "$HOST" "$PORT" "Android 模拟器"
echo "  端口可达，继续..."

# ----------------------------------------------------------
# 2. ADB 连接模拟器
# ----------------------------------------------------------
echo "[3/5] ADB 连接 ${ANDROID_DEVICE}..."
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
echo "[4/5] 初始化 uiautomator2 ATX 服务..."
python -m uiautomator2 init --serial "${ANDROID_DEVICE}" \
    && echo "  uiautomator2 初始化完成" \
    || echo "  警告: uiautomator2 初始化失败，部分功能可能不可用（如已初始化可忽略）"

# ----------------------------------------------------------
# 4. 安装 mitmproxy 证书并配置 Android 系统代理
# ----------------------------------------------------------
echo "[5/5] 安装 mitmproxy 证书并配置 Android 系统代理..."
install_mitm_certificate

if [ -n "$MITM_PROXY" ]; then
    adb -s "${ANDROID_DEVICE}" shell settings put global http_proxy "${PROXY_HOST}:${PROXY_PORT}" \
        && echo "  ✓ Android 系统代理已设置为 ${PROXY_HOST}:${PROXY_PORT}" \
        || echo "  警告: Android 系统代理设置失败，mitmproxy 可能无法抓到 App 流量"
else
    echo "  警告: 未指定 MITM_PROXY，跳过 Android 代理配置"
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
