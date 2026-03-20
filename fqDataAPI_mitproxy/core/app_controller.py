"""
App 控制模块 - 使用 uiautomator2 操作番茄小说
"""
import time
from typing import Optional
from .logger import setup_logger

try:
    import uiautomator2 as u2
except ImportError:
    u2 = None


class AppController:
    """番茄小说 App 控制器"""
    
    PACKAGE_NAME = "com.dragon.read"
    ACTIVITY_MAIN = "com.dragon.read.activity.MainActivity"
    
    def __init__(self, device_manager):
        """
        初始化 App 控制器
        
        Args:
            device_manager: DeviceManager 实例
        """
        self.logger = setup_logger("app_controller")
        self.device_mgr = device_manager
        self.device = None
        
        if u2 is None:
            self.logger.error("uiautomator2 未安装，请运行: pip install uiautomator2")
            raise ImportError("uiautomator2 not available")
        
        self._init_device()
    
    def _init_device(self):
        """初始化 uiautomator2 设备"""
        try:
            self.logger.info(f"连接 uiautomator2: {self.device_mgr.serial}")
            self.device = u2.connect(self.device_mgr.serial)
            self.logger.info(f"✓ uiautomator2 已连接")
            self.logger.debug(f"设备信息: {self.device.info}")
        except Exception as e:
            self.logger.error(f"uiautomator2 连接失败: {e}")
            self.logger.info("提示: 请先运行初始化: python -m uiautomator2 init")
            raise
    
    def start_app(self) -> bool:
        """启动番茄小说 App"""
        try:
            self.logger.info(f"启动 App: {self.PACKAGE_NAME}")
            self.device.app_start(self.PACKAGE_NAME, stop=True)
            time.sleep(3)
            
            self.logger.info("✓ App 启动成功")
            return True
        
        except Exception as e:
            self.logger.error(f"启动 App 失败: {e}")
            return False
    
    def stop_app(self):
        """停止 App"""
        try:
            self.device.app_stop(self.PACKAGE_NAME)
            self.logger.info("✓ App 已停止")
        except Exception as e:
            self.logger.warning(f"停止 App 失败: {e}")
    
    def is_app_running(self) -> bool:
        """检查 App 是否运行"""
        try:
            result = self.device.app_current()
            return result and result.get("package") == self.PACKAGE_NAME
        except Exception:
            return False
    
    def wait_for_app(self, timeout: int = 10):
        """等待 App 启动"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.is_app_running():
                self.logger.info("✓ App 已启动")
                return True
            time.sleep(1)
        
        self.logger.warning("App 启动超时")
        return False
    
    def click_search_box(self) -> bool:
        """
        点击搜索框

        优先用 resourceId 查找，找不到时按屏幕宽度比例点击，屏幕方向不影响结果。
        """
        try:
            self.logger.info("点击搜索框")
            selectors = [
                {"resourceId": "com.dragon.read:id/search_input"},
                {"resourceId": "com.dragon.read:id/edt_search"},
                {"resourceId": "com.dragon.read:id/search_src_text"},
                {"resourceId": "com.dragon.read:id/search_text"},
                {"text": "搜索", "className": "android.widget.TextView"},
                {"hint": "搜索"},
            ]
            for sel in selectors:
                try:
                    if self.device(**sel).exists(timeout=1):
                        self.device(**sel).click()
                        time.sleep(0.5)
                        self.logger.info("✓ 搜索框已点击")
                        return True
                except Exception:
                    continue
            # 回退：按屏幕宽度比例点击（搜索框在中间左侧，约 20% 宽的位置，上方约 10% 处）
            w, h = self.device.window_size()
            self.device.click(int(w * 0.22), int(h * 0.09))
            time.sleep(0.5)
            self.logger.info("✓ 搜索框已点击（比例坐标回退）")
            return True
        except Exception as e:
            self.logger.error(f"点击搜索框失败: {e}")
            return False
    
    def search_book(self, book_name: str) -> bool:
        """
        搜索书籍
        
        Args:
            book_name: 书名
        
        Returns:
            是否成功
        """
        try:
            self.logger.info(f"搜索书籍: {book_name}")
            
            # 查找搜索框 - 多种选择器尝试
            search_selectors = [
                {"resourceId": "com.dragon.read:id/search_input"},
                {"resourceId": "com.dragon.read:id/edt_search"},
                {"text": "搜索"},
                {"hint": "搜索"},
            ]
            
            found = False
            for selector in search_selectors:
                try:
                    if self.device(**selector).exists(timeout=1):
                        self.logger.debug(f"找到搜索框: {selector}")
                        self.device(**selector).click()
                        time.sleep(0.5)
                        found = True
                        break
                except Exception:
                    continue
            
            if not found:
                self.logger.warning("未找到搜索框，使用主页搜索")
                # 尝试点击主页的搜索按钮
                self.device(resourceId="com.dragon.read:id/search_text").click()
                time.sleep(1)
            
            # 输入书名
            self.device.shell("input text " + book_name)
            time.sleep(1)
            
            # 按搜索
            self.device.press("enter")
            time.sleep(2)
            
            self.logger.info("✓ 搜索完成")
            return True
        
        except Exception as e:
            self.logger.error(f"搜索书籍失败: {e}")
            return False
    
    def click_first_search_result(self) -> bool:
        """点击搜索结果第一条"""
        try:
            self.logger.info("点击搜索结果第一条")

            # 等待搜索结果加载
            time.sleep(1)

            selectors = [
                {"resourceId": "com.dragon.read:id/it"},
                {"resourceId": "com.dragon.read:id/akn"},
                {"resourceId": "com.dragon.read:id/cover"},
                {"resourceId": "com.dragon.read:id/book_img"},
                {"resourceId": "com.dragon.read:id/book_cover"},
                {"resourceId": "com.dragon.read:id/iv_cover"},
                {"resourceId": "com.dragon.read:id/title"},
                {"resourceId": "com.dragon.read:id/book_name"},
            ]

            for selector in selectors:
                try:
                    if not self.device(**selector).exists(timeout=1):
                        continue
                    self.logger.debug(f"找到候选结果: {selector}")
                    self.device(**selector).click()
                    time.sleep(1.5)
                    self.logger.info("✓ 已点击搜索结果")
                    return True
                except Exception:
                    continue

            # 最终兜底：按比例坐标点击首条区域（横竖屏兼容）
            try:
                w, h = self.device.window_size()
                self.device.click(int(w * 0.20), int(h * 0.30))
                time.sleep(1.5)
                self.logger.info("✓ 已通过坐标兜底点击首条结果")
                return True
            except Exception:
                pass

            self.logger.warning("未找到可点击的搜索结果")
            return False
        
        except Exception as e:
            self.logger.error(f"点击搜索结果失败: {e}")
            return False
    
    def start_reading(self) -> bool:
        """开始阅读"""
        try:
            self.logger.info("尝试开始阅读")
            
            # 查找阅读按钮
            read_texts = ["开始阅读", "继续阅读", "立即阅读", "开始"]
            
            for text in read_texts:
                try:
                    if self.device(text=text).exists(timeout=1):
                        self.logger.debug(f"找到按钮: {text}")
                        self.device(text=text).click()
                        time.sleep(2)
                        self.logger.info("✓ 已开始阅读")
                        return True
                except Exception:
                    continue
            
            # 查找按钮 ID
            button_selectors = [
                {"resourceId": "com.dragon.read:id/start_read_btn"},
                {"resourceId": "com.dragon.read:id/btn_read"},
            ]
            
            for selector in button_selectors:
                try:
                    if self.device(**selector).exists(timeout=1):
                        self.logger.debug(f"找到按钮: {selector}")
                        self.device(**selector).click()
                        time.sleep(2)
                        self.logger.info("✓ 已开始阅读")
                        return True
                except Exception:
                    continue
            
            self.logger.warning("未找到阅读按钮，可能已在阅读页面")
            return True
        
        except Exception as e:
            self.logger.error(f"开始阅读失败: {e}")
            return False
    
    def next_page(self, times: int = 1):
        """
        翻页（向右滑动）
        
        Args:
            times: 翻页次数
        """
        try:
            width, height = self.device_mgr.get_screen_size()
            
            for i in range(times):
                # 从右向左滑动屏幕
                x_start = int(width * 0.8)
                y = int(height * 0.5)
                x_end = int(width * 0.2)
                
                self.logger.debug(f"翻页 {i+1}/{times}: ({x_start}, {y}) -> ({x_end}, {y})")
                self.device.swipe(x_start, y, x_end, y, 0.2)
                time.sleep(0.5)
            
            self.logger.info(f"✓ 翻页 {times} 次完成")
        
        except Exception as e:
            self.logger.error(f"翻页失败: {e}")
    
    def prev_page(self, times: int = 1):
        """
        上翻页（向左滑动）
        
        Args:
            times: 翻页次数
        """
        try:
            width, height = self.device_mgr.get_screen_size()
            
            for i in range(times):
                # 从左向右滑动屏幕
                x_start = int(width * 0.2)
                y = int(height * 0.5)
                x_end = int(width * 0.8)
                
                self.device.swipe(x_start, y, x_end, y, 0.2)
                time.sleep(0.5)
            
            self.logger.info(f"✓ 上翻页 {times} 次完成")
        
        except Exception as e:
            self.logger.error(f"上翻页失败: {e}")
    
    def take_screenshot(self, filename: str):
        """
        截图
        
        Args:
            filename: 文件名
        """
        try:
            self.device.screenshot(filename)
            self.logger.info(f"✓ 截图已保存: {filename}")
        except Exception as e:
            self.logger.error(f"截图失败: {e}")
    
    def get_current_activity(self) -> str:
        """获取当前 Activity"""
        try:
            result = self.device.app_current()
            activity = result.get("activity", "unknown") if result else "unknown"
            self.logger.debug(f"当前 Activity: {activity}")
            return activity
        except Exception as e:
            self.logger.error(f"获取 Activity 失败: {e}")
            return "unknown"
    
    def wait_for_element(self, selector: dict, timeout: int = 5) -> bool:
        """
        等待元素出现
        
        Args:
            selector: 元素选择器
            timeout: 超时时间（秒）
        
        Returns:
            是否找到
        """
        try:
            return self.device(**selector).exists(timeout=timeout)
        except Exception:
            return False
