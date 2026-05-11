"""
app/bookmarks.py — Client Bookmarks Panel
"""
import os
import sys
import time
import zipfile
import subprocess
import webbrowser

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QDialog, QLineEdit, QComboBox,
    QFrame, QApplication, QMessageBox, QFileDialog, QSizePolicy,
)
from PyQt6.QtCore import Qt, QPropertyAnimation, QRect, QEasingCurve, pyqtSignal, QSize, QMimeData, QUrl
from PyQt6.QtGui import QFont, QIcon, QPixmap

from app import database as db


# ── Constants ─────────────────────────────────────────────────────────────────

DATA_TYPES = ["Link", "Image", "File", "PDF", "Video", "Document", "Folder", "Other"]

TYPE_ICONS = {
    "Link":     "\U0001f517",
    "Image":    "\U0001f5bc",
    "File":     "\U0001f4c1",
    "PDF":      "\U0001f4c4",
    "Video":    "\U0001f3ac",
    "Document": "\U0001f4dd",
    "Folder":   "\U0001f4c2",
    "Other":    "\U0001f4ce",
}

_ICON_BTN_STYLE = """
    QPushButton {{
        background: transparent; border: none;
        color: {color}; font-size: 14px;
        font-family: 'Segoe UI', Arial;
        padding: 0px; border-radius: 4px;
        min-width: 26px; min-height: 26px;
    }}
    QPushButton:hover {{ color: #e94560; background: rgba(233,69,96,0.12); }}
"""

_PIN_ACTIVE_STYLE   = _ICON_BTN_STYLE.format(color="#e94560")
_PIN_INACTIVE_STYLE = _ICON_BTN_STYLE.format(color="#888888")
_DEL_BTN_STYLE      = _ICON_BTN_STYLE.format(color="#888888")
_OPEN_BTN_STYLE     = _ICON_BTN_STYLE.format(color="#3a7bd5")
_COPY_BTN_STYLE     = _ICON_BTN_STYLE.format(color="#4caf50")


# ── Asset helpers ──────────────────────────────────────────────────────────────

def _load_icon(name: str, size: int = 16) -> QIcon:
    from app.paths import assets_dir
    path = assets_dir() / name
    if path.exists():
        pm = QPixmap(str(path)).scaled(
            size, size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        return QIcon(pm)
    return QIcon()


def _add_icon(size=16):
    return _load_icon("add.png", size)


# ── Clipboard helpers ─────────────────────────────────────────────────────────

def _zip_to_cache(folder_path: str) -> str:
    """Zip a folder into the app's data/zips cache. Returns zip path."""
    from app.paths import data_dir
    cache = data_dir() / "zips"
    cache.mkdir(exist_ok=True)

    # Clean zips older than 24 h
    for old in cache.glob("*.zip"):
        try:
            if time.time() - old.stat().st_mtime > 86400:
                old.unlink()
        except Exception:
            pass

    name     = os.path.basename(folder_path.rstrip("/\\")) or "folder"
    zip_path = str(cache / f"{name}.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(folder_path):
            for f in files:
                abs_p  = os.path.join(root, f)
                arcname = os.path.relpath(abs_p, os.path.dirname(folder_path))
                zf.write(abs_p, arcname)
    return zip_path


def _copy_path_to_clipboard(file_path: str):
    """Copy a file/folder path so it pastes as an actual file anywhere."""
    mime = QMimeData()
    mime.setUrls([QUrl.fromLocalFile(file_path)])
    QApplication.clipboard().setMimeData(mime)


# ── Dialogs ───────────────────────────────────────────────────────────────────

class AddClientDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Client")
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        self.setMinimumWidth(320)
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.addWidget(QLabel("Client Name:"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g. ATB Media")
        layout.addWidget(self.name_input)
        btns = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        add_btn = QPushButton("Add Client")
        add_btn.setDefault(True)
        ai = _add_icon(16)
        if not ai.isNull():
            add_btn.setIcon(ai)
        add_btn.clicked.connect(self._accept)
        btns.addStretch()
        btns.addWidget(cancel_btn)
        btns.addWidget(add_btn)
        layout.addLayout(btns)

    def _accept(self):
        if self.name_input.text().strip():
            self.accept()
        else:
            self.name_input.setFocus()

    def get_name(self):
        return self.name_input.text().strip()


class AddItemDialog(QDialog):
    def __init__(self, clients, current_client_id=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Bookmark Data")
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        self.setMinimumWidth(420)
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(16, 16, 16, 16)

        layout.addWidget(QLabel("Data Name:"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g. Client Main Sheet")
        layout.addWidget(self.name_input)

        layout.addWidget(QLabel("Type:"))
        self.type_combo = QComboBox()
        for t in DATA_TYPES:
            self.type_combo.addItem(f"{TYPE_ICONS.get(t, '')}  {t}")
        self.type_combo.currentIndexChanged.connect(self._on_type_changed)
        layout.addWidget(self.type_combo)

        layout.addWidget(QLabel("Content:"))
        content_row = QHBoxLayout()
        self.content_input = QLineEdit()
        self.content_input.setPlaceholderText("https://...")
        content_row.addWidget(self.content_input, 1)
        self.browse_btn = QPushButton("Browse")
        self.browse_btn.setFixedWidth(72)
        self.browse_btn.setVisible(False)
        self.browse_btn.clicked.connect(self._browse)
        content_row.addWidget(self.browse_btn)
        layout.addLayout(content_row)

        layout.addWidget(QLabel("Client:"))
        self.client_combo = QComboBox()
        for c in clients:
            self.client_combo.addItem(c['name'], c['id'])
        if current_client_id is not None:
            for i, c in enumerate(clients):
                if c['id'] == current_client_id:
                    self.client_combo.setCurrentIndex(i)
                    break
        layout.addWidget(self.client_combo)

        btns = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        add_btn = QPushButton("Add Data")
        add_btn.setDefault(True)
        ai = _add_icon(16)
        if not ai.isNull():
            add_btn.setIcon(ai)
        add_btn.clicked.connect(self._accept)
        btns.addStretch()
        btns.addWidget(cancel_btn)
        btns.addWidget(add_btn)
        layout.addLayout(btns)

    def _on_type_changed(self, idx):
        t = DATA_TYPES[idx]
        self.browse_btn.setVisible(t != "Link")
        self.content_input.setPlaceholderText(
            "https://..." if t == "Link"
            else "Folder path  (or click Browse)" if t == "Folder"
            else f"{t} path  (or click Browse)"
        )

    def _browse(self):
        t = DATA_TYPES[self.type_combo.currentIndex()]
        if t == "Folder":
            path = QFileDialog.getExistingDirectory(self, "Select Folder", "")
            if path:
                self.content_input.setText(path)
            return
        filters = {
            "Image":    "Images (*.png *.jpg *.jpeg *.gif *.bmp *.webp *.svg)",
            "PDF":      "PDF Files (*.pdf)",
            "Video":    "Videos (*.mp4 *.avi *.mov *.mkv *.wmv *.flv)",
            "Document": "Documents (*.doc *.docx *.txt *.xlsx *.xls *.pptx *.ppt)",
        }.get(t, "All Files (*.*)")
        path, _ = QFileDialog.getOpenFileName(self, f"Select {t}", "", filters)
        if path:
            self.content_input.setText(path)

    def _accept(self):
        if not self.name_input.text().strip() or not self.content_input.text().strip():
            (self.name_input if not self.name_input.text().strip()
             else self.content_input).setFocus()
            return
        self.accept()

    def get_data(self):
        return {
            'data_name': self.name_input.text().strip(),
            'data_type': DATA_TYPES[self.type_combo.currentIndex()],
            'content':   self.content_input.text().strip(),
            'client_id': self.client_combo.currentData(),
        }


class BrowserPickerDialog(QDialog):
    def __init__(self, url, browsers, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Open in Browser")
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        self.setMinimumWidth(300)
        self.url = url
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(8)
        short = url if len(url) <= 60 else url[:57] + "..."
        lbl = QLabel(f"<b>Open URL:</b><br><small>{short}</small>")
        lbl.setWordWrap(True)
        layout.addWidget(lbl)
        layout.addWidget(QLabel("Choose browser:"))
        for name, path in browsers:
            btn = QPushButton(name)
            btn.clicked.connect(lambda checked, p=path: self._open_with(p))
            layout.addWidget(btn)
        default_btn = QPushButton("Default Browser")
        default_btn.clicked.connect(self._open_default)
        layout.addWidget(default_btn)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(cancel_btn)

    def _open_with(self, path):
        try:
            subprocess.Popen([path, self.url])
        except Exception:
            webbrowser.open(self.url)
        self.accept()

    def _open_default(self):
        webbrowser.open(self.url)
        self.accept()


# ── Row widgets ───────────────────────────────────────────────────────────────

class ClientRowWidget(QWidget):
    selected    = pyqtSignal(int)
    pin_toggled = pyqtSignal(int)
    deleted     = pyqtSignal(int)

    def __init__(self, client, is_selected=False, parent=None):
        super().__init__(parent)
        self.client_id = client['id']
        self.is_pinned = bool(client['is_pinned'])
        self.setAutoFillBackground(True)
        self.setStyleSheet("QWidget{background:transparent;}")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 3, 6, 3)
        layout.setSpacing(4)

        drag = QLabel("\u2630")
        drag.setFixedWidth(16)
        drag.setStyleSheet("color:#666;font-size:13px;background:transparent;")
        layout.addWidget(drag)

        self.name_btn = QPushButton(client['name'])
        self.name_btn.setFixedHeight(28)
        self.name_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._apply_name_style(is_selected)
        self.name_btn.clicked.connect(lambda: self.selected.emit(self.client_id))
        layout.addWidget(self.name_btn, 1)

        pin_icon = _load_icon("pinned.png" if self.is_pinned else "pin.png", 16)
        self.pin_btn = QPushButton()
        self.pin_btn.setFixedSize(26, 26)
        if not pin_icon.isNull():
            self.pin_btn.setIcon(pin_icon)
            self.pin_btn.setIconSize(QSize(16, 16))
        else:
            self.pin_btn.setText("\u25cf" if self.is_pinned else "\u25cb")
        self.pin_btn.setStyleSheet(_PIN_ACTIVE_STYLE if self.is_pinned else _PIN_INACTIVE_STYLE)
        self.pin_btn.setToolTip("Unpin" if self.is_pinned else "Pin to top")
        self.pin_btn.clicked.connect(lambda: self.pin_toggled.emit(self.client_id))
        layout.addWidget(self.pin_btn)

        del_icon = _load_icon("remove.png", 16)
        del_btn = QPushButton()
        del_btn.setFixedSize(26, 26)
        if not del_icon.isNull():
            del_btn.setIcon(del_icon)
            del_btn.setIconSize(QSize(16, 16))
        else:
            del_btn.setText("\u00d7")
        del_btn.setStyleSheet(_DEL_BTN_STYLE)
        del_btn.setToolTip("Delete client")
        del_btn.clicked.connect(lambda: self.deleted.emit(self.client_id))
        layout.addWidget(del_btn)

    def _apply_name_style(self, selected):
        if selected:
            self.name_btn.setStyleSheet(
                "QPushButton{text-align:left;padding:2px 8px;font-weight:bold;"
                "color:#e94560;background:rgba(233,69,96,0.1);border:1px solid #e94560;"
                "border-radius:5px;font-size:13px;}"
                "QPushButton:hover{background:rgba(233,69,96,0.2);}"
            )
        else:
            self.name_btn.setStyleSheet(
                "QPushButton{text-align:left;padding:2px 8px;font-weight:bold;"
                "color:inherit;background:transparent;border:1px solid transparent;"
                "border-radius:5px;font-size:13px;}"
                "QPushButton:hover{border-color:#e94560;color:#e94560;}"
            )


class ItemRowWidget(QWidget):
    """drag | type icon | [name + content] | open | copy | pin | delete"""
    opened      = pyqtSignal(int)
    pin_toggled = pyqtSignal(int)
    deleted     = pyqtSignal(int)

    def __init__(self, item, parent=None):
        super().__init__(parent)
        self.item_id   = item['id']
        self.content   = item['content']
        self.data_type = item['data_type']
        self.is_pinned = bool(item['is_pinned'])

        self.setAutoFillBackground(True)
        self.setStyleSheet("QWidget{background:transparent;}")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(2)

        # ── Top row ───────────────────────────────────────────────────────────
        top = QHBoxLayout()
        top.setSpacing(4)

        drag = QLabel("\u2630")
        drag.setFixedWidth(16)
        drag.setStyleSheet("color:#666;font-size:13px;background:transparent;")
        top.addWidget(drag)

        icon_lbl = QLabel(TYPE_ICONS.get(item['data_type'], "\U0001f4ce"))
        icon_lbl.setFixedWidth(20)
        icon_lbl.setStyleSheet("font-family:'Segoe UI Emoji';font-size:14px;background:transparent;")
        top.addWidget(icon_lbl)

        name_lbl = QLabel(item['data_name'])
        name_lbl.setStyleSheet("font-weight:bold;font-size:13px;background:transparent;")
        name_lbl.setToolTip(item['content'])
        name_lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        top.addWidget(name_lbl, 1)

        # Open
        open_icon = _load_icon("launch.png", 16)
        open_btn = QPushButton()
        open_btn.setFixedSize(26, 26)
        if not open_icon.isNull():
            open_btn.setIcon(open_icon)
            open_btn.setIconSize(QSize(16, 16))
        else:
            open_btn.setText("\u2197")
        open_btn.setStyleSheet(_OPEN_BTN_STYLE)
        open_btn.setToolTip("Open")
        open_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        open_btn.clicked.connect(lambda: self.opened.emit(self.item_id))
        top.addWidget(open_btn)

        # Copy — tooltip changes per type
        copy_tooltip = {
            "Link":   "Copy link to clipboard",
            "Folder": "Zip folder & copy — paste anywhere to share",
        }.get(item['data_type'], "Copy file to clipboard — paste anywhere to share")

        copy_btn = QPushButton()
        copy_btn.setFixedSize(26, 26)
        copy_btn.setText("\u29c9")   # ⧉
        copy_btn.setStyleSheet(_COPY_BTN_STYLE)
        copy_btn.setToolTip(copy_tooltip)
        copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        copy_btn.clicked.connect(self._handle_copy)
        top.addWidget(copy_btn)

        # Pin
        pin_icon = _load_icon("pinned.png" if self.is_pinned else "pin.png", 16)
        pin_btn = QPushButton()
        pin_btn.setFixedSize(26, 26)
        if not pin_icon.isNull():
            pin_btn.setIcon(pin_icon)
            pin_btn.setIconSize(QSize(16, 16))
        else:
            pin_btn.setText("\u25cf" if self.is_pinned else "\u25cb")
        pin_btn.setStyleSheet(_PIN_ACTIVE_STYLE if self.is_pinned else _PIN_INACTIVE_STYLE)
        pin_btn.setToolTip("Unpin" if self.is_pinned else "Pin to top")
        pin_btn.clicked.connect(lambda: self.pin_toggled.emit(self.item_id))
        top.addWidget(pin_btn)

        # Delete
        del_icon = _load_icon("remove.png", 16)
        del_btn = QPushButton()
        del_btn.setFixedSize(26, 26)
        if not del_icon.isNull():
            del_btn.setIcon(del_icon)
            del_btn.setIconSize(QSize(16, 16))
        else:
            del_btn.setText("\u00d7")
        del_btn.setStyleSheet(_DEL_BTN_STYLE)
        del_btn.setToolTip("Delete")
        del_btn.clicked.connect(lambda: self.deleted.emit(self.item_id))
        top.addWidget(del_btn)

        layout.addLayout(top)

        # ── Content preview ───────────────────────────────────────────────────
        preview = item['content']
        if len(preview) > 72:
            preview = preview[:70] + "\u2026"
        content_lbl = QLabel(preview)
        content_lbl.setStyleSheet(
            "color:#888;font-size:11px;background:transparent;padding-left:36px;"
        )
        content_lbl.setToolTip(item['content'])
        content_lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        layout.addWidget(content_lbl)

    # ── Copy logic ────────────────────────────────────────────────────────────

    def _handle_copy(self):
        from app.toast import show_toast

        if self.data_type == 'Link':
            # Plain text copy — paste the URL anywhere
            QApplication.clipboard().setText(self.content)
            show_toast("Link copied to clipboard!")

        elif self.data_type == 'Folder':
            if not os.path.exists(self.content):
                show_toast("Folder not found!")
                return
            show_toast("Zipping folder\u2026")
            QApplication.processEvents()
            try:
                zip_path = _zip_to_cache(self.content)
                _copy_path_to_clipboard(zip_path)
                show_toast("Folder zipped & copied!\nPaste anywhere to share.")
            except Exception as e:
                show_toast(f"Zip failed: {e}")

        else:
            # Image / File / PDF / Video / Document / Other
            if not os.path.exists(self.content):
                show_toast("File not found!")
                return
            _copy_path_to_clipboard(self.content)
            show_toast("File copied!\nPaste anywhere to share.")


# ── Drag-aware list ───────────────────────────────────────────────────────────

class DraggableList(QListWidget):
    order_changed = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.setSpacing(1)
        self.setUniformItemSizes(False)

    def dropEvent(self, event):
        super().dropEvent(event)
        ids = [
            self.item(i).data(Qt.ItemDataRole.UserRole)
            for i in range(self.count())
            if self.item(i).data(Qt.ItemDataRole.UserRole) is not None
        ]
        self.order_changed.emit(ids)


# ── Main bookmarks panel ──────────────────────────────────────────────────────

class BookmarksPanel(QWidget):
    closed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._visible_state      = False
        self._selected_client_id = None

        screen = QApplication.primaryScreen().availableGeometry()
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

        self._anim = QPropertyAnimation(self, b"geometry")
        self._anim.setDuration(300)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutQuart)

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QWidget()
        header.setObjectName("header")
        header.setFixedHeight(50)
        hl = QHBoxLayout(header)
        hl.setContentsMargins(10, 6, 10, 6)

        # Tray icon = close button
        logo_btn = QPushButton()
        logo_btn.setFixedSize(34, 34)
        tray_icon = _load_icon("tray_icon.png", 28)
        if not tray_icon.isNull():
            logo_btn.setIcon(tray_icon)
        logo_btn.setIconSize(QSize(28, 28))
        logo_btn.setToolTip("Close bookmarks")
        logo_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        logo_btn.setStyleSheet(
            "QPushButton{background:transparent;border:none;border-radius:8px;padding:2px;}"
            "QPushButton:hover{background:rgba(233,69,96,0.12);}"
        )
        logo_btn.clicked.connect(self.close_panel)
        hl.addWidget(logo_btn)

        lbl = QLabel("\U0001f516  Client Bookmarks")
        lbl.setObjectName("title")
        hl.addWidget(lbl)
        hl.addStretch()

        add_client_btn = QPushButton("+ Client")
        add_client_btn.setObjectName("settingsBtn")
        ai = _add_icon(16)
        if not ai.isNull():
            add_client_btn.setIcon(ai)
            add_client_btn.setIconSize(QSize(16, 16))
        add_client_btn.clicked.connect(self._add_client)
        hl.addWidget(add_client_btn)

        layout.addWidget(header)

        div = QFrame()
        div.setFrameShape(QFrame.Shape.HLine)
        div.setStyleSheet("background:#e94560;max-height:1px;")
        layout.addWidget(div)

        # Body
        body = QWidget()
        body.setObjectName("content")
        bl = QVBoxLayout(body)
        bl.setContentsMargins(12, 10, 12, 10)
        bl.setSpacing(8)

        cl_hdr = QHBoxLayout()
        cl_lbl = QLabel("CLIENTS")
        cl_lbl.setStyleSheet(
            "font-size:10px;font-weight:bold;letter-spacing:1px;"
            "color:#e94560;background:transparent;"
        )
        cl_hdr.addWidget(cl_lbl)
        cl_hdr.addStretch()
        bl.addLayout(cl_hdr)

        self.clients_list = DraggableList()
        self.clients_list.setFixedHeight(220)
        self.clients_list.setStyleSheet(
            "QListWidget{border:1px solid #2d3748;border-radius:6px;"
            "background:transparent;outline:none;}"
            "QListWidget::item{border-bottom:1px solid #2d3748;padding:0;}"
            "QListWidget::item:selected{background:transparent;}"
        )
        self.clients_list.order_changed.connect(self._save_client_order)
        bl.addWidget(self.clients_list)

        it_hdr = QHBoxLayout()
        self.items_section_lbl = QLabel("SELECT A CLIENT ABOVE")
        self.items_section_lbl.setStyleSheet(
            "font-size:10px;font-weight:bold;letter-spacing:1px;"
            "color:#e94560;background:transparent;"
        )
        it_hdr.addWidget(self.items_section_lbl)
        it_hdr.addStretch()
        self.add_item_btn = QPushButton("+ Add Data")
        self.add_item_btn.setObjectName("settingsBtn")
        ai2 = _add_icon(16)
        if not ai2.isNull():
            self.add_item_btn.setIcon(ai2)
            self.add_item_btn.setIconSize(QSize(16, 16))
        self.add_item_btn.setEnabled(False)
        self.add_item_btn.clicked.connect(self._add_item)
        it_hdr.addWidget(self.add_item_btn)
        bl.addLayout(it_hdr)

        self.items_list = DraggableList()
        self.items_list.setStyleSheet(
            "QListWidget{border:1px solid #2d3748;border-radius:6px;"
            "background:transparent;outline:none;}"
            "QListWidget::item{border-bottom:1px solid #2d3748;padding:0;}"
            "QListWidget::item:selected{background:transparent;}"
        )
        self.items_list.order_changed.connect(self._save_item_order)
        bl.addWidget(self.items_list, 1)

        layout.addWidget(body, 1)

    # ── Slide ─────────────────────────────────────────────────────────────────

    def open_panel(self):
        self._visible_state = True
        self._refresh_clients()
        self._anim.stop()
        self._anim.setStartValue(self.geometry())
        self._anim.setEndValue(self._open_rect)
        self._anim.start()
        self.show()
        self.raise_()

    def close_panel(self):
        if not self._visible_state:
            return
        self._visible_state = False
        self._anim.stop()
        self._anim.setStartValue(self.geometry())
        self._anim.setEndValue(self._closed_rect)
        self._anim.finished.connect(self._on_close_finished)
        self._anim.start()

    def _on_close_finished(self):
        try:
            self._anim.finished.disconnect(self._on_close_finished)
        except Exception:
            pass
        self.closed.emit()

    def close_panel_instant(self):
        self._visible_state = False
        self.setGeometry(self._closed_rect)

    # ── Clients ───────────────────────────────────────────────────────────────

    def _refresh_clients(self):
        self.clients_list.clear()
        for c in db.get_bookmark_clients():
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, c['id'])
            widget = ClientRowWidget(c, is_selected=(c['id'] == self._selected_client_id))
            widget.selected.connect(self._select_client)
            widget.pin_toggled.connect(self._toggle_client_pin)
            widget.deleted.connect(self._delete_client)
            item.setSizeHint(QSize(self.clients_list.width() - 4, 38))
            self.clients_list.addItem(item)
            self.clients_list.setItemWidget(item, widget)

    def _add_client(self):
        dlg = AddClientDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            db.add_bookmark_client(dlg.get_name())
            self._refresh_clients()

    def _select_client(self, client_id):
        self._selected_client_id = client_id
        for i in range(self.clients_list.count()):
            w = self.clients_list.itemWidget(self.clients_list.item(i))
            if isinstance(w, ClientRowWidget):
                w._apply_name_style(w.client_id == client_id)
        self._refresh_items(client_id)

    def _toggle_client_pin(self, client_id):
        clients = db.get_bookmark_clients()
        cur = next((c for c in clients if c['id'] == client_id), None)
        if cur:
            db.update_bookmark_client(client_id, is_pinned=0 if cur['is_pinned'] else 1)
            self._refresh_clients()
            if self._selected_client_id == client_id:
                self._refresh_items(client_id)

    def _delete_client(self, client_id):
        dlg = QMessageBox(self)
        dlg.setWindowFlags(dlg.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        dlg.setWindowTitle("Delete Client?")
        dlg.setText("Delete this client and ALL its bookmark data?\nThis cannot be undone.")
        dlg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if dlg.exec() == QMessageBox.StandardButton.Yes:
            db.delete_bookmark_client(client_id)
            if self._selected_client_id == client_id:
                self._selected_client_id = None
                self.items_list.clear()
                self.items_section_lbl.setText("SELECT A CLIENT ABOVE")
                self.add_item_btn.setEnabled(False)
            self._refresh_clients()

    def _save_client_order(self, ordered_ids):
        for i, cid in enumerate(ordered_ids):
            db.update_bookmark_client(cid, sort_order=i)
        self._refresh_clients()

    # ── Items ─────────────────────────────────────────────────────────────────

    def _refresh_items(self, client_id):
        self.items_list.clear()
        clients = db.get_bookmark_clients()
        client  = next((c for c in clients if c['id'] == client_id), None)
        self.items_section_lbl.setText(
            f"DATA \u2014 {client['name'].upper()}" if client else "SELECT A CLIENT ABOVE"
        )
        self.add_item_btn.setEnabled(True)

        for itm in db.get_bookmark_items(client_id):
            li = QListWidgetItem()
            li.setData(Qt.ItemDataRole.UserRole, itm['id'])
            widget = ItemRowWidget(itm)
            widget.opened.connect(self._open_item)
            widget.pin_toggled.connect(self._toggle_item_pin)
            widget.deleted.connect(self._delete_item)
            li.setSizeHint(QSize(self.items_list.width() - 4, 58))
            self.items_list.addItem(li)
            self.items_list.setItemWidget(li, widget)

    def _add_item(self):
        if self._selected_client_id is None:
            return
        clients = db.get_bookmark_clients()
        if not clients:
            return
        dlg = AddItemDialog(clients, self._selected_client_id, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            db.add_bookmark_item(data['client_id'], data['data_name'],
                                 data['data_type'], data['content'])
            self._selected_client_id = data['client_id']
            self._refresh_clients()
            self._refresh_items(self._selected_client_id)

    def _delete_item(self, item_id):
        db.delete_bookmark_item(item_id)
        if self._selected_client_id is not None:
            self._refresh_items(self._selected_client_id)

    def _toggle_item_pin(self, item_id):
        if self._selected_client_id is None:
            return
        items = db.get_bookmark_items(self._selected_client_id)
        cur = next((it for it in items if it['id'] == item_id), None)
        if cur:
            db.update_bookmark_item(item_id, is_pinned=0 if cur['is_pinned'] else 1)
            self._refresh_items(self._selected_client_id)

    def _save_item_order(self, ordered_ids):
        for i, iid in enumerate(ordered_ids):
            db.update_bookmark_item(iid, sort_order=i)
        if self._selected_client_id is not None:
            self._refresh_items(self._selected_client_id)

    def _open_item(self, item_id):
        item = next(
            (it for it in db.get_bookmark_items(self._selected_client_id) if it['id'] == item_id),
            None
        ) if self._selected_client_id else None
        if not item:
            return
        if item['data_type'] == 'Link':
            browsers = _detect_browsers()
            if len(browsers) > 1:
                BrowserPickerDialog(item['content'], browsers, self).exec()
            else:
                webbrowser.open(item['content'])
        elif item['data_type'] == 'Folder':
            if os.path.exists(item['content']):
                if sys.platform == 'win32':
                    subprocess.Popen(['explorer', os.path.normpath(item['content'])])
                else:
                    subprocess.run(['xdg-open', item['content']])
            else:
                QMessageBox.warning(self, "Not Found", f"Folder not found:\n{item['content']}")
        else:
            if os.path.exists(item['content']):
                if sys.platform == 'win32':
                    os.startfile(item['content'])
                else:
                    subprocess.run(['xdg-open', item['content']])
            else:
                QMessageBox.warning(self, "Not Found", f"File not found:\n{item['content']}")


# ── Helpers ───────────────────────────────────────────────────────────────────

def _detect_browsers():
    if sys.platform != 'win32':
        return []
    user = os.environ.get('USERNAME', '')
    candidates = [
        ("Google Chrome",   r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
        ("Google Chrome",   r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
        ("Mozilla Firefox", r"C:\Program Files\Mozilla Firefox\firefox.exe"),
        ("Mozilla Firefox", r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe"),
        ("Microsoft Edge",  r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
        ("Microsoft Edge",  r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
        ("Brave",           r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"),
        ("Opera",           rf"C:\Users\{user}\AppData\Local\Programs\Opera\opera.exe"),
    ]
    found, seen = [], set()
    for name, path in candidates:
        if name not in seen and os.path.exists(path):
            found.append((name, path))
            seen.add(name)
    return found
