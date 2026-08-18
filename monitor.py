import sys
import time
import threading
import subprocess
import re
import os

from PySide6.QtCore import QObject, Signal


class SlideShowMonitor(QObject):
    """跨平台幻灯片放映状态监控"""

    slideshow_started = Signal(str)  # 携带 ppt_path
    slideshow_ended = Signal()

    # 关键词匹配（窗口标题中包含这些词表示正在放映）
    SLIDESHOW_KEYWORDS = [
        "放映", "演示", "幻灯片放映",
        "Slideshow", "Slide Show", "Presentation",
        "正在放映", "全屏",
    ]

    def __init__(self, on_start_callback, on_end_callback):
        self.on_start = on_start_callback
        self.on_end = on_end_callback
        self.running = False
        self.is_slideshow_active = False
        self.current_ppt_path = None
        self.thread = None
        self._stop_event = threading.Event()

    def start(self):
        if not self.running:
            self.running = True
            self._stop_event.clear()
            self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.thread.start()

    def stop(self):
        self.running = False
        self._stop_event.set()
        if self.thread:
            self.thread.join(timeout=3)

    def _monitor_loop(self):
        if sys.platform == "win32":
            self._monitor_windows()
        else:
            self._monitor_linux()

    # ── Linux 实现 ──────────────────────────────────────────────

    def _monitor_linux(self):
        """通过 xdotool 检测窗口标题判断放映状态"""
        while not self._stop_event.is_set():
            active, ppt_path = self._check_slideshow_linux()
            self._update_state(active, ppt_path)
            time.sleep(2)

    def _check_slideshow_linux(self):
        """使用 xdotool 搜索包含放映关键词的窗口"""
        try:
            result = subprocess.run(
                ["xdotool", "search", "--name", "--onlyvisible", "."],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode != 0:
                return False, None

            window_ids = result.stdout.strip().split("\n")
            for wid in window_ids:
                wid = wid.strip()
                if not wid:
                    continue
                try:
                    name_result = subprocess.run(
                        ["xdotool", "getwindowname", wid],
                        capture_output=True, text=True, timeout=3
                    )
                    title = name_result.stdout.strip()
                    if self._is_slideshow_title(title):
                        ppt_path = self._extract_ppt_path_from_title(title)
                        # 如果只提取到文件名（无路径），尝试通过进程信息获取完整路径
                        if ppt_path and not os.path.isabs(ppt_path):
                            full_path = self._resolve_full_path_linux(wid, ppt_path)
                            if full_path:
                                ppt_path = full_path
                        return True, ppt_path
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    continue
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        return False, None

    def _resolve_full_path_linux(self, window_id, filename):
        """通过窗口PID和进程打开的文件描述符查找PPT完整路径"""
        try:
            # 获取窗口所属进程 PID
            pid_result = subprocess.run(
                ["xdotool", "getwindowpid", window_id],
                capture_output=True, text=True, timeout=3
            )
            if pid_result.returncode != 0:
                return None
            pid = pid_result.stdout.strip()
            if not pid or not pid.isdigit():
                return None

            # 通过 /proc/PID/fd/ 查找该进程打开的文件描述符，
            # 匹配以 .ppt 或 .pptx 结尾的文件路径
            fd_dir = f"/proc/{pid}/fd"
            if not os.path.isdir(fd_dir):
                return None

            for fd_name in os.listdir(fd_dir):
                try:
                    link = os.readlink(os.path.join(fd_dir, fd_name))
                    if link.lower().endswith(('.ppt', '.pptx')):
                        # 确认文件名匹配
                        link_basename = os.path.basename(link)
                        if link_basename.lower() == filename.lower():
                            return link
                except (OSError, FileNotFoundError):
                    continue

            # 兜底：如果文件名匹配找到但路径不同，返回第一个 ppt 文件
            for fd_name in os.listdir(fd_dir):
                try:
                    link = os.readlink(os.path.join(fd_dir, fd_name))
                    if link.lower().endswith(('.ppt', '.pptx')):
                        return link
                except (OSError, FileNotFoundError):
                    continue

            return None
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            return None

    def _is_slideshow_title(self, title: str) -> bool:
        """判断窗口标题是否表示正在放映"""
        if not title:
            return False
        title_lower = title.lower()
        for keyword in self.SLIDESHOW_KEYWORDS:
            if keyword.lower() in title_lower:
                return True
        return False

    def _extract_ppt_path_from_title(self, title: str) -> str:
        """尝试从窗口标题中提取 PPT 文件名"""
        # 常见格式: "filename.pptx - PowerPoint 放映" 或 "filename - WPS 演示"
        match = re.search(r'([^\s/\\]+\.pptx?)', title, re.IGNORECASE)
        if match:
            return match.group(1)
        return None

    # ── Windows 实现（保留原有逻辑）────────────────────────────

    def _monitor_windows(self):
        """通过 COM 接口检测 PowerPoint/WPS 放映状态"""
        try:
            import pythoncom
            import win32com.client
            pythoncom.CoInitialize()
        except ImportError:
            # 无 pywin32，降级为 Linux 方式
            self._monitor_linux()
            return

        try:
            while not self._stop_event.is_set():
                active = False
                ppt_path = None

                for app_name in ["PowerPoint.Application", "Kwpp.Application", "WPS.Application"]:
                    is_active, path = self._check_app_windows(app_name)
                    if is_active:
                        active = True
                        ppt_path = path
                        break

                self._update_state(active, ppt_path)
                time.sleep(1)
        finally:
            try:
                pythoncom.CoUninitialize()
            except Exception:
                pass

    def _check_app_windows(self, app_name):
        """Windows COM 检测"""
        try:
            import win32com.client
            app = win32com.client.GetActiveObject(app_name)
            if app.SlideShowWindows.Count > 0:
                try:
                    if app_name == "PowerPoint.Application" and hasattr(app, 'ActivePresentation'):
                        pres = app.ActivePresentation
                        if pres and hasattr(pres, 'FullName'):
                            return True, pres.FullName
                    elif app.SlideShowWindows.Count > 0:
                        sw = app.SlideShowWindows(1)
                        if hasattr(sw, 'Presentation') and hasattr(sw.Presentation, 'FullName'):
                            return True, sw.Presentation.FullName
                except Exception:
                    pass
                return True, None
        except Exception:
            pass
        return False, None

    # ── 共用状态更新 ────────────────────────────────────────────

    def _update_state(self, active, ppt_path):
        ppt_path_changed = ppt_path != self.current_ppt_path

        if active and not self.is_slideshow_active:
            self.is_slideshow_active = True
            self.current_ppt_path = ppt_path
            self.slideshow_started.emit(ppt_path)
        elif not active and self.is_slideshow_active:
            self.is_slideshow_active = False
            self.current_ppt_path = None
            self.slideshow_ended.emit()
        elif active and self.is_slideshow_active and ppt_path_changed:
            self.current_ppt_path = ppt_path
            self.slideshow_started.emit(ppt_path)
