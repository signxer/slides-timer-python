from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from qfluentwidgets import (
    FluentWindow, PrimaryPushButton, PushButton, SpinBox,
    CardWidget, BodyLabel, StrongBodyLabel, TitleLabel,
    FluentIcon as FIF
)


class SetupWindow(QWidget):
    """计时设置窗口（弹出式）"""

    def __init__(self, parent, on_start_callback, on_settings_callback):
        super().__init__(parent)
        self.on_start = on_start_callback
        self.on_settings = on_settings_callback
        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle("设置演讲倒计时")
        self.setFixedSize(400, 340)
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Dialog)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        # 标题
        title = StrongBodyLabel("演讲时长 (分钟)")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # 时间输入区
        input_layout = QHBoxLayout()
        input_layout.setSpacing(10)

        btn_minus = PushButton("−")
        btn_minus.setFixedSize(50, 40)
        btn_minus.clicked.connect(lambda: self._adjust_time(-1))

        self.time_spinbox = SpinBox()
        self.time_spinbox.setRange(1, 999)
        self.time_spinbox.setValue(10)
        self.time_spinbox.setFixedSize(140, 40)

        btn_plus = PushButton("+")
        btn_plus.setFixedSize(50, 40)
        btn_plus.clicked.connect(lambda: self._adjust_time(1))

        input_layout.addStretch()
        input_layout.addWidget(btn_minus)
        input_layout.addWidget(self.time_spinbox)
        input_layout.addWidget(btn_plus)
        input_layout.addStretch()
        layout.addLayout(input_layout)

        # 快速选择
        quick_layout = QHBoxLayout()
        quick_layout.setSpacing(8)
        for m in [5, 10, 15, 20]:
            btn = PushButton(f"{m}分钟")
            btn.setFixedHeight(32)
            btn.clicked.connect(lambda checked, t=m: self.time_spinbox.setValue(t))
            quick_layout.addWidget(btn)
        layout.addLayout(quick_layout)

        layout.addStretch()

        # 开始按钮
        btn_start = PrimaryPushButton("开始计时")
        btn_start.setFixedHeight(50)
        btn_start.setIcon(FIF.PLAY)
        btn_start.clicked.connect(self._on_start_click)
        layout.addWidget(btn_start)

    def _adjust_time(self, delta):
        val = self.time_spinbox.value() + delta
        self.time_spinbox.setValue(max(1, val))

    def _on_start_click(self):
        minutes = self.time_spinbox.value()
        self.on_start(minutes)
        self.close()

    def closeEvent(self, event):
        event.accept()
