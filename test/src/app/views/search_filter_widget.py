from PySide6.QtWidgets import (QWidget, QHBoxLayout, QLineEdit, QComboBox, 
                               QSpinBox, QLabel)
from PySide6.QtCore import Signal, QTimer

class SearchFilterWidget(QWidget):
    """Widget chứa các điều khiển tìm kiếm và lọc."""
    filters_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 5, 0, 5)

        # Từ khóa tìm kiếm
        self.keyword_input = QLineEdit()
        self.keyword_input.setPlaceholderText("Tìm theo từ khóa...")
        
        # Bộ lọc sách
        self.book_filter_combo = QComboBox()
        
        # Bộ lọc theo số
        self.number_type_combo = QComboBox()
        self.number_type_combo.addItems()
        self.number_input = QSpinBox()
        self.number_input.setRange(0, 9999) # 0 để vô hiệu hóa
        self.number_input.setSpecialValueText("...") # Hiển thị khi giá trị là 0

        self.layout.addWidget(self.keyword_input)
        self.layout.addWidget(QLabel("Trong sách:"))
        self.layout.addWidget(self.book_filter_combo)
        self.layout.addWidget(self.number_type_combo)
        self.layout.addWidget(self.number_input)

        # Sử dụng QTimer để tránh tìm kiếm liên tục khi gõ (debouncing)
        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.setInterval(300) # 300ms
        self.search_timer.timeout.connect(self.filters_changed)

        # Kết nối tín hiệu
        self.keyword_input.textChanged.connect(self.search_timer.start)
        self.book_filter_combo.currentIndexChanged.connect(self.filters_changed)
        self.number_type_combo.currentIndexChanged.connect(self.filters_changed)
        self.number_input.valueChanged.connect(self.filters_changed)

    def populate_songbooks(self, songbooks):
        """Điền danh sách sách vào ComboBox."""
        self.book_filter_combo.blockSignals(True)
        self.book_filter_combo.clear()
        self.book_filter_combo.addItem("Tất cả các sách", 0) # 0 là ID cho "tất cả"
        for sb in songbooks:
            self.book_filter_combo.addItem(sb.name, sb.id)
        self.book_filter_combo.blockSignals(False)

    def get_filters(self) -> dict:
        """Lấy các giá trị bộ lọc hiện tại."""
        number = self.number_input.value()
        search_by = ""
        if number > 0:
            search_by = 'number' if self.number_type_combo.currentIndex() == 0 else 'page'

        return {
            "keyword": self.keyword_input.text().strip(),
            "songbook_id": self.book_filter_combo.currentData() or 0,
            "search_by": search_by,
            "number": number if number > 0 else None
        }