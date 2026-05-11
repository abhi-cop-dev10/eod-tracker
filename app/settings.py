from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QCheckBox, QComboBox,
    QRadioButton, QButtonGroup, QGroupBox, QFileDialog,
    QSpinBox, QTabWidget, QFrame, QApplication, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QIcon

from app.database import get_setting, set_setting
from app.icon_utils import app_icon

INTERVAL_OPTIONS = [
    ("30 seconds (demo)", 30),
    ("2 minutes",  120),
    ("5 minutes",  300),
    ("10 minutes", 600),
    ("15 minutes", 900),
    ("30 minutes", 1800),
    ("1 hour",     3600),
]


class SettingsWindow(QWidget):
    settings_saved = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Settings — EOD Tracker")
        self.setWindowIcon(app_icon())
        self.setMinimumSize(540, 620)
        # Always on top of panel and other app windows
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self._setup_ui()
        self._load_settings()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title = QLabel("Settings")
        title.setObjectName("sectionLabel")
        title.setStyleSheet("font-size:18px;font-weight:bold;")
        layout.addWidget(title)

        tabs = QTabWidget()
        tabs.addTab(self._general_tab(),    "General")
        tabs.addTab(self._gorilla_tab(),    "Gorilla")
        tabs.addTab(self._bookmarks_tab(),  "Bookmarks")
        tabs.addTab(self._theme_tab(),      "Theme")
        tabs.addTab(self._about_tab(),      "About")
        layout.addWidget(tabs, 1)

        bottom = QHBoxLayout()
        bottom.addStretch()
        save_btn = QPushButton("Save Settings")
        save_btn.setObjectName("saveBtn")
        save_btn.setMinimumWidth(140)
        save_btn.clicked.connect(self._save)
        bottom.addWidget(save_btn)
        layout.addLayout(bottom)

    # ── Tabs ──────────────────────────────────────────────────────────────────

    def _general_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(12, 12, 12, 12)
        l.setSpacing(12)

        emp = QGroupBox("Employee")
        g   = QGridLayout(emp)
        g.setSpacing(8)
        g.addWidget(QLabel("Your Name:"), 0, 0)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g. John Smith")
        g.addWidget(self.name_input, 0, 1)
        g.setColumnStretch(1, 1)
        l.addWidget(emp)

        sys_grp = QGroupBox("System")
        sv = QVBoxLayout(sys_grp)
        self.startup_cb = QCheckBox("Run at Windows startup")
        sv.addWidget(self.startup_cb)
        l.addWidget(sys_grp)

        xlsx = QGroupBox("Excel Template")
        xg   = QGridLayout(xlsx)
        xg.setSpacing(8)
        xg.addWidget(QLabel("Template File:"), 0, 0)
        self.template_input = QLineEdit()
        self.template_input.setPlaceholderText("Path to .xlsx template (leave blank for auto)")
        xg.addWidget(self.template_input, 0, 1)
        browse = QPushButton("Browse")
        browse.clicked.connect(self._browse_template)
        xg.addWidget(browse, 0, 2)
        xg.addWidget(QLabel("Data Start Row:"), 1, 0)
        self.data_row_spin = QSpinBox()
        self.data_row_spin.setMinimum(1)
        self.data_row_spin.setMaximum(20)
        xg.addWidget(self.data_row_spin, 1, 1)
        xg.setColumnStretch(1, 1)
        l.addWidget(xlsx)

        col_grp = QGroupBox("Column Mapping (Excel column letter per field)")
        cg = QGridLayout(col_grp)
        cg.setSpacing(6)
        self._col_inputs = {}
        fields = [
            ("task_name",   "Task Name",    "A"),
            ("eod_status",  "Status",       "B"),
            ("client_name", "Client",       "C"),
            ("start_time",  "Start Time",   "D"),
            ("end_time",    "End Time",     "E"),
            ("duration",    "Duration",     "F"),
            ("assigned_to", "Assigned To",  "G"),
            ("assigned_by", "Assigned By",  "H"),
            ("what_done",   "What Done",    "I"),
        ]
        for row, (key, label, default) in enumerate(fields):
            cg.addWidget(QLabel(f"{label}:"), row, 0)
            inp = QLineEdit()
            inp.setMaximumWidth(55)
            inp.setMaxLength(3)
            inp.setPlaceholderText(default)
            cg.addWidget(inp, row, 1)
            cg.addWidget(QLabel(f"(default: {default})"), row, 2)
            self._col_inputs[key] = inp
        l.addWidget(col_grp)

        l.addStretch()
        return w

    def _gorilla_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(12, 12, 12, 12)
        l.setSpacing(12)

        eg = QGroupBox("Gorilla Reminders")
        ev = QVBoxLayout(eg)
        self.gorilla_enabled_cb = QCheckBox("Enable Gorilla Reminders")
        ev.addWidget(self.gorilla_enabled_cb)
        l.addWidget(eg)

        ig = QGroupBox("Interval Type")
        iv = QVBoxLayout(ig)
        self._interval_grp = QButtonGroup(self)
        self.fixed_radio  = QRadioButton("Fixed Interval")
        self.random_radio = QRadioButton("Random Interval")
        self._interval_grp.addButton(self.fixed_radio,  0)
        self._interval_grp.addButton(self.random_radio, 1)
        self.fixed_radio.setChecked(True)
        iv.addWidget(self.fixed_radio)
        iv.addWidget(self.random_radio)
        l.addWidget(ig)

        fg = QGroupBox("Fixed Interval")
        fh = QHBoxLayout(fg)
        fh.addWidget(QLabel("Every:"))
        self.fixed_combo = QComboBox()
        for label, _ in INTERVAL_OPTIONS:
            self.fixed_combo.addItem(label)
        fh.addWidget(self.fixed_combo)
        fh.addStretch()
        l.addWidget(fg)

        rg = QGroupBox("Random Interval Range")
        rh = QHBoxLayout(rg)
        rh.addWidget(QLabel("Between:"))
        self.rand_min_combo = QComboBox()
        self.rand_max_combo = QComboBox()
        for label, _ in INTERVAL_OPTIONS:
            self.rand_min_combo.addItem(label)
            self.rand_max_combo.addItem(label)
        self.rand_min_combo.setCurrentIndex(1)
        self.rand_max_combo.setCurrentIndex(4)
        rh.addWidget(self.rand_min_combo)
        rh.addWidget(QLabel("and"))
        rh.addWidget(self.rand_max_combo)
        rh.addStretch()
        l.addWidget(rg)

        mg = QGroupBox("Gorilla Message Heading")
        mh = QHBoxLayout(mg)
        mh.addWidget(QLabel("Message:"))
        self.gorilla_msg_input = QLineEdit()
        self.gorilla_msg_input.setPlaceholderText("What are you doing?")
        mh.addWidget(self.gorilla_msg_input)
        l.addWidget(mg)

        preview_btn = QPushButton("Preview Gorilla Now")
        preview_btn.setObjectName("previewBtn")
        preview_btn.clicked.connect(self._preview_gorilla)
        l.addWidget(preview_btn)

        l.addStretch()
        return w

    def _bookmarks_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(12, 12, 12, 12)
        l.setSpacing(12)

        enable_grp = QGroupBox("Client Bookmarks")
        ev = QVBoxLayout(enable_grp)
        self.bookmarks_enabled_cb = QCheckBox("Enable Client Bookmarks")
        ev.addWidget(self.bookmarks_enabled_cb)

        desc = QLabel(
            "When enabled, a bookmark button (\U0001f516) appears on the floating side button.\n\n"
            "Click it to manage clients and store important links, files, PDFs, images, "
            "and other resources per client.\n\n"
            "Each item can be opened directly — links open in your chosen browser, "
            "files open with your default application.\n\n"
            "Items and clients can be dragged to reorder or pinned to the top."
        )
        desc.setObjectName("smallLabel")
        desc.setWordWrap(True)
        ev.addWidget(desc)
        l.addWidget(enable_grp)

        l.addStretch()
        return w

    def _theme_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(12, 12, 12, 12)
        l.setSpacing(12)

        tg = QGroupBox("Application Theme")
        tv = QVBoxLayout(tg)

        self._theme_grp = QButtonGroup(self)
        self.dark_radio  = QRadioButton("Dark Theme  (Deep Navy — default)")
        self.light_radio = QRadioButton("Light Theme (Clean White)")
        self._theme_grp.addButton(self.dark_radio,  0)
        self._theme_grp.addButton(self.light_radio, 1)
        self.dark_radio.setChecked(True)

        tv.addWidget(self.dark_radio)
        tv.addWidget(self.light_radio)

        note = QLabel(
            "Theme is applied immediately when you click Save Settings."
        )
        note.setObjectName("smallLabel")
        note.setWordWrap(True)
        tv.addWidget(note)
        l.addWidget(tg)
        l.addStretch()
        return w

    def _about_tab(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(12, 12, 12, 12)
        l.setSpacing(12)

        info_grp = QGroupBox("Application")
        ig = QGridLayout(info_grp)
        ig.setSpacing(8)
        for row, (lbl, val) in enumerate([
            ("App Name:",    "EOD Tracker"),
            ("Version:",     "1.0.0"),
            ("Organisation:","CodeClouds Dev"),
            ("Purpose:",     "Daily task tracker with Excel EOD export"),
        ]):
            ig.addWidget(QLabel(lbl), row, 0)
            v = QLabel(val)
            v.setStyleSheet("font-weight: bold;")
            ig.addWidget(v, row, 1)
        ig.setColumnStretch(1, 1)
        l.addWidget(info_grp)

        dev_grp = QGroupBox("Developer")
        dg = QGridLayout(dev_grp)
        dg.setSpacing(8)
        for row, (lbl, val) in enumerate([
            ("Developed by:", "Abhinay Kumar"),
            ("Community:",    "CodeClouds Dev Team"),
            ("Type:",         "Internal Organisation Tool"),
        ]):
            dg.addWidget(QLabel(lbl), row, 0)
            v = QLabel(val)
            v.setStyleSheet("font-weight: bold;")
            dg.addWidget(v, row, 1)
        dg.setColumnStretch(1, 1)
        l.addWidget(dev_grp)

        footer = QLabel("All data stored locally. No internet required.")
        footer.setObjectName("smallLabel")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l.addWidget(footer)
        l.addStretch()
        return w

    # ── Load / Save ───────────────────────────────────────────────────────────

    def _load_settings(self):
        from app.startup import get_startup_enabled
        self.startup_cb.setChecked(get_startup_enabled())
        self.name_input.setText(get_setting('employee_name', ''))
        self.template_input.setText(get_setting('excel_template_path', ''))
        self.data_row_spin.setValue(int(get_setting('data_start_row', '2')))

        from app.excel_export import COLUMN_MAP
        for key, inp in self._col_inputs.items():
            saved = get_setting(f'col_map_{key}', '')
            inp.setText(saved if saved else COLUMN_MAP.get(key, ''))

        self.gorilla_enabled_cb.setChecked(
            get_setting('gorilla_enabled', 'false') == 'true'
        )
        self.bookmarks_enabled_cb.setChecked(
            get_setting('bookmarks_enabled', 'false') == 'true'
        )
        itype = get_setting('gorilla_interval_type', 'fixed')
        self.fixed_radio.setChecked(itype == 'fixed')
        self.random_radio.setChecked(itype == 'random')

        fs = int(get_setting('gorilla_interval_seconds', '120'))
        for i, (_, secs) in enumerate(INTERVAL_OPTIONS):
            if secs == fs:
                self.fixed_combo.setCurrentIndex(i)

        rmin = int(get_setting('gorilla_random_min', '120'))
        rmax = int(get_setting('gorilla_random_max', '300'))
        for i, (_, secs) in enumerate(INTERVAL_OPTIONS):
            if secs == rmin: self.rand_min_combo.setCurrentIndex(i)
            if secs == rmax: self.rand_max_combo.setCurrentIndex(i)

        self.gorilla_msg_input.setText(
            get_setting('gorilla_message', 'What are you doing?')
        )

        theme = get_setting('theme', 'dark')
        self.dark_radio.setChecked(theme == 'dark')
        self.light_radio.setChecked(theme == 'light')

    def _save(self):
        from app.startup import set_startup_enabled
        set_startup_enabled(self.startup_cb.isChecked())
        set_setting('employee_name',     self.name_input.text().strip())
        set_setting('excel_template_path', self.template_input.text().strip())
        set_setting('data_start_row',    str(self.data_row_spin.value()))

        import re
        _COL_RE = re.compile(r'^[A-Z]{1,3}$')
        for key, inp in self._col_inputs.items():
            val = inp.text().strip().upper()
            if val and _COL_RE.match(val):
                set_setting(f'col_map_{key}', val)

        set_setting('gorilla_enabled',
                    'true' if self.gorilla_enabled_cb.isChecked() else 'false')
        set_setting('bookmarks_enabled',
                    'true' if self.bookmarks_enabled_cb.isChecked() else 'false')
        set_setting('gorilla_interval_type',
                    'fixed' if self.fixed_radio.isChecked() else 'random')
        set_setting('gorilla_interval_seconds',
                    str(INTERVAL_OPTIONS[self.fixed_combo.currentIndex()][1]))
        set_setting('gorilla_random_min',
                    str(INTERVAL_OPTIONS[self.rand_min_combo.currentIndex()][1]))
        set_setting('gorilla_random_max',
                    str(INTERVAL_OPTIONS[self.rand_max_combo.currentIndex()][1]))
        set_setting('gorilla_message',
                    self.gorilla_msg_input.text().strip() or 'What are you doing?')

        new_theme = 'dark' if self.dark_radio.isChecked() else 'light'
        set_setting('theme', new_theme)

        # Apply theme immediately
        from app.themes import get_colors, build_stylesheet
        QApplication.instance().setStyleSheet(build_stylesheet(get_colors(new_theme)))
        self._refresh_all_widgets()

        self.settings_saved.emit()
        from app.toast import show_toast
        show_toast("Settings saved!")

    def _refresh_all_widgets(self):
        for w in QApplication.topLevelWidgets():
            w.update()

    def _browse_template(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Excel Template", str(Path.home()),
            "Excel Files (*.xlsx *.xls)"
        )
        if path:
            self.template_input.setText(path)

    def _preview_gorilla(self):
        set_setting('gorilla_message',
                    self.gorilla_msg_input.text().strip() or 'What are you doing?')
        for w in QApplication.topLevelWidgets():
            if hasattr(w, 'gorilla'):
                w.gorilla.show_gorilla()
                return
        from app.gorilla import GorillaWidget
        self._preview_g = GorillaWidget()
        self._preview_g.show_gorilla()
