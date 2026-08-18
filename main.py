import sys
import os

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QObject, QTimer
from PySide6.QtGui import QIcon

from config import cfg
from monitor import SlideShowMonitor
from sound_player import SoundPlayer
from ui.banner import BannerWindow
from ui.setup_window import SetupWindow
from ui.settings_window import SettingsWindow
from ui.resume_dialog import ResumeDialog
from ui.tray import SystemTray


class SlidesTimerApp(QObject):
    """Slides Timer 主应用"""

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

        # 组件
        self.banner = BannerWindow()
        self.monitor = SlideShowMonitor(self.on_slideshow_start, self.on_slideshow_end)

        # 窗口引用（防止被 GC）
        self._setup_window = None
        self._settings_window = None
        self._resume_dialog = None

        # 系统托盘
        self.tray = SystemTray(self.open_settings, self.on_exit)
        self.tray.show()

        # 计时器
        self._tick_timer = QTimer(self)
        self._tick_timer.setInterval(1000)
        self._tick_timer.timeout.connect(self._tick)

        # 启动监控
        self.monitor.start()

        print("Application Started. Waiting for PowerPoint/WPS...")

    def on_slideshow_start(self, ppt_path=None):
        print(f"Slideshow Started detected. Path: {ppt_path}")
        if self.timer_paused and not self.session_finished:
            print("Resuming previous session...")
            self.timer_paused = False
            self.timer_running = True
            self._tick_timer.start()
        else:
            self._start_new_session(ppt_path)

    def on_slideshow_end(self):
        print("Slideshow Ended detected.")
        if self.timer_running:
            self.timer_running = False
            self.timer_paused = True
            self._tick_timer.stop()

            if self.session_finished:
                self.reset_state()
            else:
                self.open_resume_dialog()

    def open_setup_window(self):
        self._setup_window = SetupWindow(None, self.start_timer, self.open_settings)
        self._setup_window.show()

    def open_settings(self):
        self._settings_window = SettingsWindow(None, cfg)
        self._settings_window.show()

    def open_resume_dialog(self):
        self._resume_dialog = ResumeDialog(None, self.on_user_resume, self.on_user_stop)
        self._resume_dialog.show()

    def _start_new_session(self, ppt_path=None):
        print(f"Starting new session with PPT path: {ppt_path}")
        if ppt_path:
            ppt_timers = cfg.get("ppt_timers")
            normalized_ppt_path = ppt_path.replace("\\", "/").lower()

            for stored_path, time_min in ppt_timers.items():
                normalized_stored_path = stored_path.replace("\\", "/").lower()
                if normalized_ppt_path == normalized_stored_path:
                    print(f"Found preset time for PPT: {time_min} minutes")
                    self.start_timer(time_min, show_notification=True)
                    return

            print("No preset time found for this PPT")

        self.open_setup_window()

    def start_timer(self, minutes, show_notification=False):
        print(f"Starting timer for {minutes} minutes")
        self.total_seconds = int(minutes * 60)
        self.remaining_seconds = self.total_seconds
        self.timer_running = True
        self.timer_paused = False
        self.session_finished = False
        self.warning_triggered = False
        self.critical_triggered = False

        if show_notification:
            self.show_banner(
                f"开始计时：{minutes}分钟",
                "#4CAF50",
                3
            )

        self._tick_timer.start()

    def _tick(self):
        if not self.timer_running:
            return

        self.remaining_seconds -= 1

        if self.remaining_seconds % 10 == 0:
            print(f"Time remaining: {self.remaining_seconds}s")

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

    def on_user_resume(self):
        print("User chose to resume later.")

    def on_user_stop(self):
        print("User chose to stop.")
        self.reset_state()

    def reset_state(self):
        self.timer_running = False
        self.timer_paused = False
        self.session_finished = False
        self.remaining_seconds = 0
        self._tick_timer.stop()

    def on_exit(self):
        self.monitor.stop()
        self._tick_timer.stop()
        self.tray.hide()
        QApplication.instance().quit()


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # 关闭窗口不退出，靠托盘维持

    # 设置应用图标
    icon_path = os.path.join(os.path.dirname(__file__), "icon.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    timer_app = SlidesTimerApp()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
