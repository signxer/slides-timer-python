import sys
import os

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QObject, QTimer, Qt, QSize
from PySide6.QtGui import QIcon

from config import cfg
from monitor import SlideShowMonitor
from sound_player import SoundPlayer
from ui.tray import SystemTray
from ui.banner import BannerOverlay
from ui.setup_window import SetupWindow
from ui.settings_window import SettingsWindow
from ui.resume_dialog import ResumeDialog


class SlidesTimerApp(QObject):
    """Slides Timer 主应用 — 纯逻辑层，UI 由 MainWindow 承载"""

    def __init__(self):
        super().__init__()

        # 状态
        self.timer_running = False
        self.timer_paused = False
        self.remaining_seconds = 0
        self.total_seconds = 0
        self.warning_triggered = False
        self.critical_triggered = False
        self.session_finished = False
        self._current_minutes = 0

        # Banner 横幅（全局浮动覆盖层）
        self.banner = BannerOverlay()

        # 演示监控
        self.monitor = SlideShowMonitor(self.on_slideshow_start, self.on_slideshow_end)

        # 窗口引用（防止 GC）
        self._settings_window = None
        self._resume_dialog = None

        # 计时器
        self._tick_timer = QTimer(self)
        self._tick_timer.setInterval(1000)
        self._tick_timer.timeout.connect(self._tick)

        # 主窗口引用（由 main() 注入）
        self.main_window = None

        # 托盘
        self.tray = SystemTray(self.on_tray_settings, self.on_exit)
        self.tray.on_show_window = self._show_main_window
        self.tray.on_start_timer = self.on_tray_start
        self.tray.show()

        # 启动监控
        self.monitor.start()

        print("Application Started. Waiting for PowerPoint/WPS...")

    # ── 计时核心逻辑 ──────────────────────────────────────────

    def on_slideshow_start(self, ppt_path=None):
        print(f"Slideshow Started. Path: {ppt_path}")
        # 确保在主线程执行 UI 操作（monitor 在后台线程中调用）
        QTimer.singleShot(0, lambda: self._on_slideshow_start(ppt_path))

    def _on_slideshow_start(self, ppt_path=None):
        if self.timer_paused and not self.session_finished:
            print("Resuming previous session...")
            self.timer_paused = False
            self.timer_running = True
            self._tick_timer.start()
            self._emit_update()
        else:
            self._start_new_session(ppt_path)

    def on_slideshow_end(self):
        print("Slideshow Ended.")
        # 确保在主线程执行 UI 操作（monitor 在后台线程中调用）
        QTimer.singleShot(0, lambda: self._on_slideshow_end())

    def _on_slideshow_end(self):
        if self.timer_running:
            self.timer_running = False
            self.timer_paused = True
            self._tick_timer.stop()
            if self.session_finished:
                self.reset_state()
            else:
                self._open_resume_dialog()
            self._emit_update()

    def start_timer(self, minutes, show_notification=False):
        print(f"Starting timer for {minutes} minutes")
        self._current_minutes = minutes
        self.total_seconds = int(minutes * 60)
        self.remaining_seconds = self.total_seconds
        self.timer_running = True
        self.timer_paused = False
        self.session_finished = False
        self.warning_triggered = False
        self.critical_triggered = False

        if show_notification:
            self.show_banner(f"开始计时：{minutes}分钟", "#4CAF50", 3)

        self._tick_timer.start()
        self._emit_update()

    def pause_timer(self):
        if self.timer_running:
            self.timer_running = False
            self.timer_paused = True
            self._tick_timer.stop()
            self._emit_update()

    def resume_timer(self):
        if self.timer_paused and not self.session_finished:
            self.timer_paused = False
            self.timer_running = True
            self._tick_timer.start()
            self._emit_update()

    def stop_timer(self):
        self.reset_state()
        self._emit_update()

    def _tick(self):
        if not self.timer_running:
            return

        self.remaining_seconds -= 1
        self._emit_update()

        # 警告触发
        trigger_type = cfg.get("warning_trigger_type")
        trigger_val = cfg.get("warning_trigger_value")
        should_warn = False

        if trigger_type == "percent":
            threshold = self.total_seconds * (trigger_val / 100.0)
            if 0 < self.remaining_seconds <= threshold:
                should_warn = True
        else:
            threshold = trigger_val * 60
            if 0 < self.remaining_seconds <= threshold:
                should_warn = True

        if not self.warning_triggered and should_warn:
            self.warning_triggered = True
            self.show_banner(
                cfg.get("text_warning"),
                cfg.get("bg_color_warning"),
                cfg.get("duration_warning")
            )
            SoundPlayer.play(cfg.get("sound_warning_path") if cfg.get("sound_warning_enabled") else "")

        # 时间到
        if not self.critical_triggered and self.remaining_seconds <= 0:
            self.critical_triggered = True
            self.session_finished = True
            self.show_banner(
                cfg.get("text_critical"),
                cfg.get("bg_color_critical"),
                cfg.get("duration_critical")
            )
            SoundPlayer.play(cfg.get("sound_critical_path") if cfg.get("sound_critical_enabled") else "")
            self.timer_running = False
            self._tick_timer.stop()

    def _emit_update(self):
        """通知主窗口更新 UI"""
        if self.main_window and hasattr(self.main_window, 'on_timer_update'):
            self.main_window.on_timer_update(
                running=self.timer_running,
                paused=self.timer_paused,
                remaining=self.remaining_seconds,
                total=self.total_seconds,
                session_finished=self.session_finished,
            )

    # ── 窗口 / 对话框 ─────────────────────────────────────────

    def _start_new_session(self, ppt_path=None):
        print(f"Starting new session. PPT: {ppt_path}")
        if ppt_path:
            # 检查是否在忽略列表
            ignored = set(cfg.get("ignored_ppts") or [])
            if ppt_path in ignored:
                print(f"PPT is in ignored list, skipping timer")
                return

            ppt_timers = cfg.get("ppt_timers")
            normalized_ppt_path = ppt_path.replace("\\", "/").lower()
            for stored_path, time_min in ppt_timers.items():
                normalized_stored_path = stored_path.replace("\\", "/").lower()
                if normalized_ppt_path == normalized_stored_path:
                    # 再次检查忽略（用存储路径）
                    if stored_path in ignored:
                        print(f"PPT is in ignored list, skipping timer")
                        return
                    print(f"Found preset time for PPT: {time_min} minutes")
                    self.start_timer(time_min, show_notification=True)
                    return
            print("No preset time found for this PPT")

        win = SetupWindow(self.start_timer, self.open_settings, parent=self.main_window)
        win.show()
        win.raise_()
        win.activateWindow()
        QTimer.singleShot(200, win.raise_)
        QTimer.singleShot(500, win.raise_)

    def open_settings(self):
        if self._settings_window is None or not self._settings_window.isVisible():
            self._settings_window = SettingsWindow(cfg)
        self._settings_window.show()
        self._settings_window.raise_()

    def _open_resume_dialog(self):
        dlg = ResumeDialog(self.on_user_resume, self.on_user_stop)
        # 设置父窗口确保对话框在正确层级显示
        if self.main_window:
            dlg.setParent(self.main_window)
        dlg.exec()

    # ── 回调 ──────────────────────────────────────────────────

    def on_user_resume(self):
        print("User chose to resume later.")

    def on_user_stop(self):
        print("User chose to stop.")
        self.reset_state()
        self._emit_update()

    def on_tray_settings(self):
        self.open_settings()

    def on_tray_start(self):
        win = SetupWindow(self.start_timer, self.open_settings, parent=self.main_window)
        win.show()
        win.raise_()
        win.activateWindow()

    def reset_state(self):
        self.timer_running = False
        self.timer_paused = False
        self.session_finished = False
        self.remaining_seconds = 0
        self.warning_triggered = False
        self.critical_triggered = False
        self._tick_timer.stop()

    def _show_main_window(self):
        """显示主窗口（从托盘恢复）"""
        if self.main_window:
            self.main_window.show()
            self.main_window.raise_()
            self.main_window.activateWindow()

    def on_exit(self):
        self.monitor.stop()
        self._tick_timer.stop()
        self.tray.hide()
        QApplication.instance().quit()

    def show_banner(self, text, bg_color, duration):
        self.banner.show_message(
            message=text,
            bg_color=bg_color,
            text_color=cfg.get("text_color"),
            font_size=cfg.get("font_size"),
            font_family=cfg.get("font_family"),
            position=cfg.get("position"),
            duration=duration,
            offset_x=cfg.get("offset_x"),
            offset_y=cfg.get("offset_y"),
            manual_width=cfg.get("screen_width"),
            manual_height=cfg.get("screen_height"),
        )


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    icon_path = os.path.join(os.path.dirname(__file__), "icon.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    # 启动页（使用 QFluentWidgets 的 SplashScreen）
    from qfluentwidgets import SplashScreen
    splash = SplashScreen(QIcon(icon_path), enableShadow=True)
    splash.setIconSize(QSize(128, 128))
    splash.show()

    # 处理事件让启动页显示出来
    app.processEvents()

    # 延迟导入避免循环
    from ui.main_window import MainWindow

    timer_app = SlidesTimerApp()
    window = MainWindow(timer_app)
    timer_app.main_window = window
    window.show()

    # 关闭启动页
    splash.finish()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()