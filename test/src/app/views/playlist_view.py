# src/app/views/playlist_view.py

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QListWidget, 
                               QAbstractItemView, QListWidgetItem, QStyledItemDelegate,
                               QStyle, QApplication, QStyleOptionViewItem)
from PySide6.QtCore import Signal, Qt, QModelIndex, QRect, QPoint
from PySide6.QtGui import QPainter, QMouseEvent, QIcon

class PlaylistItemDelegate(QStyledItemDelegate):
    """Delegate tùy chỉnh để vẽ các mục trong playlist."""
    def __init__(self, parent=None):
        super().__init__(parent)

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
        painter.setRenderHint(QPainter.TextAntialiasing)
        
        # Vẽ nền mặc định (màu chọn, màu xen kẽ)
        super().paint(painter, option, index)

        # --- Vẽ các nút ---
        style = QApplication.style()
        button_size = option.rect.height() - 10

        # Nút Xóa bên phải
        delete_icon = style.standardIcon(QStyle.SP_TrashIcon)
        self.delete_rect = QRect(option.rect.right() - button_size - 5, option.rect.top() + 5, button_size, button_size)
        delete_icon.paint(painter, self.delete_rect)

        # Nút Kéo bên trái
        drag_icon = style.standardIcon(QStyle.SP_ToolBarHorizontalExtensionButton)
        self.drag_rect = QRect(option.rect.left() + 5, option.rect.top() + 5, button_size, button_size)
        drag_icon.paint(painter, self.drag_rect)

        # --- Vẽ văn bản ---
        text = index.data(Qt.DisplayRole)
        text_rect = option.rect.adjusted(self.drag_rect.width() + 10, 0, -self.delete_rect.width() - 10, 0)
        painter.drawText(text_rect, Qt.AlignVCenter | Qt.AlignLeft, text)

    def editorEvent(self, event: QMouseEvent, model, option, index):
        if event.type() == QMouseEvent.MouseButtonPress and event.button() == Qt.LeftButton:
            # Tính toán lại vùng nút xóa cho mục hiện tại
            button_size = option.rect.height() - 10
            delete_rect = QRect(option.rect.right() - button_size - 5, option.rect.top() + 5, button_size, button_size)
            
            if delete_rect.contains(event.pos()):
                # Phát tín hiệu yêu cầu xóa
                self.parent().remove_song_clicked.emit(index)
                return True
        return False

class PlaylistView(QWidget):
    """
    Cột ở giữa, hiển thị danh sách các bài hát sẽ được trình chiếu.
    """
    theme_button_clicked = Signal()
    export_button_clicked = Signal()
    song_selected = Signal(int) # Gửi đi song_id
    remove_song_clicked = Signal(QModelIndex) # Tín hiệu mới
    playlist_reordered = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        
        self.theme_button = QPushButton("Thiết lập Theme")
        self.export_button = QPushButton("Xuất ra PowerPoint (.pptx)")

        self.list_widget = QListWidget()
        self.list_widget.setDragDropMode(QAbstractItemView.InternalMove)
        self.list_widget.setAlternatingRowColors(True)
        self.list_widget.setStyleSheet("QListWidget::item { height: 30px; }") # Tăng chiều cao item

        # Thiết lập delegate tùy chỉnh
        self.delegate = PlaylistItemDelegate(self)
        self.list_widget.setItemDelegate(self.delegate)

        self.layout.addWidget(self.theme_button)
        self.layout.addWidget(self.list_widget)
        self.layout.addWidget(self.export_button)

        # Kết nối tín hiệu
        self.theme_button.clicked.connect(self.theme_button_clicked)
        self.export_button.clicked.connect(self.export_button_clicked)
        self.list_widget.currentRowChanged.connect(self._on_song_selected)
        self.list_widget.model().rowsMoved.connect(self.playlist_reordered)

    def _on_song_selected(self, row):
        if row >= 0:
            item = self.list_widget.item(row)
            song_id = item.data(Qt.UserRole)
            self.song_selected.emit(song_id)

    def add_song_to_list(self, song_title: str, song_id: int):
        item = QListWidgetItem(song_title)
        item.setData(Qt.UserRole, song_id)
        self.list_widget.addItem(item)

    def get_playlist_song_ids(self) -> list[int]:
        ids = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            ids.append(item.data(Qt.UserRole))
        return ids

    def clear_playlist(self):
        self.list_widget.clear()