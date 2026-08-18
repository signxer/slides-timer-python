#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
设置窗口 — 现代 Fluent 卡片布局。

分为两个 Tab 页：
  1. 提醒设置（触发条件、声音、提示语）
  2. 外观与位置（字体、颜色、偏移、分辨率）

PPT 文件管理已移至主窗口导航栏独立页面，避免重复。
使用 SimpleCardWidget + 手动 QVBoxLayout 代替 GroupHeaderCardWidget.addGroup，
避免版本间 API 不兼容（addGroup 签名在 1.11.x 中变化）。
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
    QFileDialog, QFrame, QApplication
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFontDatabase
from qfluentwidgets import (
    TabWidget, SimpleCardWidget,
    LineEdit, SpinBox, ComboBox, SwitchButton,
    PushButton, PrimaryPushButton, ColorPickerButton,
    BodyLabel, StrongBodyLabel, CaptionLabel,
    FluentIcon as FIF, InfoBar, InfoBarPosition,
)


class SettingsWindow(QWidget):
    def __init__(self, config_manager, embed=False, parent=None):
        super().__init__(parent)
        self.cfg = config_manager
        self.embed = embed
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
        self.tab_view = TabWidget(self)
        self.tab_reminder = QWidget()
        self._build_reminder_tab()
        self.tab_view.addTab(self.tab_reminder, "提醒设置")
        self.tab_appearance = QWidget()
        self._build_appearance_tab()
        self.tab_view.addTab(self.tab_appearance, "外观与位置")
        self.tab_view.setCurrentIndex(0)
        main_layout.addWidget(self.tab_view, 1)
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

    def _row_widget(self, label_text, widget):
        w = QWidget()
        row = QHBoxLayout(w)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(12)
        lbl = BodyLabel(label_text)
        lbl.setFixedWidth(110)
        row.addWidget(lbl)
        row.addWidget(widget)
        row.addStretch()
        return w

    def _build_reminder_tab(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(16)
        layout.setContentsMargins(8, 8, 8, 8)
        # Card 1
        card1 = SimpleCardWidget(); card1.setBorderRadius(10)
        c1l = QVBoxLayout(card1)
        c1l.setContentsMargins(24, 16, 24, 16); c1l.setSpacing(10)
        c1l.addWidget(StrongBodyLabel("第一阶段提醒"))
        self.entry_text_warning = LineEdit()
        self.entry_text_warning.setText(str(self.cfg.get("text_warning")))
        c1l.addWidget(self._row_widget("提示语", self.entry_text_warning))
        self.spin_duration_warning = SpinBox()
        self.spin_duration_warning.setRange(1, 60)
        self.spin_duration_warning.setValue(int(self.cfg.get("duration_warning")))
        c1l.addWidget(self._row_widget("持续时间(秒)", self.spin_duration_warning))
        trow = QHBoxLayout()
        trow.setSpacing(12)
        tlbl = BodyLabel("触发条件"); tlbl.setFixedWidth(110); trow.addWidget(tlbl)
        self.combo_trigger_type = ComboBox()
        self.combo_trigger_type.addItems(["百分比(%)", "剩余时间(分钟)"])
        self.combo_trigger_type.setCurrentIndex(0 if self.cfg.get("warning_trigger_type") == "percent" else 1)
        self.spin_trigger_value = SpinBox(); self.spin_trigger_value.setRange(1, 999)
        self.spin_trigger_value.setValue(int(self.cfg.get("warning_trigger_value")))
        trow.addWidget(self.combo_trigger_type); trow.addWidget(self.spin_trigger_value); trow.addStretch()
        c1l.addLayout(trow)
        self.switch_sound_warning = SwitchButton()
        self.switch_sound_warning.setChecked(self.cfg.get("sound_warning_enabled"))
        self.switch_sound_warning.setOnText("已开启"); self.switch_sound_warning.setOffText("已关闭")
        c1l.addWidget(self._row_widget("播放声音", self.switch_sound_warning))
        sww = QWidget()
        swl = QHBoxLayout(sww); swl.setContentsMargins(0, 0, 0, 0); swl.setSpacing(8)
        sw_lbl = BodyLabel("声音文件"); sw_lbl.setFixedWidth(110); swl.addWidget(sw_lbl)
        self.entry_sound_warning = LineEdit()
        self.entry_sound_warning.setText(str(self.cfg.get("sound_warning_path")))
        self.entry_sound_warning.setPlaceholderText("选择 WAV/MP3 文件...")
        swl.addWidget(self.entry_sound_warning, 1)
        btn_bw = PushButton("浏览"); btn_bw.setIcon(FIF.FOLDER)
        btn_bw.clicked.connect(lambda: self._browse_file(self.entry_sound_warning))
        swl.addWidget(btn_bw); c1l.addWidget(sww)
        layout.addWidget(card1)
        # Card 2
        card2 = SimpleCardWidget(); card2.setBorderRadius(10)
        c2l = QVBoxLayout(card2)
        c2l.setContentsMargins(24, 16, 24, 16); c2l.setSpacing(10)
        c2l.addWidget(StrongBodyLabel("时间耗尽提醒"))
        self.entry_text_critical = LineEdit()
        self.entry_text_critical.setText(str(self.cfg.get("text_critical")))
        c2l.addWidget(self._row_widget("提示语", self.entry_text_critical))
        self.spin_duration_critical = SpinBox(); self.spin_duration_critical.setRange(1, 60)
        self.spin_duration_critical.setValue(int(self.cfg.get("duration_critical")))
        c2l.addWidget(self._row_widget("持续时间(秒)", self.spin_duration_critical))
        self.switch_sound_critical = SwitchButton()
        self.switch_sound_critical.setChecked(self.cfg.get("sound_critical_enabled"))
        self.switch_sound_critical.setOnText("已开启"); self.switch_sound_critical.setOffText("已关闭")
        c2l.addWidget(self._row_widget("播放声音", self.switch_sound_critical))
        scw = QWidget()
        scl = QHBoxLayout(scw); scl.setContentsMargins(0, 0, 0, 0); scl.setSpacing(8)
        sc_lbl = BodyLabel("声音文件"); sc_lbl.setFixedWidth(110); scl.addWidget(sc_lbl)
        self.entry_sound_critical = LineEdit()
        self.entry_sound_critical.setText(str(self.cfg.get("sound_critical_path")))
        self.entry_sound_critical.setPlaceholderText("选择 WAV/MP3 文件...")
        scl.addWidget(self.entry_sound_critical, 1)
        btn_bc = PushButton("浏览"); btn_bc.setIcon(FIF.FOLDER)
        btn_bc.clicked.connect(lambda: self._browse_file(self.entry_sound_critical))
        scl.addWidget(btn_bc); c2l.addWidget(scw)
        layout.addWidget(card2)
        layout.addStretch(); scroll.setWidget(content)
        tab_layout = QVBoxLayout(self.tab_reminder)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.addWidget(scroll)

    def _build_appearance_tab(self):
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget(); layout = QVBoxLayout(content)
        layout.setSpacing(16); layout.setContentsMargins(8, 8, 8, 8)
        # 位置偏移
        card_offset = SimpleCardWidget(); card_offset.setBorderRadius(10)
        col = QVBoxLayout(card_offset); col.setContentsMargins(24, 16, 24, 16); col.setSpacing(10)
        col.addWidget(StrongBodyLabel("位置偏移"))
        self.spin_offset_x = SpinBox(); self.spin_offset_x.setRange(-9999, 9999)
        self.spin_offset_x.setValue(int(self.cfg.get("offset_x")))
        col.addWidget(self._row_widget("水平偏移 (X)", self.spin_offset_x))
        self.spin_offset_y = SpinBox(); self.spin_offset_y.setRange(-9999, 9999)
        self.spin_offset_y.setValue(int(self.cfg.get("offset_y")))
        col.addWidget(self._row_widget("垂直偏移 (Y)", self.spin_offset_y))
        layout.addWidget(card_offset)
        # 屏幕分辨率
        card_scr = SimpleCardWidget(); card_scr.setBorderRadius(10)
        scl = QVBoxLayout(card_scr); scl.setContentsMargins(24, 16, 24, 16); scl.setSpacing(10)
        scl.addWidget(StrongBodyLabel("屏幕分辨率"))
        self.spin_screen_width = SpinBox(); self.spin_screen_width.setRange(0, 99999)
        self.spin_screen_width.setValue(int(self.cfg.get("screen_width")))
        scl.addWidget(self._row_widget("屏幕宽度", self.spin_screen_width))
        self.spin_screen_height = SpinBox(); self.spin_screen_height.setRange(0, 99999)
        self.spin_screen_height.setValue(int(self.cfg.get("screen_height")))
        scl.addWidget(self._row_widget("屏幕高度", self.spin_screen_height))
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.geometry()
            hint = CaptionLabel(f"当前自动识别: {geo.width()} x {geo.height()}")
            hint.setContentsMargins(122, 4, 0, 0); scl.addWidget(hint)
        layout.addWidget(card_scr)
        # 外观
        card_app = SimpleCardWidget(); card_app.setBorderRadius(10)
        al = QVBoxLayout(card_app); al.setContentsMargins(24, 16, 24, 16); al.setSpacing(10)
        al.addWidget(StrongBodyLabel("外观"))
        self.spin_font_size = SpinBox(); self.spin_font_size.setRange(8, 200)
        self.spin_font_size.setValue(int(self.cfg.get("font_size")))
        al.addWidget(self._row_widget("字体大小", self.spin_font_size))
        self.combo_font_family = ComboBox()
        fonts = QFontDatabase.families(); current_font = self.cfg.get("font_family")
        self.combo_font_family.addItems(fonts)
        idx = self.combo_font_family.findText(current_font)
        if idx >= 0: self.combo_font_family.setCurrentIndex(idx)
        al.addWidget(self._row_widget("字体名称", self.combo_font_family))
        self.btn_text_color = ColorPickerButton(self.cfg.get("text_color"), "文字颜色")
        al.addWidget(self._row_widget("文字颜色", self.btn_text_color))
        self.btn_bg_color_warning = ColorPickerButton(self.cfg.get("bg_color_warning"), "警告背景色")
        al.addWidget(self._row_widget("警告背景色", self.btn_bg_color_warning))
        self.btn_bg_color_critical = ColorPickerButton(self.cfg.get("bg_color_critical"), "到期背景色")
        al.addWidget(self._row_widget("到期背景色", self.btn_bg_color_critical))
        layout.addWidget(card_app)
        # 横幅位置
        card_pos = SimpleCardWidget(); card_pos.setBorderRadius(10)
        pl = QVBoxLayout(card_pos); pl.setContentsMargins(24, 16, 24, 16); pl.setSpacing(10)
        pl.addWidget(StrongBodyLabel("横幅位置"))
        self.combo_position = ComboBox()
        self.combo_position.addItems(["顶部", "底部"])
        self.combo_position.setCurrentIndex(0 if self.cfg.get("position") == "top" else 1)
        pl.addWidget(self._row_widget("横幅位置", self.combo_position))
        layout.addWidget(card_pos)
        layout.addStretch(); scroll.setWidget(content)
        tab_layout = QVBoxLayout(self.tab_appearance)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.addWidget(scroll)

    def _browse_file(self, entry):
        path, _ = QFileDialog.getOpenFileName(self, "选择声音文件", "", "Sound Files (*.wav *.mp3);;All Files (*)")
        if path: entry.setText(path)

    def save(self):
        try:
            self.cfg.set("text_warning", self.entry_text_warning.text())
            self.cfg.set("duration_warning", self.spin_duration_warning.value())
            tt = "percent" if self.combo_trigger_type.currentIndex() == 0 else "time_remaining"
            self.cfg.set("warning_trigger_type", tt)
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
            pv = "top" if self.combo_position.currentIndex() == 0 else "bottom"
            self.cfg.set("position", pv)
            self.cfg.set("text_color", self.btn_text_color.color().name())
            self.cfg.set("bg_color_warning", self.btn_bg_color_warning.color().name())
            self.cfg.set("bg_color_critical", self.btn_bg_color_critical.color().name())
            if not self.embed: self.close()
            InfoBar.success("已保存", "设置已保存成功", parent=self, position=InfoBarPosition.TOP, duration=2000)
        except Exception as e:
            InfoBar.error("保存失败", f"保存设置时出错: {e}", parent=self, position=InfoBarPosition.TOP, duration=3000)
