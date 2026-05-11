from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFrame, QApplication, QMessageBox
)
from PyQt6.QtCore import Qt, QPropertyAnimation, QRect, QEasingCurve, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QPainter, QBrush, QPen, QPixmap

from app.database import reset_timers


def _load_panel_icon(name, size=22):
    """Return QIcon from assets/<name>, or None if missing."""
    from app.paths import assets_dir
    from PyQt6.QtGui import QIcon, QPixmap
    path = assets_dir() / name
    if path.exists():
        pm = QPixmap(str(path)).scaled(
            size, size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        return QIcon(pm)
    return None


def _asset_pixmap(name, w, h):
    """Load a pixmap from assets, scaled to w×h. Returns None if missing."""
    from app.paths import assets_dir
    p = assets_dir() / name
    if p.exists():
        return QPixmap(str(p)).scaled(
            w, h,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
    return None


class FloatingButton(QWidget):
    """Always-on-top pill button anchored near the right screen edge.

    Section order (top → bottom):
        [BOOKMARK]  — optional, if bookmarks module enabled
        [MAIN ICON] — always present (opens EOD panel)
        [GORILLA]   — optional, if gorilla module enabled
    """
    clicked           = pyqtSignal()
    gorilla_clicked   = pyqtSignal()
    bookmarks_clicked = pyqtSignal()

    _PANEL_H    = 60
    _SEP        = 5
    _GORILLA_H  = 30
    _BOOKMARK_H = 30
    _MARGIN     = 16   # gap from screen right edge

    def __init__(self):
        super().__init__()
        self._open              = False
        self._gorilla_active    = False
        self._gorilla_visible   = False
        self._bookmarks_active  = False
        self._bookmarks_visible = False
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.FramelessWindowHint  |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._resize()
        self._reposition(0)

    # ── Geometry ──────────────────────────────────────────────────────────────

    def _resize(self):
        h = self._PANEL_H
        if self._bookmarks_active:
            h += self._SEP + self._BOOKMARK_H
        if self._gorilla_active:
            h += self._SEP + self._GORILLA_H
        self.setFixedSize(28, h)

    def _reposition(self, panel_width=0):
        screen = QApplication.primaryScreen().availableGeometry()
        self.move(
            screen.width() - self.width() - panel_width - self._MARGIN,
            (screen.height() - self.height()) // 2
        )

    # Section Y coordinates ───────────────────────────────────────────────────

    def _bookmark_top(self):
        """Bookmark section is always at y=0 when active."""
        return 0

    def _icon_top(self):
        """Main icon section starts below bookmark section (if active)."""
        return (self._BOOKMARK_H + self._SEP) if self._bookmarks_active else 0

    def _gorilla_top(self):
        """Gorilla section starts below the icon section."""
        return self._icon_top() + self._PANEL_H + self._SEP

    # ── State setters ─────────────────────────────────────────────────────────

    def set_open(self, is_open, panel_width=0):
        self._open = is_open
        self._reposition(panel_width)
        self.update()

    def set_gorilla_active(self, active):
        self._gorilla_active = active
        self._resize()
        self._reposition(0)
        self.update()

    def set_gorilla_visible(self, visible):
        self._gorilla_visible = visible
        self.update()

    def set_bookmarks_active(self, active):
        self._bookmarks_active = active
        self._resize()
        self._reposition(0)
        self.update()

    def set_bookmarks_visible(self, visible):
        self._bookmarks_visible = visible
        self.update()

    # ── Paint ─────────────────────────────────────────────────────────────────

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        from PyQt6.QtCore import QRect as QR

        W, H = self.width(), self.height()

        # White capsule with red border
        p.setBrush(QBrush(QColor("white")))
        p.setPen(QPen(QColor("#e94560"), 2))
        p.drawRoundedRect(1, 1, W - 2, H - 2, 9, 9)

        # ── Bookmark section (TOP) ────────────────────────────────────────────
        if self._bookmarks_active:
            bm_rect = QR(2, 2, W - 4, self._BOOKMARK_H - 2)
            p.setBrush(QBrush(QColor("#f5f5f5")))   # no colour change when active
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(bm_rect, 6, 6)

            # Use bookmark.png if available, else text symbol
            bm_pm = _asset_pixmap("bookmark.png", 16, 16)
            if bm_pm:
                px = (W - bm_pm.width()) // 2
                py = 2 + (self._BOOKMARK_H - 4 - bm_pm.height()) // 2
                p.drawPixmap(px, py, bm_pm)
            else:
                p.setPen(QPen(QColor("#e94560")))
                p.setFont(QFont("Segoe UI Emoji", 9))
                p.drawText(bm_rect, Qt.AlignmentFlag.AlignCenter, "\U0001f516")

            # Separator between bookmark and icon
            sep_y = self._BOOKMARK_H + self._SEP // 2
            p.setPen(QPen(QColor("#e94560"), 1))
            p.drawLine(4, sep_y, W - 4, sep_y)

        # ── Main icon section (MIDDLE) ────────────────────────────────────────
        icon_top = self._icon_top()
        dpr      = self.devicePixelRatioF()
        icon_sz  = int(20 * dpr)
        from app.icon_utils import app_pixmap
        pm = app_pixmap(icon_sz)
        pm.setDevicePixelRatio(dpr)
        ix = (W - 20) // 2
        iy = icon_top + (self._PANEL_H - 20) // 2
        p.drawPixmap(ix, iy, pm)

        # ── Gorilla section (BOTTOM) ──────────────────────────────────────────
        if self._gorilla_active:
            g_top  = self._gorilla_top()
            sep_y2 = g_top - self._SEP // 2 - 1
            p.setPen(QPen(QColor("#e94560"), 1))
            p.drawLine(4, sep_y2, W - 4, sep_y2)

            g_rect = QR(2, g_top, W - 4, self._GORILLA_H - 2)
            p.setBrush(QBrush(QColor("#f5f5f5")))   # no colour change when active
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(g_rect, 6, 6)

            # Use gorilla.png if available
            g_pm = _asset_pixmap("gorilla.png", W - 8, self._GORILLA_H - 6)
            if g_pm:
                gx = (W - g_pm.width()) // 2
                gy = g_top + (self._GORILLA_H - g_pm.height()) // 2
                p.drawPixmap(gx, gy, g_pm)
            else:
                p.setPen(QPen(QColor("white")))
                p.setFont(QFont("Segoe UI Emoji", 10))
                p.drawText(g_rect, Qt.AlignmentFlag.AlignCenter, "\U0001f98d")

    # ── Mouse ─────────────────────────────────────────────────────────────────

    def mousePressEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            return
        y = int(event.position().y())

        # Bookmark section (top)
        if self._bookmarks_active and y < self._BOOKMARK_H:
            self.bookmarks_clicked.emit()
            return

        # Main icon section (middle)
        icon_top = self._icon_top()
        if icon_top <= y < icon_top + self._PANEL_H:
            self.clicked.emit()
            return

        # Gorilla section (bottom)
        if self._gorilla_active and y >= self._gorilla_top():
            self.gorilla_clicked.emit()


# ── FloatingPanel ─────────────────────────────────────────────────────────────

class FloatingPanel(QWidget):
    def __init__(self):
        super().__init__()
        self._panel_open = False
        self.settings_window = None
        self._setup_panel_ui()
        self._setup_floating_button()
        self._setup_gorilla()
        self._setup_bookmarks()

    def _setup_panel_ui(self):
        screen = QApplication.primaryScreen().availableGeometry()
        self._screen      = screen
        self._panel_width = screen.width() // 2

        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.FramelessWindowHint  |
            Qt.WindowType.Tool
        )
        self.setObjectName("panel")
        self.setFixedSize(self._panel_width, screen.height())

        self._closed_rect = QRect(screen.width(), 0, self._panel_width, screen.height())
        self._open_rect   = QRect(screen.width() - self._panel_width, 0, self._panel_width, screen.height())
        self.setGeometry(self._closed_rect)

        self.anim = QPropertyAnimation(self, b"geometry")
        self.anim.setDuration(300)
        self.anim.setEasingCurve(QEasingCurve.Type.InOutQuart)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QWidget()
        header.setObjectName("header")
        header.setFixedHeight(50)
        hl = QHBoxLayout(header)
        hl.setContentsMargins(10, 5, 10, 5)

        # Tray icon acts as the close/back button
        from app.icon_utils import app_pixmap
        from PyQt6.QtCore import QSize
        logo_btn = QPushButton()
        logo_btn.setFixedSize(34, 34)
        logo_btn.setIcon(_load_panel_icon("tray_icon.png", 28) or _load_panel_icon("tray_icon.ico", 28))
        logo_btn.setIconSize(QSize(28, 28))
        logo_btn.setToolTip("Close panel")
        logo_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        logo_btn.setStyleSheet(
            "QPushButton{background:transparent;border:none;border-radius:8px;padding:2px;}"
            "QPushButton:hover{background:rgba(233,69,96,0.12);}"
        )
        logo_btn.clicked.connect(self.close_panel)

        title = QLabel("EOD Task Tracker")
        title.setObjectName("title")

        settings_btn = QPushButton("Settings")
        settings_btn.setObjectName("settingsBtn")
        settings_btn.clicked.connect(self.open_settings)

        hl.addWidget(logo_btn)
        hl.addWidget(title)
        hl.addStretch()
        hl.addWidget(settings_btn)
        layout.addWidget(header)

        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet("background:#e94560; max-height:1px;")
        layout.addWidget(divider)

        # Content
        content = QWidget()
        content.setObjectName("content")
        cl = QVBoxLayout(content)
        cl.setContentsMargins(10, 10, 10, 6)
        cl.setSpacing(8)

        from app.task_form import TaskForm
        self.task_form = TaskForm()
        self.task_form.task_added.connect(self._refresh_table)
        cl.addWidget(self.task_form)

        from app.task_table import TaskTable
        self.task_table = TaskTable()
        cl.addWidget(self.task_table, 1)

        layout.addWidget(content, 1)

        # Bottom bar
        bottom = QWidget()
        bottom.setObjectName("bottomBar")
        bl = QHBoxLayout(bottom)
        bl.setContentsMargins(10, 8, 10, 8)
        bl.setSpacing(8)

        reset_btn = QPushButton("Reset Day")
        reset_btn.setObjectName("resetBtn")
        reset_btn.setFixedWidth(90)
        reset_btn.setToolTip("Clear all timers for a fresh day")
        reset_btn.clicked.connect(self._reset_day)
        bl.addWidget(reset_btn)

        export_btn = QPushButton("Download Today's Excel Report")
        export_btn.setObjectName("exportBtn")
        export_btn.clicked.connect(self._export_excel)
        bl.addWidget(export_btn, 1)

        layout.addWidget(bottom)

    def _setup_floating_button(self):
        self.float_btn = FloatingButton()
        self.float_btn.clicked.connect(self.toggle_panel)
        self.float_btn.gorilla_clicked.connect(self._toggle_gorilla)
        self.float_btn.bookmarks_clicked.connect(self._toggle_bookmarks)
        self.float_btn.show()

    def _setup_gorilla(self):
        from app.gorilla import GorillaWidget
        from app.database import get_setting
        self.gorilla = GorillaWidget()
        self.gorilla.task_updated.connect(self._refresh_table)
        self.gorilla.visibility_changed.connect(self.float_btn.set_gorilla_visible)
        self.float_btn.set_gorilla_active(
            get_setting('gorilla_enabled', 'false') == 'true'
        )

    def _setup_bookmarks(self):
        from app.bookmarks import BookmarksPanel
        from app.database import get_setting
        self.bookmarks = BookmarksPanel()
        self.bookmarks.closed.connect(self._on_bookmarks_closed)
        self.float_btn.set_bookmarks_active(
            get_setting('bookmarks_enabled', 'false') == 'true'
        )

    # ── Panel open / close ────────────────────────────────────────────────────

    def toggle_panel(self):
        self.close_panel() if self._panel_open else self.open_panel()

    def open_panel(self):
        if self._panel_open:
            return
        # Close bookmarks panel if open (exclusive)
        if self.bookmarks._visible_state:
            self.bookmarks.close_panel_instant()
            self.float_btn.set_bookmarks_visible(False)
        self._panel_open = True
        self._refresh_table()
        self.float_btn.set_open(True, self._panel_width)
        self.anim.stop()
        self.anim.setStartValue(self.geometry())
        self.anim.setEndValue(self._open_rect)
        self.anim.start()
        self.show()
        self.raise_()

    def close_panel(self):
        if not self._panel_open:
            return
        self._panel_open = False
        self.float_btn.set_open(False, 0)
        self.anim.stop()
        self.anim.setStartValue(self.geometry())
        self.anim.setEndValue(self._closed_rect)
        self.anim.start()

    def _on_bookmarks_closed(self):
        self.float_btn.set_open(False, 0)
        self.float_btn.set_bookmarks_visible(False)

    # ── Actions ───────────────────────────────────────────────────────────────

    def _refresh_table(self):
        self.task_table.refresh()

    def _export_excel(self):
        from app.excel_export import export_excel
        export_excel(parent=self)

    def _reset_day(self):
        dlg = QMessageBox(self)
        dlg.setWindowFlags(dlg.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        dlg.setWindowTitle("Reset Day?")
        dlg.setText(
            "This will clear all timer data (start time, end time, duration, notes) "
            "for all active tasks.\n\nUse this at the start of a new day.\n\nContinue?"
        )
        dlg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        dlg.button(QMessageBox.StandardButton.Yes).setText("Reset")
        if dlg.exec() == QMessageBox.StandardButton.Yes:
            reset_timers()
            self._refresh_table()
            from app.toast import show_toast
            show_toast("Day reset! All timers cleared.")

    def open_settings(self):
        from app.settings import SettingsWindow
        if not self.settings_window or not self.settings_window.isVisible():
            self.settings_window = SettingsWindow()
            self.settings_window.settings_saved.connect(self._on_settings_saved)
            self.settings_window.show()
            self.settings_window.raise_()
            self.settings_window.activateWindow()
        else:
            self.settings_window.raise_()
            self.settings_window.activateWindow()

    def _toggle_gorilla(self):
        if self.gorilla._visible_state:
            self.gorilla._slide_down()
        else:
            self.gorilla.show_gorilla()

    def _toggle_bookmarks(self):
        if self.bookmarks._visible_state:
            self.bookmarks.close_panel()
        else:
            # Close main EOD panel first (exclusive)
            if self._panel_open:
                self.close_panel()
            self.bookmarks.open_panel()
            self.float_btn.set_open(True, self._panel_width)
            self.float_btn.set_bookmarks_visible(True)

    def _on_settings_saved(self):
        from app.database import get_setting
        self.task_form.refresh_employee_name()
        self.float_btn.set_gorilla_active(
            get_setting('gorilla_enabled', 'false') == 'true'
        )
        bm_enabled = get_setting('bookmarks_enabled', 'false') == 'true'
        self.float_btn.set_bookmarks_active(bm_enabled)
        if not bm_enabled and self.bookmarks._visible_state:
            self.bookmarks.close_panel()
            self.float_btn.set_open(False, 0)
