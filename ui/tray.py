from PySide6.QtWidgets import QSystemTrayIcon, QMenu, QApplication
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QPen
from PySide6.QtCore import QSize


class SystemTray(QSystemTrayIcon):
    """系统托盘图标"""

    def __init__(self, on_settings, on_exit, parent=None):
        super().__init__(parent)
        self.on_settings = on_settings
        self.on_exit = on_exit

        self.setIcon(self._create_icon())
        self.setToolTip("演讲计时助手")

        # 右键菜单
        menu = QMenu()
        settings_action = menu.addAction("设置")
        settings_action.triggered.connect(self._on_settings_clicked)
        menu.addSeparator()
        exit_action = menu.addAction("退出")
        exit_action.triggered.connect(self._on_exit_clicked)
        self.setContextMenu(menu)

        # 左键点击打开设置
        self.activated.connect(self._on_activated)

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
        painter.drawLine(32, 32, 32, 14)  # 时针
        painter.drawLine(32, 32, 48, 32)  # 分针

        painter.end()
        return QIcon(pixmap)

    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.on_settings()

    def _on_settings_clicked(self):
        self.on_settings()

    def _on_exit_clicked(self):
        self.on_exit()
