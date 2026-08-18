import json
import os
import sys


def get_app_dir():
    """获取应用根目录（兼容 PyInstaller 打包）"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


CONFIG_FILE = os.path.join(get_app_dir(), "config.json")

DEFAULT_CONFIG = {
    "reminder_duration": 5,  # seconds (Legacy, kept for compat if needed, but we will use specific ones)
    "duration_warning": 5,
    "duration_critical": 5,
    "sound_warning_enabled": False,
    "sound_warning_path": "",
    "sound_critical_enabled": False,
    "sound_critical_path": "",
    "warning_trigger_type": "percent", # "percent" or "time_remaining"
    "warning_trigger_value": 33, # 33% or 60 seconds
    "font_family": "Segoe UI",
    "font_size": 24,
    "text_color": "#FFFFFF",
    "bg_color_warning": "#FFA500",  # Orange for 1/3 reminder
    "bg_color_critical": "#FF0000", # Red for time up
    "text_warning": "严控会议时长 剩余1/3时间",
    "text_critical": "严控会议时长 时间到",
    "position": "top",  # top, bottom
    "opacity": 0.9,
    "offset_x": 0,
    "offset_y": 0,
    "screen_width": 0, # 0 means auto
    "screen_height": 0, # 0 means auto
    "ppt_timers": {}, # PPT文件路径 -> 时间(分钟)
    "ignored_ppts": [] # 不计时的PPT文件路径列表
}

class ConfigManager:
    def __init__(self):
        self.config = DEFAULT_CONFIG.copy()
        self.load()

    def load(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.config.update(data)
            except Exception as e:
                print(f"Error loading config: {e}")

    def save(self):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")

    def get(self, key):
        return self.config.get(key, DEFAULT_CONFIG.get(key))

    def set(self, key, value):
        self.config[key] = value
        self.save()

# Global instance
cfg = ConfigManager()
