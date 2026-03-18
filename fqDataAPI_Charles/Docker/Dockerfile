# ============================================================
#  番茄小说数据采集 - Docker 镜像
#  基础系统: Debian Bookworm Slim (Python 3.11)
#  运行环境: Linux x86_64，需配合 Android 模拟器容器使用
# ============================================================

FROM python:3.11-slim

# ---------- 系统依赖 ----------
# android-tools-adb : ADB 命令行工具
# wget / curl       : 网络工具（调试备用）
RUN apt-get update && apt-get install -y --no-install-recommends \
        android-tools-adb \
        wget \
        curl \
        netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# ---------- 工作目录 ----------
WORKDIR /app

# ---------- Python 依赖 ----------
# 先单独复制 requirements.txt，利用 Docker 层缓存加速重建
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# ---------- 项目代码 ----------
# 构建上下文为 fqDataAPI/ 目录（见 docker-compose.yml 中 context: ..）
COPY . .

# ---------- 运行时目录 ----------
RUN mkdir -p data logs

# ---------- 入口脚本 ----------
COPY Docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# 默认进入 bash，方便手动执行各采集脚本
ENTRYPOINT ["/entrypoint.sh"]
CMD ["bash"]
