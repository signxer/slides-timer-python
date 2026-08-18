#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
恢复对话框 — 使用 QFluentWidgets 的 Dialog。

演示中途退出时，询问用户"是否已完成"。
类似 silent-rain 中的 Dialog 用法。
"""
from PySide6.QtCore import Qt
from qfluentwidgets import Dialog, BodyLabel


class ResumeDialog(Dialog):
    """演示结束确认对话框"""

    def __init__(self, on_resume, on_stop):
        super().__init__(
            "演示已结束",
            "检测到演示提前结束。\n您的演讲完成了吗？",
        )
        self.on_resume = on_resume
        self.on_stop = on_stop

        # 确保在最前显示
        self.setWindowFlags(
            self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint
        )

        # 自定义按钮文字
        self.yesButton.setText("是的，已完成")
        self.cancelButton.setText("没有，稍后继续")

        # 连接信号
        self.yesSignal.connect(self._on_stop)
        self.cancelSignal.connect(self._on_resume)

    def _on_resume(self):
        self.on_resume()
        self.accept()

    def _on_stop(self):
        self.on_stop()
        self.accept()

    def closeEvent(self, event):
        self.on_stop()
        event.accept()