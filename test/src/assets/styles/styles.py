STYLESHEET = """
QWidget {
    background-color: #2E2E2E;
    color: #F0F0F0;
    font-family: Segoe UI;
    font-size: 10pt;
}

QMainWindow {
    border: 1px solid #1E1E1E;
}

QDialog {
    background-color: #383838;
}

/* --- Buttons --- */
QPushButton {
    background-color: #0078D7;
    border: 1px solid #005A9E;
    color: #FFFFFF;
    padding: 8px 16px;
    border-radius: 4px;
}
QPushButton:hover {
    background-color: #005A9E;
}
QPushButton:pressed {
    background-color: #004C87;
}
QPushButton:disabled {
    background-color: #4A4A4A;
    color: #909090;
}

/* --- Input Fields --- */
QLineEdit, QTextEdit, QSpinBox {
    background-color: #1E1E1E;
    border: 1px solid #555;
    border-radius: 4px;
    padding: 6px;
    color: #F0F0F0;
}
QLineEdit:focus, QTextEdit:focus, QSpinBox:focus {
    border: 1px solid #0078D7;
}

/* --- List & Tree --- */
QListWidget, QTreeWidget {
    background-color: #252526;
    border: 1px solid #1E1E1E;
    border-radius: 4px;
    padding: 5px;
}
QListWidget::item, QTreeWidget::item {
    padding: 8px;
    border-radius: 3px;
}
QListWidget::item:hover, QTreeWidget::item:hover {
    background-color: #3E3E40;
}
QListWidget::item:selected, QTreeWidget::item:selected {
    background-color: #0078D7;
    color: #FFFFFF;
}
QHeaderView::section {
    background-color: #383838;
    color: #F0F0F0;
    padding: 4px;
    border: 1px solid #1E1E1E;
}

/* --- Combobox --- */
QComboBox {
    background-color: #1E1E1E;
    border: 1px solid #555;
    border-radius: 4px;
    padding: 6px;
}
QComboBox:hover {
    border: 1px solid #777;
}
QComboBox::drop-down {
    border: none;
}
QComboBox QAbstractItemView {
    background-color: #1E1E1E;
    border: 1px solid #555;
    selection-background-color: #0078D7;
}

/* --- Labels & GroupBox --- */
QLabel {
    background-color: transparent;
}
QGroupBox {
    border: 1px solid #555;
    border-radius: 4px;
    margin-top: 10px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 5px;
    color: #CCCCCC;
}

/* --- ScrollBars --- */
QScrollBar:vertical {
    border: none;
    background: #252526;
    width: 10px;
    margin: 0px 0px 0px 0px;
}
QScrollBar::handle:vertical {
    background: #555;
    min-height: 20px;
    border-radius: 5px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    border: none;
    background: none;
}
"""
