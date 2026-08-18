#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
计时设置窗口 — 现代 Fluent 风格。

Silent-rain 风格参考：HeaderCardWidget + StrongBodyLabel 标题 + SpinBox + 快速选择按钮。
弹出式窗口，选择时长后回调 start_timer。
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from PySide6.QtCore import Qt
from qfluentwidgets import (
    PrimaryPushButton, PushButton, SpinBox, HeaderCardWidget,
    StrongBodyLabel, BodyLabel, CaptionLabel,
    FluentIcon as FIF,
)


class SetupWindow(QWidget):
    """计时设置窗口（弹出式）"""

    def __init__(self, on_start_callback, on_settings_callback, parent=None):
        super().__init__(parent)
        self.on_start = on_start_callback
        self.on_settings = on_settings_callback
        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle("设置演讲倒计时")
        self.setFixedSize(400, 320)
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Dialog)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setAlignment(Qt.AlignTop)

        # 卡片
        card = HeaderCardWidget(self)
        card.setTitle("演讲时长")
        card.setBorderRadius(10)
        card.viewLayout.setContentsMargins(24, 8, 24, 20)

        card_layout = QVBoxLayout()
        card_layout.setSpacing(16)
        card_layout.setContentsMargins(0, 0, 0, 0)

        # 时间输入区
        input_row = QHBoxLayout()
        input_row.setSpacing(10)

        btn_minus = PushButton("−")
        btn_minus.setFixedSize(44, 40)
        btn_minus.clicked.connect(lambda: self._adjust_time(-1))

        self.time_spinbox = SpinBox()
        self.time_spinbox.setRange(1, 999)
        self.time_spinbox.setValue(10)
        self.time_spinbox.setFixedSize(130, 40)

        btn_plus = PushButton("+")
        btn_plus.setFixedSize(44, 40)
        btn_plus.clicked.connect(lambda: self._adjust_time(1))

        input_row.addStretch()
        input_row.addWidget(btn_minus)
        input_row.addWidget(self.time_spinbox)
        input_row.addWidget(btn_plus)
        input_row.addStretch()
        card_layout.addLayout(input_row)

        card.viewLayout.addLayout(card_layout)

        layout.addWidget(card)

        # 快速选择区
        quick_label = StrongBodyLabel("快速选择")
        layout.addWidget(quick_label)

        quick_row = QHBoxLayout()
        quick_row.setSpacing(8)
        for m in [5, 10, 15, 20, 30]:
            btn = PushButton(f"{m} 分钟")
            btn.setFixedHeight(36)
            btn.clicked.connect(lambda checked, t=m: self.time_spinbox.setValue(t))
            quick_row.addWidget(btn)
        layout.addLayout(quick_row)

        layout.addStretch()

        # 开始按钮
        btn_start = PrimaryPushButton("  开始计时")
        btn_start.setIcon(FIF.PLAY)
        btn_start.setFixedHeight(48)
        btn_start.clicked.connect(self._on_start_click)
        layout.addWidget(btn_start)

        # 设置按钮（小）
        btn_settings = PushButton("  设置")
        btn_settings.setIcon(FIF.SETTING)
        btn_settings.clicked.connect(self.on_settings)
        layout.addWidget(btn_settings)

    def _adjust_time(self, delta):
        val = self.time_spinbox.value() + delta
        self.time_spinbox.setValue(max(1, val))

    def _on_start_click(self):
        minutes = self.time_spinbox.value()
        self.on_start(minutes)
        self.close()

    def closeEvent(self, event):
        event.accept()