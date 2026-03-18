# 番茄小说自动化控制 - 快速开始

## 环境要求

- Python 3.8+
- Windows 系统
- 逍遥模拟器
- ADB 工具

## 安装步骤

### 1. 激活虚拟环境

```powershell
# Windows PowerShell
.\venv\Scripts\Activate.ps1

# 或使用 cmd
venv\Scripts\activate.bat
```

### 2. 安装依赖

```powershell
pip install -r requirements.txt
```

### 3. 连接逍遥模拟器

```powershell
# 默认端口 21503
adb connect 127.0.0.1:21503

# 验证连接
adb devices
```

### 4. 初始化 uiautomator2

```powershell
python -m uiautomator2 init
```

这会在模拟器中安装 ATX 服务和 app-uiautomator

## 使用方法

### 快速测试

```powershell
# 激活虚拟环境
.\venv\Scripts\Activate.ps1

# 运行主程序
python main.py
```

### 自定义脚本示例

创建文件 `my_script.py`:

```python
from core.device import DeviceManager
from core.app_controller import AppController

# 连接设备
device_mgr = DeviceManager()
device_mgr.connect()

# 控制 App
app = AppController(device_mgr)
app.start_app()
app.search_book("我不是戏神")
app.click_first_search_result()
app.start_reading()
app.next_page(times=5)
app.stop_app()
```

## 主要类和方法

### DeviceManager

```python
# 连接设备
device_mgr = DeviceManager()
device_mgr.connect()

# 获取设备信息
info = device_mgr.get_device_info()

# 获取屏幕尺寸
width, height = device_mgr.get_screen_size()

# 执行 shell 命令
success, stdout, stderr = device_mgr.shell_command("command")
```

### AppController

```python
# 初始化
app = AppController(device_mgr)

# 启动/停止 App
app.start_app()
app.stop_app()

# 搜索书籍
app.search_book("书名")

# 点击搜索结果
app.click_first_search_result()

# 开始阅读
app.start_reading()

# 翻页
app.next_page(times=3)         # 下翻
app.prev_page(times=3)         # 上翻

# 截图
app.take_screenshot("screenshot.png")

# 获取当前 Activity
activity = app.get_current_activity()

# 等待元素
app.wait_for_element({"text": "开始阅读"}, timeout=5)
```

## 常见问题

### Q1: "找不到模块" 错误

确保已激活虚拟环境:
```powershell
.\venv\Scripts\Activate.ps1
```

### Q2: 设备连接失败

```powershell
# 重启 ADB
adb kill-server
adb start-server

# 重新连接
adb connect 127.0.0.1:21503
```

### Q3: uiautomator2 初始化失败

```powershell
# 卸载旧版本
adb uninstall com.github.uiautomator
adb uninstall com.github.uiautomator.test

# 重新初始化
python -m uiautomator2 init
```

### Q4: 找不到 UI 元素

检查资源 ID 是否正确，可以使用以下工具查看:
- UIAutomator Viewer (Android SDK)
- Weditor: `python -m uiautomator2 weditor`

## 调试技巧

### 查看屏幕截图

```python
# 在脚本中添加
app.take_screenshot("debug.png")
```

### 查看当前 Activity

```python
activity = app.get_current_activity()
print(f"当前: {activity}")
```

### 查看元素树

```powershell
# 启动 weditor 可视化调试工具
python -m uiautomator2 weditor
```

## 项目结构

```
fqDataAPI/
├── venv/                    # 虚拟环境
├── core/
│   ├── __init__.py
│   ├── device.py           # 设备管理
│   ├── app_controller.py   # App 控制
│   └── logger.py           # 日志
├── logs/                   # 日志文件
├── main.py                 # 主程序
├── requirements.txt        # 依赖
├── setup.py               # 初始化脚本
└── description.txt
```

## 下一步

看到自动化能正常工作后，可以:

1. 扩展 `AppController` 以支持更多操作
2. 集成 Charles 代理拦截
3. 编写数据处理逻辑

## 支持

如有问题，请查看日志文件: `logs/app_controller.log`
