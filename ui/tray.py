#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统托盘图标 — 增加"显示主窗口"和"开始计时"菜单项。

Silent-rain 风格参考：ToolButton 图标 + 清晰菜单结构。
"""
from PySide6.QtWidgets import QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QPen
from PySide6.QtCore import QSize


class SystemTray(QSystemTrayIcon):
    """系统托盘图标"""

    def __init__(self, on_settings, on_exit, parent=None):
        super().__init__(parent)
        self.on_settings = on_settings
        self.on_exit = on_exit
        self.on_show_window = None
        self.on_start_timer = None

        self.setIcon(self._create_icon())
        self.setToolTip("演讲计时助手")

        # 右键菜单
        self._build_menu()

        # 左键点击打开主窗口
        self.activated.connect(self._on_activated)

    def _build_menu(self):
        menu = QMenu()

        show_action = menu.addAction("显示主窗口")
        show_action.triggered.connect(self._on_show_window)

        start_action = menu.addAction("开始计时")
        start_action.triggered.connect(self._on_start_timer)

        menu.addSeparator()

        settings_action = menu.addAction("设置")
        settings_action.triggered.connect(self._on_settings_clicked)

        menu.addSeparator()

        exit_action = menu.addAction("退出")
        exit_action.triggered.connect(self._on_exit_clicked)

        self.setContextMenu(menu)

    def _create_icon(self) -> QIcon:
        """生成时钟图标"""
        pixmap = QPixmap(QSize(64, 64))
        pixmap.fill(QColor(0, 0, 0, 0))

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 蓝色圆形背景
        painter.setBrush(QColor("#1f538d"))
        painter.setPen(QPen(QColor("#1f538d")))
        painter.drawEllipse(4, 4, 56, 56)

        # 白色指针
        painter.setPen(QPen(QColor("white"), 3))
        painter.drawLine(32, 32, 32, 14)
        painter.drawLine(32, 32, 48, 32)

        painter.end()
        return QIcon(pixmap)

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