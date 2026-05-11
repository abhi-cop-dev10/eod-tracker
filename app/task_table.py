from datetime import datetime, date as dt_date

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QAbstractItemView, QMessageBox, QHeaderView
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QBrush

from app.database import (
    get_active_tasks, get_all_tasks, update_task, delete_task, toggle_active
)


def calc_duration(start_str, end_str=None):
    try:
        start = datetime.strptime(start_str, "%H:%M")
        end   = (datetime.strptime(end_str, "%H:%M")
                 if end_str
                 else datetime.now().replace(second=0, microsecond=0))
        mins = int((end - start).total_seconds() / 60)
        if mins < 0:
            mins += 24 * 60
        h, m = divmod(mins, 60)
        if h == 0:
            return f"{m} Minute{'s' if m != 1 else ''}"
        if m == 0:
            return f"{h} Hour{'s' if h != 1 else ''}"
        return f"{h}h {m}m"
    except Exception:
        return ""


def _row_colors(row: int, status: str) -> tuple[str, str]:
    """Return (bg_hex, text_hex) for a row, respecting current theme."""
    from app.database import get_setting
    from app.themes import get_colors
    c = get_colors(get_setting('theme', 'dark'))
    if status == 'running':
        return c['row_running'], c['text_primary']
    bg = c['row_even'] if row % 2 == 0 else c['row_odd']
    return bg, c['text_primary']


class TimerPill(QPushButton):
    def __init__(self, status):
        super().__init__()
        self.setFixedSize(65, 22)
        self.set_status(status)

    def set_status(self, status):
        if status == 'running':
            self.setText("Running")
            self.setStyleSheet(
                "QPushButton{background:#4caf50;color:white;border-radius:11px;"
                "font-size:10px;font-weight:bold;border:none;}"
                "QPushButton:hover{background:#43a047;}"
            )
        elif status == 'finished':
            self.setText("Done")
            self.setStyleSheet(
                "QPushButton{background:#3a7bd5;color:white;border-radius:11px;"
                "font-size:10px;font-weight:bold;border:none;}"
                "QPushButton:hover{background:#2f6cbf;}"
            )
        else:
            self.setText("Stopped")
            self.setStyleSheet(
                "QPushButton{background:#3a3a4a;color:#aaa;border-radius:11px;"
                "font-size:10px;font-weight:bold;border:none;}"
                "QPushButton:hover{background:#555;}"
            )


MODE_ACTIVE = 'active'
MODE_MANAGE = 'manage'

# Shared inline styles for table action buttons
_BTN_START  = ("QPushButton{background:#4caf50;color:white;border-radius:5px;"
               "padding:3px 7px;font-size:11px;border:none;font-weight:bold;}"
               "QPushButton:hover{background:#43a047;}")
_BTN_FINISH = ("QPushButton{background:#e94560;color:white;border-radius:5px;"
               "padding:3px 7px;font-size:11px;border:none;font-weight:bold;}"
               "QPushButton:hover{background:#c73652;}")
_BTN_DEL    = ("QPushButton{background:#e94560;color:white;border-radius:4px;"
               "padding:2px 6px;font-size:10px;border:none;font-weight:bold;}"
               "QPushButton:hover{background:#c73652;}")
_BTN_ENABLE = ("QPushButton{background:#4caf50;color:white;border-radius:5px;"
               "padding:3px 8px;font-size:10px;border:none;font-weight:bold;}"
               "QPushButton:hover{background:#43a047;}")
_BTN_DISABLE= ("QPushButton{background:#888;color:white;border-radius:5px;"
               "padding:3px 8px;font-size:10px;border:none;font-weight:bold;}"
               "QPushButton:hover{background:#666;}")


class TaskTable(QWidget):
    def __init__(self):
        super().__init__()
        self._tasks = []
        self._mode  = MODE_ACTIVE
        self._setup_ui()

        self._live_timer = QTimer()
        self._live_timer.timeout.connect(self._update_live_durations)
        self._live_timer.start(30000)

    # ── UI ────────────────────────────────────────────────────────────────────

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        bar   = QWidget()
        bar.setStyleSheet("background: transparent;")
        bar_l = QHBoxLayout(bar)
        bar_l.setContentsMargins(0, 0, 0, 0)
        bar_l.setSpacing(6)

        self._active_tab_btn = QPushButton("Active Tasks")
        self._active_tab_btn.setObjectName("tabBtn")
        self._active_tab_btn.setCheckable(True)
        self._active_tab_btn.setChecked(True)
        self._active_tab_btn.clicked.connect(lambda: self._switch_mode(MODE_ACTIVE))

        self._manage_tab_btn = QPushButton("Manage All")
        self._manage_tab_btn.setObjectName("tabBtn")
        self._manage_tab_btn.setCheckable(True)
        self._manage_tab_btn.setChecked(False)
        self._manage_tab_btn.clicked.connect(lambda: self._switch_mode(MODE_MANAGE))

        bar_l.addWidget(self._active_tab_btn)
        bar_l.addWidget(self._manage_tab_btn)
        bar_l.addStretch()
        layout.addWidget(bar)

        self.table = QTableWidget()
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(False)
        self.table.setShowGrid(False)
        layout.addWidget(self.table)

    def _switch_mode(self, mode):
        self._mode = mode
        self._active_tab_btn.setChecked(mode == MODE_ACTIVE)
        self._manage_tab_btn.setChecked(mode == MODE_MANAGE)
        self.refresh()

    # ── Refresh ───────────────────────────────────────────────────────────────

    def refresh(self):
        if self._mode == MODE_ACTIVE:
            self._tasks = get_active_tasks()
            self._build_active_table()
        else:
            self._tasks = get_all_tasks()
            self._build_manage_table()

    def _build_active_table(self):
        # Clear everything before rebuilding to prevent stale cell widgets
        self.table.clearContents()
        self.table.setRowCount(0)
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(
            ["Timer", "Task Name", "Client", "Start", "End", "Duration", "What Done?", "Actions"]
        )
        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        # "What Done?" (col 6) stretches; all others fixed
        for i, w in enumerate([62, 125, 82, 50, 50, 58, 0, 108]):
            if i != 6:
                self.table.setColumnWidth(i, w)
        hdr.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        # Thin horizontal scrollbar if content overflows
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.table.setRowCount(len(self._tasks))
        for row, task in enumerate(self._tasks):
            self._populate_active_row(row, task)

    def _build_manage_table(self):
        self.table.clearContents()
        self.table.setRowCount(0)
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["Status", "Task Name", "Client", "Assigned To", "Assigned By", "Actions"]
        )
        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        # Task Name (col 1) stretches to fill available space
        for i, w in enumerate([58, 0, 88, 98, 98, 165]):
            if i != 1:
                self.table.setColumnWidth(i, w)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.table.setRowCount(len(self._tasks))
        for row, task in enumerate(self._tasks):
            self._populate_manage_row(row, task)

    # ── Active mode rows ──────────────────────────────────────────────────────

    def _populate_active_row(self, row, task):
        status     = task['timer_status']
        bg_hex, _fg = _row_colors(row, status)

        # Timer pill
        pill = TimerPill(status)
        pill.clicked.connect(
            lambda _=False, tid=task['id'], s=status: self._toggle_timer(tid, s)
        )
        self.table.setCellWidget(row, 0, _center(pill, bg_hex))

        # Text cells (cols 1-6)
        from app.database import get_setting
        from app.themes import get_colors
        c = get_colors(get_setting('theme', 'dark'))
        primary   = QBrush(QColor(c['text_primary']))
        secondary = QBrush(QColor(c['text_secondary']))
        bg        = QBrush(QColor(bg_hex))

        texts  = [
            task['task_name'],
            task['client_name'],
            task['start_time'] or '',
            task['end_time']   or '',
            self._live_duration(task),
            task['what_done']  or '',
        ]
        fgs = [primary, primary, secondary, secondary, secondary, secondary]
        for col, (text, fg_brush) in enumerate(zip(texts, fgs), start=1):
            item = QTableWidgetItem(text)
            item.setToolTip(text)
            item.setForeground(fg_brush)
            item.setBackground(bg)
            self.table.setItem(row, col, item)

        # Actions (col 7)
        self.table.setCellWidget(row, 7, self._make_active_actions(task, bg_hex))
        self.table.setRowHeight(row, 42)

    def _make_active_actions(self, task, bg_hex='#1a1a2e'):
        w = QWidget()
        w.setStyleSheet(f"background: {bg_hex};")
        l = QHBoxLayout(w)
        l.setContentsMargins(3, 3, 3, 3)
        l.setSpacing(4)

        status  = task['timer_status']
        task_id = task['id']

        if status == 'inactive':
            btn = QPushButton("Start")
            btn.setStyleSheet(_BTN_START)
            btn.clicked.connect(lambda: self._start_task(task_id))
            l.addWidget(btn)
        elif status == 'running':
            btn = QPushButton("Finish")
            btn.setStyleSheet(_BTN_FINISH)
            btn.clicked.connect(lambda: self._finish_task(task_id, task['start_time']))
            l.addWidget(btn)
        else:
            lbl = QLabel("Done")
            lbl.setStyleSheet("color:#4caf50;font-size:11px;font-weight:bold;background:transparent;")
            l.addWidget(lbl)

        del_btn = QPushButton("Del")
        del_btn.setStyleSheet(_BTN_DEL)
        del_btn.clicked.connect(lambda: self._confirm_delete(task_id, task['task_name']))
        l.addWidget(del_btn)
        return w

    # ── Manage mode rows ──────────────────────────────────────────────────────

    def _populate_manage_row(self, row, task):
        from app.database import get_setting
        from app.themes import get_colors
        c         = get_colors(get_setting('theme', 'dark'))
        is_active = bool(task['is_active'])
        bg_hex    = c['row_even'] if row % 2 == 0 else c['row_odd']
        bg        = QBrush(QColor(bg_hex))
        fg        = QBrush(QColor(c['text_primary'] if is_active else c['text_secondary']))

        # Col 0: Status label
        lbl = QLabel("Active" if is_active else "Inactive")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet(
            f"color:{'#4caf50' if is_active else '#aaa'};"
            f"font-size:11px;font-weight:bold;background:{bg_hex};"
        )
        self.table.setCellWidget(row, 0, _center(lbl, bg_hex))

        # Cols 1-4: text fields
        for col, field in enumerate(
            ['task_name', 'client_name', 'assigned_to', 'assigned_by'], start=1
        ):
            item = QTableWidgetItem(task[field])
            item.setToolTip(task[field])
            item.setForeground(fg)
            item.setBackground(bg)
            self.table.setItem(row, col, item)

        # Col 5: actions (Enable/Disable + Delete)
        actions = QWidget()
        actions.setStyleSheet(f"background: {bg_hex};")
        al = QHBoxLayout(actions)
        al.setContentsMargins(3, 3, 3, 3)
        al.setSpacing(4)

        toggle_btn = QPushButton("Disable" if is_active else "Enable")
        toggle_btn.setStyleSheet(_BTN_DISABLE if is_active else _BTN_ENABLE)
        toggle_btn.clicked.connect(
            lambda _=False, tid=task['id'], a=is_active: self._toggle_active(tid, a)
        )
        al.addWidget(toggle_btn)

        del_btn = QPushButton("Del")
        del_btn.setStyleSheet(_BTN_DEL)
        del_btn.clicked.connect(
            lambda _=False, tid=task['id'], tn=task['task_name']:
                self._confirm_delete(tid, tn)
        )
        al.addWidget(del_btn)

        self.table.setCellWidget(row, 5, actions)
        self.table.setRowHeight(row, 40)

    # ── Actions ───────────────────────────────────────────────────────────────

    def _toggle_timer(self, task_id, current_status):
        task = next((t for t in self._tasks if t['id'] == task_id), None)
        if not task:
            return
        if current_status == 'inactive':
            self._start_task(task_id)
        elif current_status == 'running':
            self._finish_task(task_id, task['start_time'])

    def _start_task(self, task_id):
        now = datetime.now().strftime("%H:%M")
        update_task(
            task_id,
            timer_status='running',
            start_time=now,
            eod_status='In Progress',
            last_session_date=str(dt_date.today())
        )
        self.refresh()

    def _finish_task(self, task_id, start_time):
        now      = datetime.now().strftime("%H:%M")
        duration = calc_duration(start_time, now) if start_time else ""
        update_task(task_id, timer_status='finished', end_time=now, duration=duration)
        self.refresh()

    def _toggle_active(self, task_id, currently_active):
        toggle_active(task_id, currently_active)
        self.refresh()

    def _confirm_delete(self, task_id, task_name):
        dlg = QMessageBox()
        dlg.setWindowTitle("Delete Task?")
        dlg.setText(f"Delete '{task_name}'?\n\nThis permanently removes the task.")
        dlg.setStandardButtons(
            QMessageBox.StandardButton.Cancel | QMessageBox.StandardButton.Ok
        )
        dlg.button(QMessageBox.StandardButton.Ok).setText("Delete")
        # Always show above other windows
        dlg.setWindowFlags(
            dlg.windowFlags() | Qt.WindowType.WindowStaysOnTopHint
        )
        if dlg.exec() == QMessageBox.StandardButton.Ok:
            delete_task(task_id)
            self.refresh()

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _live_duration(self, task):
        if task['timer_status'] == 'running' and task['start_time']:
            return calc_duration(task['start_time'])
        return task['duration'] or ''

    def _update_live_durations(self):
        if self._mode != MODE_ACTIVE:
            return
        for row, task in enumerate(self._tasks):
            if task['timer_status'] == 'running' and task['start_time']:
                item = self.table.item(row, 5)
                if item:
                    item.setText(calc_duration(task['start_time']))

    def get_running_task(self):
        return next(
            (t for t in self._tasks if t['timer_status'] == 'running'), None
        )


def _center(widget: QWidget, bg: str = '#1a1a2e') -> QWidget:
    """Wrap a widget in a row-colored centered container for table cells.
    Using the actual row background (not transparent) prevents the black
    rendering artifact on Windows."""
    c = QWidget()
    c.setStyleSheet(f"background: {bg};")
    l = QHBoxLayout(c)
    l.setContentsMargins(3, 3, 3, 3)
    l.addWidget(widget)
    l.setAlignment(Qt.AlignmentFlag.AlignCenter)
    return c
