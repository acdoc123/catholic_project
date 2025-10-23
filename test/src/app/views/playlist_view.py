# src/app/views/playlist_view.py

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QListWidget, 
                               QAbstractItemView, QListWidgetItem, QLabel, QHBoxLayout)
from PySide6.QtCore import Signal, Qt

class PlaylistView(QWidget):
    """
    Cột ở giữa, hiển thị danh sách các bài hát sẽ được trình chiếu.
    Đã được đơn giản hóa, không dùng QPainter.
    """
    theme_button_clicked = Signal()
    export_button_clicked = Signal()
    song_selected = Signal(int)
    song_removed = Signal(int) # Gửi đi song_id
    playlist_reordered = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        
        self.theme_button = QPushButton("Thiết lập Theme")
        self.export_button = QPushButton("Xuất ra PowerPoint (.pptx)")

        self.list_widget = QListWidget()
        # Kích hoạt chức năng kéo-thả, người dùng có thể kéo thả trực tiếp các mục
        self.list_widget.setDragDropMode(QAbstractItemView.InternalMove)
        self.list_widget.setAlternatingRowColors(True)

        self.layout.addWidget(self.theme_button)
        self.layout.addWidget(self.list_widget)
        self.layout.addWidget(self.export_button)

        # Kết nối tín hiệu
        self.theme_button.clicked.connect(self.theme_button_clicked)
        self.export_button.clicked.connect(self.export_button_clicked)
        self.list_widget.currentRowChanged.connect(self._on_song_selected)
        self.list_widget.model().rowsMoved.connect(self.playlist_reordered)

    def on_playlist_updated(self, songs: list):
        """
        Slot công khai, được kết nối với tín hiệu của PlaylistModel.
        Hàm này sẽ tạo ra các widget tùy chỉnh cho mỗi mục.
        """
        self.list_widget.blockSignals(True)
        current_selection_id = None
        if self.list_widget.currentItem():
            current_selection_id = self.list_widget.currentItem().data(Qt.UserRole)

        self.list_widget.clear()
        
        new_item_to_select = None
        for song in songs:
            # 1. Tạo một QListWidgetItem (nó sẽ là container vô hình)
            item = QListWidgetItem(self.list_widget)
            item.setData(Qt.UserRole, song.id)

            # 2. Tạo widget tùy chỉnh của chúng ta (đây là phần sẽ hiển thị)
            item_widget = self._create_playlist_item_widget(song)
            
            # 3. Đặt kích thước cho container để nó vừa với widget của chúng ta
            item.setSizeHint(item_widget.sizeHint())

            # 4. Gắn widget tùy chỉnh vào container
            self.list_widget.setItemWidget(item, item_widget)

            if song.id == current_selection_id:
                new_item_to_select = item
        
        if new_item_to_select:
            self.list_widget.setCurrentItem(new_item_to_select)

        self.list_widget.blockSignals(False)

    def _create_playlist_item_widget(self, song):
        """Tạo một widget chứa tên bài hát và nút xóa."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(5, 2, 5, 2) # Thu nhỏ lề

        label = QLabel(song.title)
        delete_btn = QPushButton("Xóa")
        delete_btn.setFixedWidth(60) # Đặt chiều rộng cố định cho nút

        # Kết nối nút xóa, dùng lambda để truyền song.id
        delete_btn.clicked.connect(lambda checked=False, s_id=song.id: self.song_removed.emit(s_id))

        layout.addWidget(label)
        layout.addStretch() # Đẩy nút xóa về bên phải
        layout.addWidget(delete_btn)
        
        return widget

    def _on_song_selected(self, row: int):
        """Slot nội bộ, xử lý khi người dùng chọn một mục."""
        if row >= 0:
            item = self.list_widget.item(row)
            if item:
                song_id = item.data(Qt.UserRole)
                self.song_selected.emit(song_id)

    def get_current_song_ids(self) -> list[int]:
        """
        Lấy danh sách ID của các bài hát theo thứ tự hiện tại trên giao diện.
        """
        ids = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            ids.append(item.data(Qt.UserRole))
        return ids