#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统托盘图标 — 使用 QFluentWidgets SystemTrayMenu 提供圆角现代菜单。
"""
import os
from PySide6.QtWidgets import QSystemTrayIcon, QApplication
from PySide6.QtGui import QIcon, QAction
from qfluentwidgets import SystemTrayMenu, FluentIcon as FIF


class SystemTray(QSystemTrayIcon):
    """系统托盘图标"""

    def __init__(self, on_settings, on_exit, parent=None):
        super().__init__(parent)
        self.on_settings = on_settings
        self.on_exit = on_exit
        self.on_show_window = None
        self.on_start_timer = None

        # 使用应用图标
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "icon.png")
        if os.path.exists(icon_path):
            self.setIcon(QIcon(icon_path))
        else:
            app_icon = QApplication.instance().windowIcon()
            if not app_icon.isNull():
                self.setIcon(app_icon)
        self.setToolTip("演讲计时助手")

        # 右键菜单（使用 QFluentWidgets 的 SystemTrayMenu）
        self._build_menu()

        # 左键点击打开主窗口
        self.activated.connect(self._on_activated)

    def _build_menu(self):
        menu = SystemTrayMenu(parent=None)

        show_action = QAction(FIF.HOME.icon(), "显示主窗口")
        show_action.triggered.connect(self._on_show_window)
        menu.addAction(show_action)

        start_action = QAction(FIF.PLAY.icon(), "开始计时")
        start_action.triggered.connect(self._on_start_timer)
        menu.addAction(start_action)

        menu.addSeparator()

        settings_action = QAction(FIF.SETTING.icon(), "设置")
        settings_action.triggered.connect(self._on_settings_clicked)
        menu.addAction(settings_action)

        menu.addSeparator()

        exit_action = QAction(FIF.CLOSE.icon(), "退出")
        exit_action.triggered.connect(self._on_exit_clicked)
        menu.addAction(exit_action)

        self.setContextMenu(menu)

    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self._on_show_window()

    def _on_show_window(self):
        if self.on_show_window:
            self.on_show_window()

    def _on_start_timer(self):
        if self.on_start_timer:
            self.on_start_timer()

    def _on_settings_clicked(self):
        self.on_settings()

    def _on_exit_clicked(self):
        self.on_exit()