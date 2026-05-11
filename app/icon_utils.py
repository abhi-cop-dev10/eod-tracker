"""Generates the app icon programmatically if no file asset is present."""
from pathlib import Path
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QBrush, QPen, QFont
from PyQt6.QtCore import Qt

_check_png_cache = None


def create_check_png() -> str:
    """Generate a white checkmark PNG once, return its path for use in CSS."""
    global _check_png_cache
    if _check_png_cache and Path(_check_png_cache).exists():
        return _check_png_cache.replace("\\", "/")

    from app.paths import data_dir
    path = data_dir() / "check.png"
    if not path.exists():
        pm = QPixmap(14, 14)
        pm.fill(Qt.GlobalColor.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(QColor("white"))
        pen.setWidthF(2.5)
        p.setPen(pen)
        # Draw ✓ checkmark
        p.drawLine(2, 7, 5, 11)
        p.drawLine(5, 11, 12, 3)
        p.end()
        path.parent.mkdir(parents=True, exist_ok=True)
        pm.save(str(path))

    _check_png_cache = str(path)
    return _check_png_cache.replace("\\", "/")


def _draw_app_icon(size=64):
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Background circle
    p.setBrush(QBrush(QColor("#e94560")))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(2, 2, size - 4, size - 4)

    # "E" text
    p.setPen(QPen(QColor("white")))
    font = QFont("Segoe UI", int(size * 0.38), QFont.Weight.Bold)
    p.setFont(font)
    p.drawText(pm.rect(), Qt.AlignmentFlag.AlignCenter, "E")

    p.end()
    return pm


def app_icon() -> QIcon:
    """Return QIcon — from file if it exists, otherwise generated."""
    from app.paths import assets_dir
    path = assets_dir() / "tray_icon.png"
    if path.exists():
        return QIcon(str(path))
    return QIcon(_draw_app_icon(64))


def app_pixmap(size=32) -> QPixmap:
    from app.paths import assets_dir
    path = assets_dir() / "tray_icon.png"
    if path.exists():
        return QPixmap(str(path)).scaled(
            size, size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
    return _draw_app_icon(size)
