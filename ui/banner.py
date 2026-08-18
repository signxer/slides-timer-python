from PySide6.QtWidgets import QWidget, QLabel, QGraphicsOpacityEffect, QApplication
from PySide6.QtCore import Qt, QPropertyAnimation, QTimer, QEasingCurve
from PySide6.QtGui import QFont


class BannerWindow(QWidget):
    """浮动横幅提示窗口"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        self._is_animating = False
        self._flash_visible = True
        self._target_text_color = ""
        self._target_bg_color = ""

        # 标签
        self.label = QLabel("", self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 透明度效果
        self._opacity_effect = QGraphicsOpacityEffect(self.label)
        self.label.setGraphicsEffect(self._opacity_effect)
        self._opacity_effect.setOpacity(0.0)

        # 动画
        self._fade_anim = QPropertyAnimation(self._opacity_effect, b"opacity")
        self._fade_anim.setDuration(300)

        # 闪烁定时器
        self._flash_timer = QTimer(self)
        self._flash_timer.timeout.connect(self._toggle_flash)

        # 停止定时器
        self._stop_timer = QTimer(self)
        self._stop_timer.setSingleShot(True)
        self._stop_timer.timeout.connect(self._start_fade_out)

    def show_message(self, message, bg_color, text_color, font_size,
                     font_family="Noto Sans CJK SC", position="top",
                     duration=5, offset_x=0, offset_y=0,
                     manual_width=0, manual_height=0):
        """显示横幅消息"""
        # 停止之前的动画
        self._flash_timer.stop()
        self._stop_timer.stop()
        self._fade_anim.stop()
        self._is_animating = True
        self._flash_visible = True
        self._target_text_color = text_color
        self._target_bg_color = bg_color

        # 设置字体和文字
        font = QFont(font_family, font_size, QFont.Weight.Bold)
        self.label.setFont(font)
        self.label.setText(message)

        # 设置样式
        self.label.setStyleSheet(f"""
            QLabel {{
                color: {text_color};
                background-color: {bg_color};
                padding: 15px 30px;
                border-radius: 10px;
            }}
        """)

        # 计算尺寸
        self.label.adjustSize()
        label_size = self.label.sizeHint()
        w = label_size.width() + 60
        h = label_size.height() + 30

        # 获取屏幕尺寸
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.geometry()
            sw = manual_width if manual_width > 0 else geo.width()
            sh = manual_height if manual_height > 0 else geo.height()
            screen_x = geo.x()
            screen_y = geo.y()
        else:
            sw, sh = 1920, 1080
            screen_x, screen_y = 0, 0

        # 计算位置
        x = screen_x + (sw - w) // 2 + offset_x
        if position == "top":
            y = screen_y + 50 + offset_y
        else:
            y = screen_y + sh - h - 100 + offset_y

        self.setGeometry(x, y, w, h)
        self.label.setGeometry(0, 0, w, h)
        self.show()

        # 淡入动画
        self._fade_anim.setStartValue(0.0)
        self._fade_anim.setEndValue(1.0)
        self._fade_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._fade_anim.start()

        # 启动闪烁（淡入完成后）
        QTimer.singleShot(350, self._start_flash)

        # 自动关闭
        self._stop_timer.start(duration * 1000)

    def _start_flash(self):
        if self._is_animating:
            self._flash_visible = True
            self._flash_timer.start(500)

    def _toggle_flash(self):
        if not self._is_animating:
            return
        self._flash_visible = not self._flash_visible
        color = self._target_text_color if self._flash_visible else self._target_bg_color
        self.label.setStyleSheet(f"""
            QLabel {{
                color: {color};
                background-color: {self._target_bg_color};
                padding: 15px 30px;
                border-radius: 10px;
            }}
        """)

    def _start_fade_out(self):
        self._flash_timer.stop()
        self._fade_anim.setStartValue(1.0)
        self._fade_anim.setEndValue(0.0)
        self._fade_anim.setEasingCurve(QEasingCurve.Type.InCubic)
        self._fade_anim.finished.connect(self._on_fade_out_done)
        self._fade_anim.start()

    def _on_fade_out_done(self):
        self._is_animating = False
        self.hide()
        try:
            self._fade_anim.finished.disconnect(self._on_fade_out_done)
        except RuntimeError:
            pass
