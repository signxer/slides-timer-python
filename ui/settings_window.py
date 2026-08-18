#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
设置窗口 — 现代 Fluent 卡片布局。

分为三个 Tab 页：
  1. 提醒设置（触发条件、声音、提示语）
  2. 外观与位置（字体、颜色、偏移、分辨率）
  3. PPT 文件管理（内嵌 PPTManagerWindow）

Silent-rain 风格：HeaderCardWidget + 统一边距 + BodyLabel 行标签 + 紧凑布局。
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
    QFileDialog, QFrame, QApplication
)
from PySide6.QtCore import Qt
from qfluentwidgets import (
    TabWidget, SimpleCardWidget, GroupHeaderCardWidget,
    LineEdit, SpinBox, ComboBox, SwitchButton,
    PushButton, PrimaryPushButton, ColorPickerButton,
    BodyLabel, StrongBodyLabel, CaptionLabel,
    FluentIcon as FIF, InfoBar, InfoBarPosition,
)
from ui.ppt_manager_window import PPTManagerWindow


class SettingsWindow(QWidget):
    """设置窗口 — 可独立弹出或内嵌到 MSFluentWindow"""

    def __init__(self, config_manager, embed=False, parent=None):
        super().__init__(parent)
        self.cfg = config_manager
        self.embed = embed
        self._ppt_window = None
        self._init_window()
        self._init_ui()

    def _init_window(self):
        if not self.embed:
            self.setWindowTitle("设置")
            self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Dialog)
            self.resize(680, 540)
        else:
            self.setContentsMargins(0, 0, 0, 0)

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # TabView
        self.tab_view = TabWidget(self)

        # Tab 1: 提醒设置
        self.tab_reminder = QWidget()
        self._build_reminder_tab()
        self.tab_view.addTab(self.tab_reminder, "提醒设置")

        # Tab 2: 外观与位置
        self.tab_appearance = QWidget()
        self._build_appearance_tab()
        self.tab_view.addTab(self.tab_appearance, "外观与位置")

        # Tab 3: PPT 文件管理
        self.tab_ppt = QWidget()
        self._build_ppt_tab()
        self.tab_view.addTab(self.tab_ppt, "PPT文件管理")

        self.tab_view.setCurrentIndex(0)
        main_layout.addWidget(self.tab_view, 1)

        # 底部按钮（仅弹出模式）
        if not self.embed:
            bottom_bar = QWidget()
            bottom_layout = QHBoxLayout(bottom_bar)
            bottom_layout.setContentsMargins(0, 8, 0, 0)
            btn_save = PrimaryPushButton("保存并关闭")
            btn_save.setIcon(FIF.SAVE)
            btn_save.clicked.connect(self.save)
            bottom_layout.addStretch()
            bottom_layout.addWidget(btn_save)
            main_layout.addWidget(bottom_bar)

    # ── 辅助方法 ─────────────────────────────────────────────

    def _row(self, label_text, widget, stretch=True):
        row = QHBoxLayout()
        row.setSpacing(12)
        lbl = BodyLabel(label_text)
        lbl.setFixedWidth(110)
        row.addWidget(lbl)
        row.addWidget(widget)
        if stretch:
            row.addStretch()
        return row

    # ── Tab 1: 提醒设置 ──────────────────────────────────────

    def _build_reminder_tab(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(16)
        layout.setContentsMargins(8, 8, 8, 8)

        # 卡片 1: 第一阶段提醒
        card1 = GroupHeaderCardWidget()
        card1.setTitle("第一阶段提醒")
        card1.setBorderRadius(10)

        self.entry_text_warning = LineEdit()
        self.entry_text_warning.setText(str(self.cfg.get("text_warning")))
        card1.addGroup(self._row("提示语", self.entry_text_warning))

        self.spin_duration_warning = SpinBox()
        self.spin_duration_warning.setRange(1, 60)
        self.spin_duration_warning.setValue(int(self.cfg.get("duration_warning")))
        card1.addGroup(self._row("持续时间(秒)", self.spin_duration_warning))

        # 触发条件行
        trigger_row = QHBoxLayout()
        trigger_row.setSpacing(12)
        self.combo_trigger_type = ComboBox()
        self.combo_trigger_type.addItems(["百分比(%)", "剩余时间(分钟)"])
        self.combo_trigger_type.setCurrentIndex(0 if self.cfg.get("warning_trigger_type") == "percent" else 1)
        self.spin_trigger_value = SpinBox()
        self.spin_trigger_value.setRange(1, 999)
        self.spin_trigger_value.setValue(int(self.cfg.get("warning_trigger_value")))
        trigger_row.addWidget(BodyLabel("触发条件"))
        trigger_row.addWidget(self.combo_trigger_type)
        trigger_row.addWidget(self.spin_trigger_value)
        trigger_row.addStretch()
        card1.addGroup(trigger_row)

        # 声音开关
        self.switch_sound_warning = SwitchButton()
        self.switch_sound_warning.setChecked(self.cfg.get("sound_warning_enabled"))
        self.switch_sound_warning.setOnText("已开启")
        self.switch_sound_warning.setOffText("已关闭")
        card1.addGroup(self._row("播放声音", self.switch_sound_warning))

        # 声音文件浏览
        self.entry_sound_warning = LineEdit()
        self.entry_sound_warning.setText(str(self.cfg.get("sound_warning_path")))
        self.entry_sound_warning.setPlaceholderText("选择 WAV/MP3 文件...")
        sound_warn_row = QHBoxLayout()
        sound_warn_row.setSpacing(8)
        sound_warn_row.addWidget(BodyLabel("声音文件"))
        sound_warn_row.addWidget(self.entry_sound_warning, 1)
        btn_browse_warn = PushButton("浏览")
        btn_browse_warn.setIcon(FIF.FOLDER)
        btn_browse_warn.clicked.connect(lambda: self._browse_file(self.entry_sound_warning))
        sound_warn_row.addWidget(btn_browse_warn)
        card1.addGroup(sound_warn_row)

        layout.addWidget(card1)

        # 卡片 2: 时间耗尽提醒
        card2 = GroupHeaderCardWidget()
        card2.setTitle("时间耗尽提醒")
        card2.setBorderRadius(10)

        self.entry_text_critical = LineEdit()
        self.entry_text_critical.setText(str(self.cfg.get("text_critical")))
        card2.addGroup(self._row("提示语", self.entry_text_critical))

        self.spin_duration_critical = SpinBox()
        self.spin_duration_critical.setRange(1, 60)
        self.spin_duration_critical.setValue(int(self.cfg.get("duration_critical")))
        card2.addGroup(self._row("持续时间(秒)", self.spin_duration_critical))

        self.switch_sound_critical = SwitchButton()
        self.switch_sound_critical.setChecked(self.cfg.get("sound_critical_enabled"))
        self.switch_sound_critical.setOnText("已开启")
        self.switch_sound_critical.setOffText("已关闭")
        card2.addGroup(self._row("播放声音", self.switch_sound_critical))

        self.entry_sound_critical = LineEdit()
        self.entry_sound_critical.setText(str(self.cfg.get("sound_critical_path")))
        self.entry_sound_critical.setPlaceholderText("选择 WAV/MP3 文件...")
        sound_crit_row = QHBoxLayout()
        sound_crit_row.setSpacing(8)
        sound_crit_row.addWidget(BodyLabel("声音文件"))
        sound_crit_row.addWidget(self.entry_sound_critical, 1)
        btn_browse_crit = PushButton("浏览")
        btn_browse_crit.setIcon(FIF.FOLDER)
        btn_browse_crit.clicked.connect(lambda: self._browse_file(self.entry_sound_critical))
        sound_crit_row.addWidget(btn_browse_crit)
        card2.addGroup(sound_crit_row)

        layout.addWidget(card2)
        layout.addStretch()
        scroll.setWidget(content)

        tab_layout = QVBoxLayout(self.tab_reminder)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.addWidget(scroll)

    # ── Tab 2: 外观与位置 ────────────────────────────────────

    def _build_appearance_tab(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(16)
        layout.setContentsMargins(8, 8, 8, 8)

        # 位置偏移
        card_offset = GroupHeaderCardWidget()
        card_offset.setTitle("位置偏移")
        card_offset.setBorderRadius(10)

        self.spin_offset_x = SpinBox()
        self.spin_offset_x.setRange(-9999, 9999)
        self.spin_offset_x.setValue(int(self.cfg.get("offset_x")))
        card_offset.addGroup(self._row("水平偏移 (X)", self.spin_offset_x))

        self.spin_offset_y = SpinBox()
        self.spin_offset_y.setRange(-9999, 9999)
        self.spin_offset_y.setValue(int(self.cfg.get("offset_y")))
        card_offset.addGroup(self._row("垂直偏移 (Y)", self.spin_offset_y))

        layout.addWidget(card_offset)

        # 屏幕分辨率
        card_screen = GroupHeaderCardWidget()
        card_screen.setTitle("屏幕分辨率")
        card_screen.setBorderRadius(10)

        self.spin_screen_width = SpinBox()
        self.spin_screen_width.setRange(0, 99999)
        self.spin_screen_width.setValue(int(self.cfg.get("screen_width")))
        card_screen.addGroup(self._row("屏幕宽度", self.spin_screen_width))

        self.spin_screen_height = SpinBox()
        self.spin_screen_height.setRange(0, 99999)
        self.spin_screen_height.setValue(int(self.cfg.get("screen_height")))
        card_screen.addGroup(self._row("屏幕高度", self.spin_screen_height))

        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.geometry()
            hint = CaptionLabel(f"当前自动识别: {geo.width()} x {geo.height()}")
            hint.setContentsMargins(122, 4, 0, 0)
            card_screen.addGroup(hint)

        layout.addWidget(card_screen)

        # 外观
        card_appearance = GroupHeaderCardWidget()
        card_appearance.setTitle("外观")
        card_appearance.setBorderRadius(10)

        self.spin_font_size = SpinBox()
        self.spin_font_size.setRange(8, 200)
        self.spin_font_size.setValue(int(self.cfg.get("font_size")))
        card_appearance.addGroup(self._row("字体大小", self.spin_font_size))

        self.combo_font_family = ComboBox()
        from PySide6.QtGui import QFontDatabase
        fonts = QFontDatabase.families()
        current_font = self.cfg.get("font_family")
        self.combo_font_family.addItems(fonts)
        idx = self.combo_font_family.findText(current_font)
        if idx >= 0:
            self.combo_font_family.setCurrentIndex(idx)
        card_appearance.addGroup(self._row("字体名称", self.combo_font_family))

        self.btn_text_color = ColorPickerButton(self.cfg.get("text_color"), "文字颜色")
        card_appearance.addGroup(self._row("文字颜色", self.btn_text_color))

        self.btn_bg_color_warning = ColorPickerButton(self.cfg.get("bg_color_warning"), "警告背景色")
        card_appearance.addGroup(self._row("警告背景色", self.btn_bg_color_warning))

        self.btn_bg_color_critical = ColorPickerButton(self.cfg.get("bg_color_critical"), "到期背景色")
        card_appearance.addGroup(self._row("到期背景色", self.btn_bg_color_critical))

        layout.addWidget(card_appearance)

        # 横幅位置
        card_position = GroupHeaderCardWidget()
        card_position.setTitle("横幅位置")
        card_position.setBorderRadius(10)

        self.combo_position = ComboBox()
        self.combo_position.addItems(["顶部", "底部"])
        self.combo_position.setCurrentIndex(0 if self.cfg.get("position") == "top" else 1)
        card_position.addGroup(self._row("横幅位置", self.combo_position))

        layout.addWidget(card_position)
        layout.addStretch()
        scroll.setWidget(content)

        tab_layout = QVBoxLayout(self.tab_appearance)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.addWidget(scroll)

    # ── Tab 3: PPT 文件管理 ──────────────────────────────────

    def _build_ppt_tab(self):
        layout = QVBoxLayout(self.tab_ppt)
        layout.setSpacing(12)
        layout.setContentsMargins(8, 8, 8, 8)

        desc = BodyLabel("管理 PPT 文件的预设时间，检测到放映时自动开始计时。")
        desc.setStyleSheet("color: #888;")
        layout.addWidget(desc)

        self._inner_ppt = PPTManagerWindow(embed=True)
        layout.addWidget(self._inner_ppt, 1)

    # ── 工具方法 ─────────────────────────────────────────────

    def _browse_file(self, entry):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择声音文件", "",
            "Sound Files (*.wav *.mp3);;All Files (*)"
        )
        if path:
            entry.setText(path)

    def save(self):
        """保存所有设置并关闭窗口"""
        try:
            self.cfg.set("text_warning", self.entry_text_warning.text())
            self.cfg.set("duration_warning", self.spin_duration_warning.value())
            trigger_type = "percent" if self.combo_trigger_type.currentIndex() == 0 else "time_remaining"
            self.cfg.set("warning_trigger_type", trigger_type)
            self.cfg.set("warning_trigger_value", self.spin_trigger_value.value())
            self.cfg.set("sound_warning_enabled", self.switch_sound_warning.isChecked())
            self.cfg.set("sound_warning_path", self.entry_sound_warning.text())
            self.cfg.set("text_critical", self.entry_text_critical.text())
            self.cfg.set("duration_critical", self.spin_duration_critical.value())
            self.cfg.set("sound_critical_enabled", self.switch_sound_critical.isChecked())
            self.cfg.set("sound_critical_path", self.entry_sound_critical.text())
            self.cfg.set("offset_x", self.spin_offset_x.value())
            self.cfg.set("offset_y", self.spin_offset_y.value())
            self.cfg.set("screen_width", self.spin_screen_width.value())
            self.cfg.set("screen_height", self.spin_screen_height.value())
            self.cfg.set("font_size", self.spin_font_size.value())
            self.cfg.set("font_family", self.combo_font_family.currentText())
            pos_value = "top" if self.combo_position.currentIndex() == 0 else "bottom"
            self.cfg.set("position", pos_value)
            self.cfg.set("text_color", self.btn_text_color.color().name())
            self.cfg.set("bg_color_warning", self.btn_bg_color_warning.color().name())
            self.cfg.set("bg_color_critical", self.btn_bg_color_critical.color().name())
            if not self.embed:
                self.close()
            InfoBar.success("已保存", "设置已保存成功", parent=self, position=InfoBarPosition.TOP, duration=2000)
        except Exception as e:
            InfoBar.error("保存失败", f"保存设置时出错: {e}", parent=self, position=InfoBarPosition.TOP, duration=3000)