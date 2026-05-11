from PyQt6.QtWidgets import (
    QWidget, QGridLayout, QPushButton, QLabel, QLineEdit
)
from PyQt6.QtCore import pyqtSignal
from app.database import add_task, get_setting


class TaskForm(QWidget):
    task_added = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setObjectName("formCard")   # global theme targets QWidget#formCard
        self._setup_ui()

    def _setup_ui(self):
        layout = QGridLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        layout.addWidget(QLabel("Task Name:"), 0, 0)
        self.task_input = QLineEdit()
        self.task_input.setPlaceholderText("e.g. Login Page Development")
        layout.addWidget(self.task_input, 0, 1)

        layout.addWidget(QLabel("Client:"), 1, 0)
        self.client_input = QLineEdit()
        self.client_input.setPlaceholderText("e.g. ATB Media")
        layout.addWidget(self.client_input, 1, 1)

        layout.addWidget(QLabel("Assigned To:"), 2, 0)
        self.assigned_to_input = QLineEdit()
        self.assigned_to_input.setPlaceholderText("Your name")
        layout.addWidget(self.assigned_to_input, 2, 1)

        layout.addWidget(QLabel("Assigned By:"), 3, 0)
        self.assigned_by_input = QLineEdit()
        self.assigned_by_input.setPlaceholderText("e.g. Abhijeet Da")
        layout.addWidget(self.assigned_by_input, 3, 1)

        add_btn = QPushButton("+ Add Task")
        add_btn.setObjectName("addBtn")
        add_btn.clicked.connect(self._add_task)
        layout.addWidget(add_btn, 4, 0, 1, 2)

        layout.setColumnStretch(1, 1)
        self.refresh_employee_name()

    def refresh_employee_name(self):
        name = get_setting('employee_name', '')
        self.assigned_to_input.setText(name)

    def _set_error(self, field, has_error: bool):
        """Toggle error border via dynamic property (no color override)."""
        field.setProperty("hasError", "true" if has_error else "false")
        field.style().unpolish(field)
        field.style().polish(field)

    def _add_task(self):
        task_name   = self.task_input.text().strip()
        client      = self.client_input.text().strip()
        assigned_to = self.assigned_to_input.text().strip()
        assigned_by = self.assigned_by_input.text().strip()

        valid = True
        for field, value in [
            (self.task_input,       task_name),
            (self.client_input,     client),
            (self.assigned_to_input, assigned_to),
            (self.assigned_by_input, assigned_by),
        ]:
            has_error = not bool(value)
            self._set_error(field, has_error)
            if has_error:
                valid = False

        if not valid:
            return

        add_task(task_name, client, assigned_to, assigned_by)
        self.task_input.clear()
        self.client_input.clear()
        self.assigned_by_input.clear()
        # Clear error states
        for field in (self.task_input, self.client_input,
                      self.assigned_to_input, self.assigned_by_input):
            self._set_error(field, False)
        self.task_added.emit()
