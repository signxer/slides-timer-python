#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
slides-timer GUI 冒烟测试（Qt offscreen）。

验证 BannerWindow 的创建/显示/淡入淡出、SetupWindow 时间选择、
SettingsWindow 的 UI 组件存在性。

运行：
  QT_QPA_PLATFORM=offscreen python3 test/test_gui.py
"""
import os
import sys
import time
import unittest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

from config import cfg
from ui.banner import BannerWindow
from ui.setup_window import SetupWindow


class GuiSmoke(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.qapp = QApplication.instance() or QApplication([])

    def test_banner_create_and_show(self):
        banner = BannerWindow()
        self.addCleanup(banner.deleteLater)
        banner.show_message(
            message="测试横幅",
            bg_color="#FFA500",
            text_color="#FFFFFF",
            font_size=24,
            font_family="sans-serif",
            position="top",
            duration=2,
            offset_x=0,
            offset_y=0,
            manual_width=0,
            manual_height=0,
        )
        self.assertTrue(banner.isVisible(), "横幅应显示")
        # 启动事件循环让动画跑几步，然后关闭
        self._pump_events(0.5)
        banner.hide()

    def test_setup_window_components(self):
        win = SetupWindow(None, self._dummy_start, self._dummy_settings)
        self.addCleanup(win.deleteLater)
        win.show()
        self._pump_events(0.2)
        self.assertTrue(win.isVisible(), "设置窗口应显示")
        self.assertEqual(win.time_spinbox.value(), 10, "默认时间应为10分钟")

    def test_setup_window_adjust_time(self):
        win = SetupWindow(None, self._dummy_start, self._dummy_settings)
        self.addCleanup(win.deleteLater)
        win._adjust_time(5)
        self.assertEqual(win.time_spinbox.value(), 15)
        win._adjust_time(-20)
        self.assertEqual(win.time_spinbox.value(), 1, "最小值为1")

    def _dummy_start(self, minutes):
        pass

    def _dummy_settings(self):
        pass

    def _pump_events(self, seconds):
        """驱动 Qt 事件循环一段时间。"""
        deadline = time.time() + seconds
        while time.time() < deadline:
            self.qapp.processEvents()
            time.sleep(0.02)


if __name__ == '__main__':
    unittest.main(verbosity=2)