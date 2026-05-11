import random
from pathlib import Path
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QTextEdit, QComboBox, QFrame, QApplication
)
from PyQt6.QtCore import Qt, QPropertyAnimation, QRect, QEasingCurve, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QBrush, QPixmap, QPainter, QPen


def _draw_gorilla(size=80):
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    p.setBrush(QBrush(QColor("#2d1b00")))
    p.setPen(QPen(QColor("#1a0f00"), 2))
    p.drawEllipse(2, 2, size - 4, size - 4)

    p.setBrush(QBrush(QColor("#a07030")))
    p.setPen(QPen(Qt.PenStyle.NoPen))
    fx, fy = size // 5, size // 4
    p.drawEllipse(fx, fy, size - 2 * fx, size - fy - 4)

    ey = size // 3
    p.setBrush(QBrush(QColor("white")))
    p.drawEllipse(size // 4,      ey, size // 6, size // 6)
    p.drawEllipse(size * 7 // 12, ey, size // 6, size // 6)

    p.setBrush(QBrush(QColor("#111")))
    p.drawEllipse(size // 4 + size // 14,      ey + size // 14, size // 12, size // 12)
    p.drawEllipse(size * 7 // 12 + size // 14, ey + size // 14, size // 12, size // 12)

    p.setBrush(QBrush(QColor("#2d1b00")))
    nx, ny = size // 2 - size // 8, size * 3 // 5
    p.drawEllipse(nx, ny, size // 4, size // 7)

    p.setBrush(QBrush(QColor("#111")))
    p.drawEllipse(nx + 2, ny + 2, size // 14, size // 14)
    p.drawEllipse(nx + size // 4 - size // 14 - 2, ny + 2, size // 14, size // 14)

    p.setPen(QPen(QColor("#111"), 2))
    p.setBrush(QBrush(Qt.BrushStyle.NoBrush))
    from PyQt6.QtCore import QRect as QR
    p.drawArc(QR(size // 3, ny + size // 6, size // 3, size // 8), 0, -180 * 16)

    p.end()
    return pm


class GorillaWidget(QWidget):
    task_updated       = pyqtSignal()
    visibility_changed = pyqtSignal(bool)   # True = visible, False = hidden

    def __init__(self):
        super().__init__()
        self._visible_state  = False
        self._hide_connected = False
        self._setup_ui()
        self._setup_animation()
        self._setup_timer()

    def _setup_ui(self):
        screen = QApplication.primaryScreen().availableGeometry()
        W, H = 310, 390

        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(W, H)

        self._open_pos   = QRect(screen.width() - W - 16, screen.height() - H - 10, W, H)
        self._closed_pos = QRect(screen.width() - W - 16, screen.height() + 10,     W, H)
        self.setGeometry(self._closed_pos)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(4, 4, 4, 4)
        outer.setSpacing(4)

        # Gorilla image
        self.gorilla_lbl = QLabel()
        self.gorilla_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.gorilla_lbl.setStyleSheet("background: transparent;")
        self._reload_gorilla_image()
        outer.addWidget(self.gorilla_lbl)

        # Card
        card = QWidget()
        card.setObjectName("card")
        cl = QVBoxLayout(card)
        cl.setContentsMargins(12, 10, 12, 10)
        cl.setSpacing(7)

        heading_row = QHBoxLayout()
        self.heading_lbl = QLabel("What are you doing?")
        self.heading_lbl.setObjectName("heading")
        heading_row.addWidget(self.heading_lbl, 1)
        close_btn = QPushButton("×")
        close_btn.setFixedSize(22, 22)
        close_btn.setStyleSheet(
            "QPushButton{background:transparent;color:#e94560;border:none;"
            "font-size:16px;font-weight:bold;border-radius:4px;}"
            "QPushButton:hover{color:#c73652;background:rgba(233,69,96,0.15);}"
        )
        close_btn.clicked.connect(self._slide_down)
        heading_row.addWidget(close_btn)
        cl.addLayout(heading_row)

        task_row = QHBoxLayout()
        task_lbl = QLabel("Task:")
        task_lbl.setObjectName("smallLabel")
        task_row.addWidget(task_lbl)
        self.task_combo = QComboBox()
        task_row.addWidget(self.task_combo, 1)
        cl.addLayout(task_row)

        self.text_area = QTextEdit()
        self.text_area.setPlaceholderText("Type what you're doing...")
        self.text_area.setMaximumHeight(65)
        self.text_area.setMinimumHeight(50)
        cl.addWidget(self.text_area)

        btn_row = QHBoxLayout()
        confirm_btn = QPushButton("Confirm")
        confirm_btn.setObjectName("confirmBtn")
        confirm_btn.setStyleSheet(
            "QPushButton{background:#4caf50;color:white;border:none;"
            "border-radius:6px;padding:6px 10px;font-size:12px;font-weight:bold;}"
            "QPushButton:hover{background:#43a047;}"
        )
        confirm_btn.clicked.connect(self._confirm)

        same_btn = QPushButton("Same Thing")
        same_btn.setObjectName("sameBtn")
        same_btn.setStyleSheet(
            "QPushButton{background:#0f3460;color:#eaeaea;border:1px solid #2d3748;"
            "border-radius:6px;padding:6px 10px;font-size:12px;}"
            "QPushButton:hover{background:#1a3a60;}"
        )
        same_btn.clicked.connect(self._doing_same)

        btn_row.addWidget(confirm_btn)
        btn_row.addWidget(same_btn)
        cl.addLayout(btn_row)

        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet("background:#2d3748;max-height:1px;")
        cl.addWidget(divider)

        status_lbl = QLabel("Task Status:")
        status_lbl.setObjectName("smallLabel")
        cl.addWidget(status_lbl)

        self.status_combo = QComboBox()
        self.status_combo.addItems(["Update Sent", "In Progress", "Pending"])
        cl.addWidget(self.status_combo)

        finish_btn = QPushButton("Finished This Task")
        finish_btn.setObjectName("finishBtn")
        finish_btn.setStyleSheet(
            "QPushButton{background:#e94560;color:white;border:none;"
            "border-radius:6px;padding:7px 10px;font-size:12px;font-weight:bold;}"
            "QPushButton:hover{background:#c73652;}"
        )
        finish_btn.clicked.connect(self._finish_task)
        cl.addWidget(finish_btn)

        outer.addWidget(card)

    def _reload_gorilla_image(self):
        from app.paths import assets_dir
        asset = assets_dir() / "gorilla.png"
        if asset.exists():
            pm = QPixmap(str(asset)).scaled(
                80, 80,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
        else:
            pm = _draw_gorilla(80)
        self.gorilla_lbl.setPixmap(pm)

    def _setup_animation(self):
        self.anim = QPropertyAnimation(self, b"geometry")
        self.anim.setDuration(700)

    def _setup_timer(self):
        self._gtimer = QTimer()
        self._gtimer.setSingleShot(True)
        self._gtimer.timeout.connect(self._check_and_show)
        self._reschedule()

    def _reschedule(self):
        from app.database import get_setting
        if get_setting('gorilla_enabled', 'false') != 'true':
            return
        itype = get_setting('gorilla_interval_type', 'fixed')
        if itype == 'random':
            lo = int(get_setting('gorilla_random_min', '120'))
            hi = int(get_setting('gorilla_random_max', '300'))
            secs = random.randint(lo, hi)
        else:
            secs = int(get_setting('gorilla_interval_seconds', '120'))
        self._gtimer.start(secs * 1000)

    def _check_and_show(self):
        from app.database import get_setting, get_unfinished_tasks_today
        if get_setting('gorilla_enabled', 'false') == 'true':
            if get_unfinished_tasks_today():
                self.show_gorilla()
        self._reschedule()

    def show_gorilla(self):
        if self._visible_state:
            return
        from app.database import get_setting, get_unfinished_tasks_today
        self.heading_lbl.setText(get_setting('gorilla_message', 'What are you doing?'))
        self.text_area.clear()
        self.text_area.setStyleSheet("")
        self.status_combo.setCurrentIndex(0)

        # Populate task dropdown
        self.task_combo.clear()
        tasks = get_unfinished_tasks_today()
        if tasks:
            for t in tasks:
                icon = "▶" if t['timer_status'] == 'running' else "⏸"
                self.task_combo.addItem(f"{icon} {t['task_name']}", t['id'])
        else:
            self.task_combo.addItem("No active tasks", -1)
        self._visible_state = True
        self.visibility_changed.emit(True)
        self.setGeometry(self._closed_pos)
        self.show()
        self.raise_()
        self.anim.stop()
        self.anim.setEasingCurve(QEasingCurve.Type.OutBack)
        self.anim.setStartValue(self._closed_pos)
        self.anim.setEndValue(self._open_pos)
        self.anim.start()

    def _slide_down(self):
        self.anim.stop()
        if self._hide_connected:
            try:
                self.anim.finished.disconnect(self._on_hidden)
            except Exception:
                pass
        self.anim.finished.connect(self._on_hidden)
        self._hide_connected = True
        self.anim.setEasingCurve(QEasingCurve.Type.InCubic)
        self.anim.setStartValue(self.geometry())
        self.anim.setEndValue(self._closed_pos)
        self.anim.start()

    def _on_hidden(self):
        try:
            self.anim.finished.disconnect(self._on_hidden)
        except Exception:
            pass
        self._hide_connected = False
        self.hide()
        self._visible_state = False
        self.visibility_changed.emit(False)

    def _confirm(self):
        text = self.text_area.toPlainText().strip()
        if not text:
            self.text_area.setStyleSheet(
                "background:#0f3460;color:#eaeaea;border:2px solid #e94560;"
                "border-radius:6px;padding:6px;font-size:12px;"
            )
            return
        self.text_area.setStyleSheet("")
        task_id = self.task_combo.currentData()
        if task_id and task_id != -1:
            from app.database import get_connection, update_task
            with get_connection() as conn:
                row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
            if row:
                task = dict(row)
                existing = task.get('what_done') or ''
                update_task(task_id, what_done=text if not existing else f"{existing} | {text}")
                self.task_updated.emit()
        self._slide_down()
        from app.toast import show_toast
        show_toast("Logged!")

    def _doing_same(self):
        self._slide_down()

    def _finish_task(self):
        task_id = self.task_combo.currentData()
        if not task_id or task_id == -1:
            self._slide_down()
            return
        from app.database import get_connection, update_task
        from app.task_table import calc_duration
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if not row:
            self._slide_down()
            return
        task     = dict(row)
        text     = self.text_area.toPlainText().strip()
        status   = self.status_combo.currentText()
        now      = datetime.now().strftime("%H:%M")
        existing = task.get('what_done') or ''
        new_what = (text if not existing else f"{existing} | {text}") if text else existing
        duration = calc_duration(task['start_time'], now) if task.get('start_time') else ""
        update_task(task_id, what_done=new_what, end_time=now, duration=duration,
                    timer_status='finished', eod_status=status)
        self.task_updated.emit()
        self._slide_down()
        from app.toast import show_toast
        show_toast(f"Task finished! Status: {status}")
