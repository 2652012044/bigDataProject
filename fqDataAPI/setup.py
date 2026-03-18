#!/usr/bin/env python
"""
项目初始化脚本
"""
import subprocess
import sys
from pathlib import Path


def main():
    print("=" * 60)
    print("番茄小说自动化控制 - 环境初始化")
    print("=" * 60)
    
    # 获取虚拟环境路径
    venv_path = Path(__file__).parent / "venv"
    
    if not venv_path.exists():
        print("错误: 虚拟环境不存在")
        print("请先创建虚拟环境: python -m venv venv")
        sys.exit(1)
    
    print("\n[1] 安装 Python 依赖...")
    pip_path = venv_path / "Scripts" / "pip.exe"
    result = subprocess.run(
        [str(pip_path), "install", "-r", "requirements.txt"],
        cwd=Path(__file__).parent
    )
    
    if result.returncode != 0:
        print("依赖安装失败")
        sys.exit(1)
    
    print("\n[2] 检查 ADB...")
    try:
        result = subprocess.run(["adb", "version"], capture_output=True, timeout=5)
        if result.returncode == 0:
            print("✓ ADB 已安装")
        else:
            raise Exception("ADB 检查失败")
    except Exception as e:
        print(f"✗ ADB 检查失败: {e}")
        print("请从以下网址下载 ADB:")
        print("https://developer.android.com/tools/releases/platform-tools")
        sys.exit(1)
    
    print("\n[3] 初始化 uiautomator2...")
    python_path = venv_path / "Scripts" / "python.exe"
    result = subprocess.run(
        [str(python_path), "-m", "uiautomator2", "init"],
        cwd=Path(__file__).parent
    )
    
    if result.returncode != 0:
        print("✗ uiautomator2 初始化失败")
        print("请确保设备已通过 ADB 连接")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("✓ 环境初始化完成！")
    print("=" * 60)
    print("\n使用方法:")
    print("  1. 启动逍遥模拟器")
    print("  2. 运行程序: venv\\Scripts\\python.exe main.py")


if __name__ == "__main__":
    main()
