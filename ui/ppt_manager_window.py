#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PPT 文件时间管理窗口 — 现代 Fluent 风格。

Silent-rain 风格参考：HeaderCardWidget + 卡片列表 + CaptionLabel + BodyLabel。
可独立弹出或内嵌到 MSFluentWindow。
"""
import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QFrame,
    QFileDialog, QDialog
)
from PySide6.QtCore import Qt
from qfluentwidgets import (
    SimpleCardWidget, CardWidget, HeaderCardWidget,
    LineEdit, DoubleSpinBox, PushButton, PrimaryPushButton,
    BodyLabel, StrongBodyLabel, CaptionLabel,
    FluentIcon as FIF, MessageBox
)
from config import cfg


class PPTManagerWindow(QWidget):
    """PPT 文件时间管理窗口"""

    def __init__(self, parent=None, embed=False):
        super().__init__(parent)
        self.embed = embed
        if not embed:
            self.setWindowTitle("PPT文件时间管理")
            self.resize(660, 500)
            self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Dialog)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(0 if self.embed else 16, 0 if self.embed else 16, 0 if self.embed else 16, 0 if self.embed else 16)

        if not self.embed:
            # 标题栏
            header = QHBoxLayout()
            header.addWidget(StrongBodyLabel("PPT文件时间管理"))
            header.addStretch()
            btn_clear = PushButton("一键清空")
            btn_clear.setIcon(FIF.DELETE)
            btn_clear.setStyleSheet("color: #e74c3c;")
            btn_clear.clicked.connect(self._clear_all)
            header.addWidget(btn_clear)
            layout.addLayout(header)

        # PPT 列表（滚动区域）
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        self.list_container = QWidget()
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setSpacing(6)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.addStretch()

        scroll.setWidget(self.list_container)
        layout.addWidget(scroll, 1)

        # 添加区域：卡片（用 SimpleCardWidget 避免 GroupHeaderCardWidget.addGroup 版本兼容问题）
        add_card = SimpleCardWidget()
        add_card.setBorderRadius(10)
        acl = QVBoxLayout(add_card)
        acl.setContentsMargins(24, 16, 24, 16)
        acl.setSpacing(12)
        acl.addWidget(StrongBodyLabel("添加PPT文件"))

        # 文件路径行
        file_widget = QWidget()
        file_row = QHBoxLayout(file_widget)
        file_row.setContentsMargins(0, 0, 0, 0)
        file_row.setSpacing(8)
        file_row.addWidget(BodyLabel("文件路径"))
        self.entry_file_path = LineEdit()
        self.entry_file_path.setPlaceholderText("选择或输入PPT文件路径...")
        btn_browse = PushButton("浏览")
        btn_browse.setIcon(FIF.FOLDER)
        btn_browse.clicked.connect(self._browse_file)
        file_row.addWidget(self.entry_file_path, 1)
        file_row.addWidget(btn_browse)
        acl.addWidget(file_widget)

        # 时间行
        time_widget = QWidget()
        time_row = QHBoxLayout(time_widget)
        time_row.setContentsMargins(0, 0, 0, 0)
        time_row.setSpacing(8)
        time_row.addWidget(BodyLabel("时间(分钟)"))
        self.spin_time = DoubleSpinBox()
        self.spin_time.setRange(0.5, 999)
        self.spin_time.setValue(10)
        self.spin_time.setSuffix(" 分钟")
        time_row.addWidget(self.spin_time)
        btn_add = PrimaryPushButton("添加")
        btn_add.setIcon(FIF.ADD)
        btn_add.clicked.connect(self._add_ppt)
        time_row.addWidget(btn_add)
        time_row.addStretch()
        acl.addWidget(time_widget)

        layout.addWidget(add_card)

        # 加载列表
        self._load_ppt_files()

    def _browse_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择PPT文件", "",
            "PowerPoint (*.pptx *.ppt);;WPS (*.dps);;All Files (*)"
        )
        if path:
            self.entry_file_path.setText(path)

    def _add_ppt(self):
        file_path = self.entry_file_path.text().strip()
        time_val = self.spin_time.value()
        if file_path and time_val > 0:
            ppt_timers = cfg.get("ppt_timers")
            ppt_timers[file_path] = time_val
            cfg.set("ppt_timers", ppt_timers)
            self._load_ppt_files()
            self.entry_file_path.clear()
            self.spin_time.setValue(10)

    def _load_ppt_files(self):
        # 清空列表（保留 stretch）
        while self.list_layout.count() > 1:
            item = self.list_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        ppt_timers = cfg.get("ppt_timers")
        if not ppt_timers:
            empty_label = CaptionLabel("暂无PPT文件，请添加。")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_label.setStyleSheet("color: #888; padding: 20px;")
            self.list_layout.insertWidget(0, empty_label)
            return

        for file_path, time_min in ppt_timers.items():
            file_name = os.path.basename(file_path)
            card = SimpleCardWidget()
            card.setBorderRadius(8)
            row = QHBoxLayout(card)
            row.setContentsMargins(16, 10, 16, 10)
            row.setSpacing(12)

            # 文件名
            name_label = BodyLabel(file_name)
            name_label.setMinimumWidth(200)
            row.addWidget(name_label, 1)

            # 时间
            time_label = CaptionLabel(f"{time_min} 分钟")
            time_label.setFixedWidth(80)
            row.addWidget(time_label)

            # 修改按钮
            btn_edit = PushButton("修改")
            btn_edit.setFixedWidth(60)
            btn_edit.clicked.connect(lambda checked, p=file_path, t=time_min: self._edit_ppt(p, t))
            row.addWidget(btn_edit)

            # 删除按钮
            btn_del = PushButton("删除")
            btn_del.setFixedWidth(60)
            btn_del.setStyleSheet("color: #e74c3c;")
            btn_del.clicked.connect(lambda checked, p=file_path: self._delete_ppt(p))
            row.addWidget(btn_del)

            self.list_layout.insertWidget(self.list_layout.count() - 1, card)

    def _edit_ppt(self, file_path, current_time):
        dialog = QDialog(self)
        dialog.setWindowTitle("修改PPT时间")
        dialog.setFixedSize(300, 150)
        dialog.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)

        dlayout = QVBoxLayout(dialog)
        dlayout.setContentsMargins(20, 20, 20, 20)
        dlayout.setSpacing(12)

        dlayout.addWidget(BodyLabel("新时间(分钟):"))
        spin = DoubleSpinBox()
        spin.setRange(0.5, 999)
        spin.setValue(current_time)
        dlayout.addWidget(spin)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        btn_save = PrimaryPushButton("保存")
        btn_cancel = PushButton("取消")
        btn_row.addWidget(btn_save)
        btn_row.addWidget(btn_cancel)
        dlayout.addLayout(btn_row)

        def do_save():
            new_time = spin.value()
            if new_time > 0:
                ppt_timers = cfg.get("ppt_timers")
                ppt_timers[file_path] = new_time
                cfg.set("ppt_timers", ppt_timers)
                self._load_ppt_files()
                dialog.accept()

        btn_save.clicked.connect(do_save)
        btn_cancel.clicked.connect(dialog.reject)
        dialog.exec()

    def _delete_ppt(self, file_path):
        ppt_timers = cfg.get("ppt_timers")
        if file_path in ppt_timers:
            del ppt_timers[file_path]
            cfg.set("ppt_timers", ppt_timers)
            self._load_ppt_files()

    def _clear_all(self):
        w = MessageBox("确认清空", "确定要清空所有PPT文件吗？", self)
        if w.exec():
            cfg.set("ppt_timers", {})
            self._load_ppt_files()