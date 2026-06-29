from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtCore import Qt
from qfluentwidgets import PrimaryPushButton, PushButton


class ResumeDialog(QDialog):
    """演示结束确认对话框"""

    def __init__(self, parent, on_resume, on_stop):
        super().__init__(parent)
        self.on_resume = on_resume
        self.on_stop = on_stop
        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle("演示已结束")
        self.setFixedSize(380, 200)
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Dialog)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(30, 30, 30, 30)

        # 提示文本
        label = QLabel("检测到演示提前结束。\n您的演讲完成了吗？")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("font-size: 15px;")
        layout.addWidget(label)

        layout.addStretch()

        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        btn_stop = PrimaryPushButton("是的，已完成")
        btn_stop.setFixedHeight(40)
        btn_stop.setStyleSheet("""
            PrimaryPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 6px;
            }
            PrimaryPushButton:hover {
                background-color: #c0392b;
            }
        """)
        btn_stop.clicked.connect(self._on_stop)

        btn_resume = PushButton("没有，稍后继续")
        btn_resume.setFixedHeight(40)
        btn_resume.clicked.connect(self._on_resume)

        btn_layout.addWidget(btn_stop)
        btn_layout.addWidget(btn_resume)
        layout.addLayout(btn_layout)

    def _on_resume(self):
        self.on_resume()
        self.accept()

    def _on_stop(self):
        self.on_stop()
        self.accept()

    def closeEvent(self, event):
        self.on_stop()
        event.accept()
