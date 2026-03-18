# 番茄小说采集 — Docker 部署指南

本目录包含将项目运行在 **Linux** 系统上所需的全部 Docker 配置文件。

## 文件说明

```
Docker/
├── Dockerfile          # Python 采集应用镜像
├── docker-compose.yml  # 服务编排（采集应用 + Android 模拟器）
├── entrypoint.sh       # 容器启动脚本（自动连接 ADB、初始化 uiautomator2）
├── .dockerignore       # 构建上下文排除规则
└── README.md           # 本文档
```

---

## 架构说明

```
┌─────────────────────────────────────────────────────────┐
│ 宿主机 (Linux)                                          │
│                                                         │
│  ┌──────────────────┐    ADB TCP     ┌───────────────┐  │
│  │   fq-app 容器     │ ──────────────> │ android-      │  │
│  │  (Python 采集)   │ <────────────── │ emulator 容器 │  │
│  └────────┬─────────┘                └───────────────┘  │
│           │ HTTP PROXY                                   │
│           ▼                                              │
│  ┌──────────────────┐                                    │
│  │  Charles Proxy   │  (宿主机运行，拦截番茄小说 API)   │
│  └──────────────────┘                                    │
└─────────────────────────────────────────────────────────┘
```

| 组件 | 运行位置 | 说明 |
|------|--------|------|
| Python 采集脚本 | `fq-app` 容器 | 包含所有 .py 文件 + ADB |
| Android 模拟器 | `android-emulator` 容器 | `budtmo/docker-android:emulator_11.0`，运行番茄小说 App |
| Charles Proxy | **宿主机** | 负责 HTTPS 抓包，容器通过代理环境变量接入 |

---

## 前置条件

### 1. 宿主机要求

- Linux x86_64（推荐 Ubuntu 22.04 / Debian 12）
- Docker >= 24.0
- Docker Compose >= 2.20
- **KVM 硬件虚拟化**（Android 模拟器必须）

检查 KVM 是否可用：
```bash
ls /dev/kvm
# 有输出则支持，否则需要在 BIOS 中开启 VT-x / AMD-V
```

### 2. 安装 Charles Proxy（可选，用于 API 抓包）

在宿主机安装 Charles：https://www.charlesproxy.com/download/

启动后默认监听 `0.0.0.0:8888`，开启 HTTPS 代理并安装根证书。

---

## 快速开始

### 第一步：构建镜像（在 fqDataAPI/ 目录下执行）

```bash
cd fqDataAPI
docker compose -f Docker/docker-compose.yml build
```

### 第二步：启动 Android 模拟器

```bash
docker compose -f Docker/docker-compose.yml up -d android-emulator
```

等待约 2~5 分钟，模拟器启动完成后可通过浏览器访问 noVNC 界面：

```
http://localhost:6080
```

密码默认为空，打开后可看到 Android 模拟器界面。**请手动安装番茄小说 APK**：
```bash
# 将 APK 复制进容器并安装
docker cp 番茄小说.apk android-emulator:/tmp/fq.apk
docker exec android-emulator adb install /tmp/fq.apk
```

### 第三步：启动采集容器

```bash
# 指定 Charles 代理 IP（将 192.168.1.100 替换为宿主机实际 IP）
CHARLES_PROXY=192.168.1.100:8888 \
docker compose -f Docker/docker-compose.yml run --rm fq-app
```

> 容器会自动：等待模拟器就绪 → ADB 连接 → 初始化 uiautomator2 → 进入 bash

### 第四步：在容器内运行采集脚本

```bash
# 进入 bash 后，正常运行各脚本
python searchbook.py
python getBookListByTypeAPI.py
python getCategoryListAPI.py
python getUserAPI.py
```

采集结果会实时同步到宿主机的 `fqDataAPI/data/` 目录。

---

## 环境变量说明

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `ANDROID_DEVICE` | `android-emulator:5555` | Android 设备 ADB 地址 |
| `CHARLES_PROXY` | `host.docker.internal:8888` | Charles 代理地址 |
| `HTTP_PROXY` / `HTTPS_PROXY` | 同 `CHARLES_PROXY` | requests 库自动使用 |

---

## 不使用模拟器（连接真实设备）

如果宿主机通过 USB 连接了真实 Android 手机，可跳过 `android-emulator` 服务，直接将 ADB 暴露给容器：

```bash
# 在宿主机启动 ADB TCP 服务
adb tcpip 5555

# 获取手机 IP（假设为 192.168.1.50）
adb shell ip addr show wlan0

# 启动采集容器，直连手机
ANDROID_DEVICE=192.168.1.50:5555 \
docker compose -f Docker/docker-compose.yml run --rm fq-app
```

---

## 常见问题

**Q: 模拟器启动后 ADB 一直显示 offline**
- 检查宿主机 KVM 是否正常：`dmesg | grep kvm`
- 尝试进入模拟器容器重启 ADB：`docker exec android-emulator adb kill-server && adb start-server`

**Q: uiautomator2 初始化失败**
- 初始化只需成功一次，ATX 服务安装后会持久化在模拟器数据卷中
- 手动执行：`docker exec -it <容器ID> python -m uiautomator2 init`

**Q: Charles 无法抓到请求**
- 确认 `HTTP_PROXY` / `HTTPS_PROXY` 环境变量已正确设置
- 确认 Charles 监听 `0.0.0.0` 而非 `127.0.0.1`
- Linux 宿主机需将 `host.docker.internal` 替换为实际 IP（`CHARLES_PROXY=<host_ip>:8888`）
