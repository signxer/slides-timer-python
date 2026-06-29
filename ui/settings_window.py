from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
    QFileDialog, QFrame, QApplication
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFontDatabase
from qfluentwidgets import (
    TabWidget, CardWidget, GroupHeaderCardWidget,
    LineEdit, SpinBox, DoubleSpinBox, ComboBox, SwitchButton,
    PushButton, PrimaryPushButton, ColorPickerButton,
    BodyLabel, StrongBodyLabel, CaptionLabel,
    FluentIcon as FIF
)
from ui.banner import BannerWindow
from ui.ppt_manager_window import PPTManagerWindow


class SettingsWindow(QWidget):
    """设置窗口"""

    def __init__(self, parent, config_manager):
        super().__init__(parent)
        self.cfg = config_manager
        self.preview_banner = None
        self._ppt_window = None

        self.setWindowTitle("设置")
        self.resize(720, 560)
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Dialog)
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(12, 12, 12, 12)

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

        # 底部按钮栏
        bottom_bar = QWidget()
        bottom_layout = QHBoxLayout(bottom_bar)
        bottom_layout.setContentsMargins(0, 4, 0, 0)

        btn_preview = PushButton("预览效果")
        btn_preview.setIcon(FIF.PLAY)
        btn_preview.clicked.connect(self.preview)

        btn_save = PrimaryPushButton("保存并关闭")
        btn_save.setIcon(FIF.SAVE)
        btn_save.clicked.connect(self.save)

        bottom_layout.addStretch()
        bottom_layout.addWidget(btn_preview)
        bottom_layout.addWidget(btn_save)

        main_layout.addWidget(bottom_bar)

    # ── Tab 1: 提醒设置 ──────────────────────────────────────

    def _build_reminder_tab(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(12)
        layout.setContentsMargins(8, 8, 8, 8)

        # ── 第一阶段提醒 ──
        card1 = GroupHeaderCardWidget()
        card1.setTitle("提醒设置 (第一阶段)")
        card1.setBorderRadius(8)

        self.entry_text_warning = self._add_labeled_input(card1, "剩余提示语", self.cfg.get("text_warning"))
        self.spin_duration_warning = self._add_labeled_spinbox(card1, "提示持续时间(秒)", self.cfg.get("duration_warning"), 1, 60)

        # 触发条件
        trigger_row = QHBoxLayout()
        trigger_row.addWidget(BodyLabel("触发条件"))
        self.combo_trigger_type = ComboBox()
        self.combo_trigger_type.addItems(["百分比(%)", "剩余时间(分钟)"])
        self.combo_trigger_type.setCurrentIndex(0 if self.cfg.get("warning_trigger_type") == "percent" else 1)
        self.spin_trigger_value = SpinBox()
        self.spin_trigger_value.setRange(1, 999)
        self.spin_trigger_value.setValue(int(self.cfg.get("warning_trigger_value")))
        trigger_row.addWidget(self.combo_trigger_type)
        trigger_row.addWidget(self.spin_trigger_value)
        card1.addGroup(trigger_row)

        # 声音
        self.switch_sound_warning, self.entry_sound_warning = self._add_sound_option(
            card1, "播放声音",
            self.cfg.get("sound_warning_enabled"),
            self.cfg.get("sound_warning_path")
        )

        layout.addWidget(card1)

        # ── 时间耗尽提醒 ──
        card2 = GroupHeaderCardWidget()
        card2.setTitle("提醒设置 (时间耗尽)")
        card2.setBorderRadius(8)

        self.entry_text_critical = self._add_labeled_input(card2, "提示语", self.cfg.get("text_critical"))
        self.spin_duration_critical = self._add_labeled_spinbox(card2, "提示持续时间(秒)", self.cfg.get("duration_critical"), 1, 60)

        self.switch_sound_critical, self.entry_sound_critical = self._add_sound_option(
            card2, "播放声音",
            self.cfg.get("sound_critical_enabled"),
            self.cfg.get("sound_critical_path")
        )

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
        layout.setSpacing(12)
        layout.setContentsMargins(8, 8, 8, 8)

        # 位置偏移
        card_offset = GroupHeaderCardWidget()
        card_offset.setTitle("位置偏移 (像素)")
        card_offset.setBorderRadius(8)

        self.spin_offset_x = self._add_labeled_spinbox(card_offset, "水平偏移 (X)", self.cfg.get("offset_x"), -9999, 9999)
        self.spin_offset_y = self._add_labeled_spinbox(card_offset, "垂直偏移 (Y)", self.cfg.get("offset_y"), -9999, 9999)
        layout.addWidget(card_offset)

        # 屏幕分辨率
        card_screen = GroupHeaderCardWidget()
        card_screen.setTitle("屏幕分辨率 (0为自动识别)")
        card_screen.setBorderRadius(8)

        self.spin_screen_width = self._add_labeled_spinbox(card_screen, "屏幕宽度", self.cfg.get("screen_width"), 0, 99999)
        self.spin_screen_height = self._add_labeled_spinbox(card_screen, "屏幕高度", self.cfg.get("screen_height"), 0, 99999)

        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.geometry()
            cap = CaptionLabel(f"当前自动识别: {geo.width()} x {geo.height()}")
            card_screen.addGroup(cap)

        layout.addWidget(card_screen)

        # 外观
        card_appearance = GroupHeaderCardWidget()
        card_appearance.setTitle("外观")
        card_appearance.setBorderRadius(8)

        self.spin_font_size = self._add_labeled_spinbox(card_appearance, "字体大小", self.cfg.get("font_size"), 8, 200)

        # 字体选择
        font_row = QHBoxLayout()
        font_row.addWidget(BodyLabel("字体名称"))
        self.combo_font_family = ComboBox()
        fonts = QFontDatabase.families()
        current_font = self.cfg.get("font_family")
        self.combo_font_family.addItems(fonts)
        idx = self.combo_font_family.findText(current_font)
        if idx >= 0:
            self.combo_font_family.setCurrentIndex(idx)
        font_row.addWidget(self.combo_font_family)
        card_appearance.addGroup(font_row)

        # 颜色选择
        self.btn_text_color = self._add_color_picker(card_appearance, "文字颜色", self.cfg.get("text_color"))
        self.btn_bg_color_warning = self._add_color_picker(card_appearance, "剩余1/3警告背景色", self.cfg.get("bg_color_warning"))
        self.btn_bg_color_critical = self._add_color_picker(card_appearance, "时间耗尽背景色", self.cfg.get("bg_color_critical"))

        layout.addWidget(card_appearance)

        # 位置
        card_position = GroupHeaderCardWidget()
        card_position.setTitle("位置")
        card_position.setBorderRadius(8)

        pos_row = QHBoxLayout()
        pos_row.addWidget(BodyLabel("横幅位置"))
        self.combo_position = ComboBox()
        self.combo_position.addItems(["顶部", "底部"])
        self.combo_position.setCurrentIndex(0 if self.cfg.get("position") == "top" else 1)
        pos_row.addWidget(self.combo_position)
        card_position.addGroup(pos_row)

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

        desc = BodyLabel("管理PPT文件的预设时间，播放时会自动加载对应时间。")
        layout.addWidget(desc)

        btn_open = PushButton("打开PPT文件管理")
        btn_open.setIcon(FIF.FOLDER)
        btn_open.setFixedWidth(200)
        btn_open.clicked.connect(self.open_ppt_manager)
        layout.addWidget(btn_open)

        layout.addStretch()

    # ── 辅助方法 ──────────────────────────────────────────────

    def _add_labeled_input(self, card, label, value):
        row = QHBoxLayout()
        row.addWidget(BodyLabel(label))
        entry = LineEdit()
        entry.setText(str(value))
        row.addWidget(entry)
        card.addGroup(row)
        return entry

    def _add_labeled_spinbox(self, card, label, value, min_val=0, max_val=9999):
        row = QHBoxLayout()
        row.addWidget(BodyLabel(label))
        spinbox = SpinBox()
        spinbox.setRange(min_val, max_val)
        spinbox.setValue(int(value))
        row.addWidget(spinbox)
        card.addGroup(row)
        return spinbox

    def _add_sound_option(self, card, label, enabled, path):
        switch_row = QHBoxLayout()
        switch_row.addWidget(BodyLabel(label))
        switch = SwitchButton()
        switch.setChecked(enabled)
        switch_row.addWidget(switch)
        card.addGroup(switch_row)

        path_row = QHBoxLayout()
        path_row.addWidget(BodyLabel("声音文件"))
        entry = LineEdit()
        entry.setText(str(path))
        btn_browse = PushButton("浏览")
        btn_browse.setIcon(FIF.FOLDER)
        btn_browse.clicked.connect(lambda: self._browse_file(entry))
        path_row.addWidget(entry)
        path_row.addWidget(btn_browse)
        card.addGroup(path_row)

        return switch, entry

    def _add_color_picker(self, card, label, color_str):
        row = QHBoxLayout()
        row.addWidget(BodyLabel(label))
        btn = ColorPickerButton(color_str, label)
        row.addWidget(btn)
        card.addGroup(row)
        return btn

    def _browse_file(self, entry):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择声音文件", "",
            "Sound Files (*.wav *.mp3);;All Files (*)"
        )
        if path:
            entry.setText(path)

    def open_ppt_manager(self):
        self._ppt_window = PPTManagerWindow(self)
        self._ppt_window.show()

    def preview(self):
        try:
            self.preview_banner = BannerWindow()
            self.preview_banner.show_message(
                message=self.entry_text_warning.text(),
                bg_color=self.btn_bg_color_warning.color().name(),
                text_color=self.btn_text_color.color().name(),
                font_size=self.spin_font_size.value(),
                font_family=self.combo_font_family.currentText(),
                position="top" if self.combo_position.currentIndex() == 0 else "bottom",
                duration=3,
                offset_x=self.spin_offset_x.value(),
                offset_y=self.spin_offset_y.value(),
                manual_width=self.spin_screen_width.value(),
                manual_height=self.spin_screen_height.value(),
            )
        except Exception as e:
            print(f"Preview error: {e}")

    def save(self):
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

            self.close()
        except Exception as e:
            print(f"Save error: {e}")
