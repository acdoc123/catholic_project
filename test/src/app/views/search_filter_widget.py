# src/app/views/search_filter_widget.py

from PySide6.QtWidgets import (QWidget, QHBoxLayout, QLineEdit, QComboBox, QLabel)
from PySide6.QtCore import Signal, QTimer

class SearchFilterWidget(QWidget):
    """Widget chứa các điều khiển tìm kiếm và lọc đã được thiết kế lại."""
    filters_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 5, 0, 5)

        # ComboBox để chọn loại (trường) tìm kiếm
        self.search_type_combo = QComboBox()
        # Dictionary để ánh xạ tên hiển thị với tên cột trong database
        self.search_type_map = {
            "Tên bài hát": "title",
            "Lời bài hát": "lyrics",
            "Số bài": "number",
            "Số trang": "page"
        }
        self.search_type_combo.addItems(self.search_type_map.keys())

        # Ô nhập từ khóa tìm kiếm
        self.keyword_input = QLineEdit()
        
        # ComboBox để lọc theo sách
        self.book_filter_combo = QComboBox()

        # Sắp xếp các widget trên layout
        self.layout.addWidget(QLabel("Tìm theo:"))
        self.layout.addWidget(self.search_type_combo)
        self.layout.addWidget(self.keyword_input)
        self.layout.addWidget(QLabel("Trong sách:"))
        self.layout.addWidget(self.book_filter_combo)

        # Timer để tránh tìm kiếm liên tục khi gõ (debouncing)
        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.setInterval(300) # Chờ 300ms sau khi ngừng gõ
        self.search_timer.timeout.connect(self.filters_changed)

        # Kết nối các tín hiệu
        self.keyword_input.textChanged.connect(self.search_timer.start)
        self.book_filter_combo.currentIndexChanged.connect(self.filters_changed)
        self.search_type_combo.currentIndexChanged.connect(self._on_search_type_changed)

        # Cập nhật placeholder lần đầu khi khởi tạo
        self._on_search_type_changed()

    def _on_search_type_changed(self):
        """
        Hàm được gọi khi người dùng thay đổi loại tìm kiếm.
        Nó sẽ cập nhật placeholder và xóa nội dung của ô nhập liệu.
        """
        current_selection = self.search_type_combo.currentText()
        self.keyword_input.setPlaceholderText(f"Nhập {current_selection.lower()}...")
        self.keyword_input.clear()
        # Kích hoạt tìm kiếm ngay lập tức vì nội dung đã được xóa
        self.filters_changed.emit()

    def populate_songbooks(self, songbooks):
        """Điền danh sách sách vào ComboBox."""
        self.book_filter_combo.blockSignals(True)
        self.book_filter_combo.clear()
        self.book_filter_combo.addItem("Tất cả các sách", 0)
        for sb in songbooks:
            self.book_filter_combo.addItem(sb.name, sb.id)
        self.book_filter_combo.blockSignals(False)

    def get_filters(self) -> dict:
        """Lấy các giá trị bộ lọc hiện tại để gửi cho Controller."""
        search_type_text = self.search_type_combo.currentText()
        # Lấy tên cột tương ứng từ dictionary
        search_by = self.search_type_map.get(search_type_text, "title")

        return {
            "keyword": self.keyword_input.text().strip(),
            "songbook_id": self.book_filter_combo.currentData() or 0,
            "search_by": search_by,
        }