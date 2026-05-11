from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QApplication
from PyQt6.QtCore import QTimer

from app.icon_utils import app_icon


class TrayApp:
    def __init__(self, app):
        self.app   = app
        self.panel = None
        self._settings_win = None

        self.tray = QSystemTrayIcon(app_icon(), app)
        self.tray.setToolTip("EOD Tracker — Click to open")

        menu = QMenu()
        open_act     = menu.addAction("Open Panel")
        menu.addSeparator()
        settings_act = menu.addAction("Settings")
        menu.addSeparator()
        exit_act     = menu.addAction("Exit")

        open_act.triggered.connect(self.show_panel)
        settings_act.triggered.connect(self.show_settings)
        exit_act.triggered.connect(QApplication.quit)

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._on_activated)
        self.tray.show()

        from app.floating_panel import FloatingPanel
        self.panel = FloatingPanel()

        QTimer.singleShot(800, self._startup_notification)

    def _startup_notification(self):
        self.tray.showMessage(
            "EOD Tracker",
            "Running in background. Click the < button on the screen edge to open.",
            QSystemTrayIcon.MessageIcon.Information,
            3000
        )

    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_panel()

    def show_panel(self):
        if self.panel:
            self.panel.open_panel()

    def show_settings(self):
        from app.settings import SettingsWindow
        if not self._settings_win or not self._settings_win.isVisible():
            self._settings_win = SettingsWindow()
            self._settings_win.show()
        else:
            self._settings_win.raise_()
            self._settings_win.activateWindow()
