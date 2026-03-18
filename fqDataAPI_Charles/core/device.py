"""
设备管理模块 - 处理 ADB 连接和设备检测
"""
import subprocess
import json
from typing import Optional
from .logger import setup_logger


class DeviceManager:
    """设备管理器"""
    
    def __init__(self, serial: Optional[str] = None):
        """
        初始化设备管理器
        
        Args:
            serial: 设备号，None 则自动检测
        """
        self.logger = setup_logger("device")
        self.serial = serial
        self.device = None
    
    def get_adb_devices(self) -> list:
        """获取所有 ADB 设备"""
        try:
            result = subprocess.run(
                ["adb", "devices"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            devices = []
            for line in result.stdout.split("\n")[1:]:
                if "\tdevice" in line:
                    devices.append(line.split("\t")[0])
            return devices
        except Exception as e:
            self.logger.error(f"获取设备列表失败: {e}")
            return []
    
    def connect(self, device_serial: Optional[str] = None) -> bool:
        """
        连接设备
        
        Args:
            device_serial: 设备号，None 则自动检测
        
        Returns:
            是否成功
        """
        target_serial = device_serial or self.serial
        
        # 如果未指定，自动检测
        if not target_serial:
            devices = self.get_adb_devices()
            if not devices:
                self.logger.error("未发现设备，请确保设备已连接或逍遥模拟器已启动")
                self.logger.info("逍遥模拟器连接命令: adb connect 127.0.0.1:21503")
                return False
            
            target_serial = devices[0]
            self.logger.info(f"自动选择设备: {target_serial}")
        
        # 尝试连接到模拟器（如果是 IP 地址）
        if ":" in target_serial and "." in target_serial:
            try:
                result = subprocess.run(
                    ["adb", "connect", target_serial],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                self.logger.info(f"连接结果: {result.stdout.strip()}")
            except Exception as e:
                self.logger.warning(f"连接设备失败: {e}")
        
        self.serial = target_serial
        
        # 验证连接
        try:
            result = subprocess.run(
                ["adb", "-s", target_serial, "shell", "getprop", "ro.build.version.release"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                self.logger.info(f"✓ 已连接到设备: {target_serial}")
                return True
            else:
                self.logger.error(f"设备连接验证失败: {result.stderr}")
                return False
        
        except Exception as e:
            self.logger.error(f"连接验证异常: {e}")
            return False
    
    def get_device_info(self) -> dict:
        """获取设备信息"""
        try:
            info = {}
            
            props = [
                ("ro.build.version.release", "Android版本"),
                ("ro.build.model", "设备型号"),
                ("ro.serialno", "序列号"),
                ("ro.build.id", "Build ID"),
            ]
            
            for prop, label in props:
                result = subprocess.run(
                    ["adb", "-s", self.serial, "shell", "getprop", prop],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    info[label] = result.stdout.strip()
            
            return info
        
        except Exception as e:
            self.logger.error(f"获取设备信息失败: {e}")
            return {}
    
    def shell_command(self, cmd: str):
        """执行 shell 命令"""
        try:
            result = subprocess.run(
                ["adb", "-s", self.serial, "shell"] + cmd.split(),
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0, result.stdout, result.stderr
        except Exception as e:
            self.logger.error(f"执行 shell 命令失败: {e}")
            return False, "", str(e)
    
    def get_screen_size(self) -> tuple:
        """获取屏幕分辨率"""
        try:
            result = subprocess.run(
                ["adb", "-s", self.serial, "shell", "wm", "size"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            # 输出格式: "Physical size: 1600x1000"
            if "Physical size" in result.stdout:
                size_str = result.stdout.split(":")[1].strip()
                width, height = map(int, size_str.split("x"))
                return (width, height)
            
            return (1600, 1000)  # 默认逍遥模拟器分辨率
        
        except Exception:
            return (1600, 1000)
