DARK = {
    'bg_deep':      '#1a1a2e',
    'bg_mid':       '#16213e',
    'bg_light':     '#0f3460',
    'accent':       '#e94560',
    'accent_hover': '#c73652',
    'accent_green': '#4caf50',
    'accent_blue':  '#3a7bd5',
    'text_primary': '#eaeaea',
    'text_secondary': '#a0aec0',
    'border':       '#2d3748',
    'row_even':     '#0f3460',
    'row_odd':      '#16213e',
    'row_running':  '#0d2b1e',
    'name':         'dark',
}

LIGHT = {
    'bg_deep':      '#f0f4f8',
    'bg_mid':       '#ffffff',
    'bg_light':     '#dde6f0',
    'accent':       '#e94560',
    'accent_hover': '#c73652',
    'accent_green': '#4caf50',
    'accent_blue':  '#3a7bd5',
    'text_primary': '#1a1a2e',
    'text_secondary': '#5a6474',
    'border':       '#b0bec5',
    'row_even':     '#dde6f0',
    'row_odd':      '#f0f4f8',
    'row_running':  '#c8e6c9',
    'name':         'light',
}


def get_colors(name='dark'):
    return DARK if name == 'dark' else LIGHT


def build_stylesheet(c):
    from app.icon_utils import create_check_png
    check_path = create_check_png()
    return f"""
QWidget {{
    background-color: {c['bg_deep']};
    color: {c['text_primary']};
    font-family: "Segoe UI", Arial;
    font-size: 13px;
}}
QDialog, QMessageBox {{
    background-color: {c['bg_mid']};
}}
QLabel {{
    background: transparent;
    color: {c['text_primary']};
}}
QLabel#title {{
    font-size: 15px; font-weight: bold;
}}
QLabel#heading {{
    font-size: 14px; font-weight: bold;
}}
QLabel#smallLabel {{
    color: {c['text_secondary']};
    font-size: 11px;
}}
QLabel#sectionLabel {{
    color: {c['accent']};
    font-weight: bold;
}}
QWidget#panel {{
    background-color: {c['bg_deep']};
    border-left: 2px solid {c['accent']};
}}
QWidget#header {{
    background-color: {c['bg_mid']};
    border-bottom: 1px solid {c['border']};
}}
QWidget#content {{ background-color: {c['bg_deep']}; }}
QWidget#bottomBar {{ background-color: {c['bg_mid']}; }}
QWidget#formCard {{
    background-color: {c['bg_light']};
    border: 1px solid {c['accent']};
    border-radius: 8px;
}}
QWidget#card {{
    background-color: {c['bg_mid']};
    border: 2px solid {c['accent']};
    border-radius: 12px;
}}
QLineEdit, QSpinBox {{
    background-color: {c['bg_light']};
    color: {c['text_primary']};
    border: 1px solid {c['border']};
    border-radius: 6px;
    padding: 6px 8px;
    selection-background-color: {c['accent']};
    selection-color: white;
}}
QLineEdit:focus, QSpinBox:focus {{
    border: 1px solid {c['accent']};
}}
QTextEdit {{
    background-color: {c['bg_light']};
    color: {c['text_primary']};
    border: 1px solid {c['border']};
    border-radius: 6px;
    padding: 4px;
    selection-background-color: {c['accent']};
}}
QTextEdit:focus {{ border: 1px solid {c['accent']}; }}
QComboBox {{
    background-color: {c['bg_light']};
    color: {c['text_primary']};
    border: 1px solid {c['border']};
    border-radius: 6px;
    padding: 4px 8px;
}}
QComboBox:focus {{ border: 1px solid {c['accent']}; }}
QComboBox::drop-down {{ border: none; width: 20px; }}
QComboBox QAbstractItemView {{
    background-color: {c['bg_light']};
    color: {c['text_primary']};
    selection-background-color: {c['accent']};
    selection-color: white;
    border: 1px solid {c['accent']};
}}
QPushButton {{
    background-color: {c['bg_light']};
    color: {c['text_primary']};
    border: 1px solid {c['border']};
    border-radius: 6px;
    padding: 6px 14px;
}}
QPushButton:hover {{
    border-color: {c['accent']};
    color: {c['accent']};
}}
QPushButton#closeBtn {{
    background: transparent; border: none;
    color: {c['text_secondary']};
    font-size: 18px; font-weight: bold;
}}
QPushButton#closeBtn:hover {{
    color: {c['accent']}; background: transparent;
}}
QPushButton#settingsBtn {{
    background-color: {c['bg_light']};
    border: 1px solid {c['accent']};
    padding: 4px 10px; font-size: 12px;
}}
QPushButton#settingsBtn:hover {{
    background-color: {c['accent']}; color: white; border-color: {c['accent']};
}}
QPushButton#manageBtn {{
    background-color: {c['bg_light']};
    border: 1px solid {c['border']};
    padding: 4px 10px; font-size: 12px;
}}
QPushButton#manageBtn:hover {{
    border-color: {c['accent']}; color: {c['accent']};
}}
QPushButton#addBtn {{
    background-color: {c['accent']}; color: white;
    border: none; font-weight: bold;
    padding: 8px 16px;
}}
QPushButton#addBtn:hover {{ background-color: {c['accent_hover']}; color: white; }}
QPushButton#exportBtn {{
    background-color: {c['accent']}; color: white;
    border: none; font-weight: bold;
    padding: 10px; font-size: 13px;
}}
QPushButton#exportBtn:hover {{ background-color: {c['accent_hover']}; color: white; }}
QPushButton#resetBtn {{
    background-color: {c['bg_light']};
    color: {c['text_primary']};
    border: 1px solid {c['border']};
    padding: 10px; font-size: 12px;
}}
QPushButton#resetBtn:hover {{
    background-color: #e65c00; color: white; border-color: #e65c00;
}}
QPushButton#saveBtn {{
    background-color: {c['accent']}; color: white;
    border: none; font-weight: bold; padding: 8px 24px;
}}
QPushButton#saveBtn:hover {{ background-color: {c['accent_hover']}; color: white; }}
QPushButton#previewBtn {{
    background-color: {c['accent_green']}; color: white; border: none;
}}
QPushButton#previewBtn:hover {{ background-color: #43a047; color: white; }}
QCheckBox {{
    color: {c['text_primary']}; spacing: 8px;
}}
QCheckBox::indicator {{
    width: 18px; height: 18px;
    border: 2px solid {c['accent']};
    border-radius: 4px;
    background: {c['bg_light']};
}}
QCheckBox::indicator:checked {{
    background-color: {c['accent']};
    border: 2px solid {c['accent']};
    image: url({check_path});
}}
QCheckBox::indicator:unchecked {{
    background-color: {c['bg_light']};
}}
QRadioButton {{
    color: {c['text_primary']}; spacing: 8px;
}}
QRadioButton::indicator {{
    width: 16px; height: 16px;
    border: 2px solid {c['accent']};
    border-radius: 8px;
    background: {c['bg_light']};
}}
QRadioButton::indicator:checked {{
    background-color: {c['accent']};
    border: 2px solid {c['accent']};
}}
QGroupBox {{
    background-color: {c['bg_mid']};
    border: 1px solid {c['border']};
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 8px;
    color: {c['text_primary']};
    font-size: 13px;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 10px; padding: 0 6px;
    color: {c['accent']}; font-weight: bold;
}}
QTabWidget::pane {{
    background: {c['bg_deep']};
    border: 1px solid {c['border']};
    border-radius: 6px;
}}
QTabBar::tab {{
    background: {c['bg_mid']}; color: {c['text_secondary']};
    padding: 8px 16px; border: none;
    border-bottom: 2px solid transparent;
}}
QTabBar::tab:selected {{
    color: {c['text_primary']};
    border-bottom: 2px solid {c['accent']};
    background: {c['bg_deep']};
}}
QTableWidget {{
    background-color: {c['bg_deep']};
    color: {c['text_primary']};
    border: none; gridline-color: transparent; outline: none;
}}
QTableWidget::item {{
    padding: 4px 6px;
    border-bottom: 1px solid {c['border']};
}}
QTableWidget::item:selected {{
    background-color: {c['bg_light']};
    color: {c['text_primary']};
}}
QHeaderView::section {{
    background-color: {c['accent']};
    color: white; font-weight: bold; font-size: 11px;
    padding: 6px 4px; border: none;
}}
QScrollBar:vertical {{
    background: {c['bg_deep']}; width: 8px; border-radius: 4px;
}}
QScrollBar::handle:vertical {{
    background: {c['accent']}; border-radius: 4px; min-height: 20px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
QScrollBar:horizontal {{
    background: {c['bg_deep']}; height: 6px; border-radius: 3px;
}}
QScrollBar::handle:horizontal {{
    background: {c['accent']}; border-radius: 3px; min-width: 20px;
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0px; }}
QScrollArea {{ border: none; background: transparent; }}
QToolTip {{
    background-color: {c['bg_mid']}; color: {c['text_primary']};
    border: 1px solid {c['accent']}; padding: 4px; border-radius: 4px;
}}
QMessageBox QLabel {{ color: {c['text_primary']}; background: transparent; }}
QLineEdit[hasError="true"] {{
    border: 2px solid {c['accent']};
}}
QPushButton#tabBtn {{
    background-color: {c['bg_mid']};
    color: {c['text_secondary']};
    border: 1px solid {c['border']};
    border-radius: 6px;
    padding: 4px 12px;
    font-size: 12px;
}}
QPushButton#tabBtn:!checked {{
    background-color: {c['bg_mid']};
    color: {c['text_secondary']};
}}
QPushButton#tabBtn:checked {{
    background-color: {c['accent']};
    color: white;
    border-color: {c['accent']};
}}
QPushButton#tabBtn:hover:!checked {{
    background-color: {c['bg_mid']};
    border-color: {c['accent']};
    color: {c['accent']};
}}
"""
