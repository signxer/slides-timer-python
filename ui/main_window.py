#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Slides Timer 主窗口 — 现代 Fluent 仪表盘。

采用 MSFluentWindow 作为外壳，左侧导航栏切换页面：
  - 计时器：实时倒计时 + 进度环 + 控制按钮
  - 设置：分组卡片配置
  - PPT管理：预设时间管理

布局参照 silent-rain 的 DashboardScreen：
  HeaderCardWidget / SimpleCardWidget / ProgressRing / InfoBar / 统一边距。
"""
import os

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from PySide6.QtCore import Qt

from qfluentwidgets import (
    MSFluentWindow,
    FluentIcon as FIF,
    SimpleCardWidget, HeaderCardWidget,
    PrimaryPushButton, PushButton,
    TitleLabel, SubtitleLabel, BodyLabel, CaptionLabel,
    ProgressRing, InfoBar, InfoBarPosition,
    IconWidget,
)

from config import cfg
from ui.settings_window import SettingsWindow
from ui.ppt_manager_window import PPTManagerWindow


# ─── 计时器主页面 ───────────────────────────────────────────


class TimerPage(QWidget):
    """计时器仪表盘：状态卡片 + 大倒计时 + 进度环 + 控制按钮"""

    def __init__(self, app_ref, parent=None):
        super().__init__(parent)
        self.app = app_ref
        self.setObjectName("timerPage")
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(20)

        # ── 标题栏 ──
        header = QHBoxLayout()
        header.setSpacing(12)
        icon = IconWidget(FIF.STOP_WATCH, self)
        icon.setFixedSize(28, 28)
        header.addWidget(icon)
        title = TitleLabel("演讲计时")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        # ── 主区域：倒计时 + 进度环 + 控制 ──
        main_row = QHBoxLayout()
        main_row.setSpacing(24)

        # 左侧：状态和信息卡片
        left_col = QVBoxLayout()
        left_col.setSpacing(16)

        # 状态卡片
        status_card = HeaderCardWidget(self)
        status_card.setTitle("计时状态")
        status_card.setBorderRadius(10)
        status_card.viewLayout.setContentsMargins(24, 6, 24, 16)

        sl = QVBoxLayout()
        sl.setSpacing(8)
        sl.setContentsMargins(0, 0, 0, 0)

        # 大号倒计时数字
        self.lbl_time = SubtitleLabel("00:00")
        self.lbl_time.setStyleSheet("font-size: 56px; font-weight: bold; color: #0078d4;")
        self.lbl_time.setAlignment(Qt.AlignCenter)
        sl.addWidget(self.lbl_time)

        # 状态标签
        self.lbl_status = BodyLabel("等待演示开始...")
        self.lbl_status.setAlignment(Qt.AlignCenter)
        self.lbl_status.setStyleSheet("color: #888;")
        sl.addWidget(self.lbl_status)

        # PPT 信息
        self.lbl_ppt = CaptionLabel("")
        self.lbl_ppt.setAlignment(Qt.AlignCenter)
        self.lbl_ppt.setStyleSheet("color: #aaa;")
        sl.addWidget(self.lbl_ppt)

        status_card.viewLayout.addLayout(sl)
        left_col.addWidget(status_card, 1)

        # ── 右侧：进度环 ──
        right_col = QVBoxLayout()
        right_col.setSpacing(16)
        right_col.setAlignment(Qt.AlignCenter)

        goal_card = SimpleCardWidget(self)
        goal_card.setBorderRadius(10)
        gl = QVBoxLayout(goal_card)
        gl.setContentsMargins(24, 20, 24, 20)
        gl.setSpacing(12)
        gl.setAlignment(Qt.AlignCenter)

        gl.addWidget(CaptionLabel("完成进度"), 0, Qt.AlignCenter)

        self.progress_ring = ProgressRing(self)
        self.progress_ring.setFixedSize(140, 140)
        self.progress_ring.setValue(0)
        self.progress_ring.setTextVisible(True)
        self.progress_ring.setStrokeWidth(8)
        gl.addWidget(self.progress_ring, 0, Qt.AlignCenter)

        self.lbl_progress = CaptionLabel("0%")
        self.lbl_progress.setAlignment(Qt.AlignCenter)
        gl.addWidget(self.lbl_progress)

        right_col.addWidget(goal_card)

        main_row.addLayout(left_col, 1)
        main_row.addLayout(right_col)
        layout.addLayout(main_row, 1)

        # ── 控制按钮栏 ──
        control_bar = QHBoxLayout()
        control_bar.setSpacing(16)

        self.btn_start = PrimaryPushButton("  开始计时")
        self.btn_start.setIcon(FIF.PLAY)
        self.btn_start.setFixedHeight(42)
        self.btn_start.clicked.connect(self._on_start)
        control_bar.addWidget(self.btn_start)

        self.btn_pause = PushButton("  暂停")
        self.btn_pause.setIcon(FIF.PAUSE)
        self.btn_pause.setFixedHeight(42)
        self.btn_pause.clicked.connect(self._on_pause)
        self.btn_pause.setEnabled(False)
        control_bar.addWidget(self.btn_pause)

        self.btn_resume = PushButton("  继续")
        self.btn_resume.setIcon(FIF.PLAY)
        self.btn_resume.setFixedHeight(42)
        self.btn_resume.clicked.connect(self._on_resume)
        self.btn_resume.setEnabled(False)
        self.btn_resume.setVisible(False)
        control_bar.addWidget(self.btn_resume)

        self.btn_stop = PushButton("  停止")
        self.btn_stop.setIcon(FIF.CANCEL)
        self.btn_stop.setFixedHeight(42)
        self.btn_stop.clicked.connect(self._on_stop)
        self.btn_stop.setEnabled(False)
        control_bar.addWidget(self.btn_stop)

        control_bar.addStretch()
        layout.addLayout(control_bar)

    # ── 回调 ──────────────────────────────────────────────────

    def _on_start(self):
        from ui.setup_window import SetupWindow
        SetupWindow(self.app.start_timer, self.app.open_settings).show()

    def _on_pause(self):
        self.app.pause_timer()

    def _on_resume(self):
        self.app.resume_timer()

    def _on_stop(self):
        self.app.stop_timer()
        InfoBar.success("已停止", "计时已终止", parent=self, position=InfoBarPosition.TOP, duration=2000)

    def update_state(self, running, paused, remaining, total, session_finished):
        """由主应用每秒调用更新 UI"""
        if running and not paused:
            mins, secs = divmod(remaining, 60)
            self.lbl_time.setText(f"{mins:02d}:{secs:02d}")
            if total > 0:
                pct = int((total - remaining) / total * 100)
                self.progress_ring.setValue(pct)
                self.lbl_progress.setText(f"{pct}%")
            self.lbl_status.setText("正在计时...")
            self.lbl_status.setStyleSheet("color: #107c10;")
            self.btn_start.setEnabled(False)
            self.btn_pause.setEnabled(True)
            self.btn_resume.setVisible(False)
            self.btn_stop.setEnabled(True)

        elif paused:
            self.lbl_status.setText("已暂停")
            self.lbl_status.setStyleSheet("color: #ca5010;")
            self.btn_start.setEnabled(False)
            self.btn_pause.setEnabled(False)
            self.btn_resume.setVisible(True)
            self.btn_resume.setEnabled(True)
            self.btn_stop.setEnabled(True)

        elif session_finished:
            self.lbl_status.setText("时间到！")
            self.lbl_status.setStyleSheet("color: #d32f2f; font-weight: bold;")
            self.btn_start.setEnabled(True)
            self.btn_pause.setEnabled(False)
            self.btn_resume.setVisible(False)
            self.btn_stop.setEnabled(False)

        else:
            self.lbl_time.setText("00:00")
            self.progress_ring.setValue(0)
            self.lbl_progress.setText("0%")
            self.lbl_status.setText("等待演示开始...")
            self.lbl_status.setStyleSheet("color: #888;")
            self.btn_start.setEnabled(True)
            self.btn_pause.setEnabled(False)
            self.btn_resume.setVisible(False)
            self.btn_stop.setEnabled(False)


# ─── 设置页面 ───────────────────────────────────────────────


class SettingsPage(QWidget):
    """设置页面：内嵌 SettingsWindow 的内容，接收 cfg 而非 app_ref"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("settingsPage")
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.settings_win = SettingsWindow(cfg, embed=True)
        layout.addWidget(self.settings_win)


# ─── PPT 管理页面 ───────────────────────────────────────────


class PPTManagerPage(QWidget):
    """PPT 预设时间管理页面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("pptManagerPage")
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.manager = PPTManagerWindow(embed=True)
        layout.addWidget(self.manager)


# ─── 主窗口 ─────────────────────────────────────────────────


class MainWindow(MSFluentWindow):
    """现代 Fluent 主窗口"""

    def __init__(self, app_ref):
        super().__init__()
        self.app = app_ref
        self.setWindowTitle("演讲计时助手")
        self.resize(860, 600)
        self.setMinimumSize(640, 480)

        # 创建页面 — SettingsPage 和 PPTManagerPage 不再需要 app_ref
        self.timer_page = TimerPage(app_ref, self)
        self.settings_page = SettingsPage(self)
        self.ppt_page = PPTManagerPage(self)

        # 添加导航项
        self.addSubInterface(self.timer_page, FIF.STOP_WATCH, "计时器")
        self.addSubInterface(self.settings_page, FIF.SETTING, "设置")
        self.addSubInterface(self.ppt_page, FIF.FOLDER, "PPT管理")

        # 默认选中计时器
        self.switchTo(self.timer_page)

        self._prev_ppt_path = None

    def on_timer_update(self, running, paused, remaining, total, session_finished):
        """由 SlidesTimerApp 回调"""
        self.timer_page.update_state(running, paused, remaining, total, session_finished)

    def set_current_ppt(self, ppt_path):
        """设置当前 PPT 文件名（由 monitor 回调）"""
        self.timer_page.lbl_ppt.setText(f"📄 {os.path.basename(ppt_path)}" if ppt_path else "")
        self._prev_ppt_path = ppt_path

    def closeEvent(self, event):
        """关闭窗口 = 隐藏到托盘"""
        event.ignore()
        self.hide()
        InfoBar.info("提示", "程序已最小化到系统托盘", parent=self, position=InfoBarPosition.TOP, duration=2000)