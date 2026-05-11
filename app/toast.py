from PyQt6.QtWidgets import QLabel, QApplication
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, pyqtProperty
from PyQt6.QtGui import QColor


class Toast(QLabel):
    def __init__(self, message, parent=None, duration=2000):
        super().__init__(message, parent)
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("""
            QLabel {
                background: #4caf50;
                color: white;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: bold;
            }
        """)
        self.adjustSize()
        self._position()
        self.show()
        QTimer.singleShot(duration, self._fade_out)

    def _position(self):
        screen = QApplication.primaryScreen().availableGeometry()
        self.move(
            screen.center().x() - self.width() // 2,
            screen.height() - 100
        )

    def _fade_out(self):
        self._opacity_anim = QPropertyAnimation(self, b"windowOpacity")
        self._opacity_anim.setDuration(500)
        self._opacity_anim.setStartValue(1.0)
        self._opacity_anim.setEndValue(0.0)
        self._opacity_anim.finished.connect(self.close)
        self._opacity_anim.start()


_active_toasts = []  # Keep references so Qt doesn't GC them before they fade


def show_toast(message, duration=2000, error=False):
    global _active_toasts
    # Clean up already-closed toasts
    _active_toasts = [t for t in _active_toasts if not t.isHidden()]
    toast = Toast(message, duration=duration)
    if error:
        toast.setStyleSheet("""
            QLabel {
                background: #e94560;
                color: white;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: bold;
            }
        """)
    toast._position()
    _active_toasts.append(toast)
    return toast
