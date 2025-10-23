from PySide6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QSplitter
from PySide6.QtCore import Qt
from.songbook_view import SongbookView
from.playlist_view import PlaylistView
from.preview_view import PreviewView

class MainWindow(QMainWindow):
    """
    Cửa sổ chính của ứng dụng, chứa 3 cột giao diện.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Lyric Presenter")
        self.setGeometry(100, 100, 1200, 700)

        # Tạo các widget cho 3 cột
        self.songbook_view = SongbookView(self)
        self.playlist_view = PlaylistView(self)
        self.preview_view = PreviewView(self)

        # Sử dụng QSplitter để cho phép thay đổi kích thước các cột
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.songbook_view)
        splitter.addWidget(self.playlist_view)
        splitter.addWidget(self.preview_view)

        # Thiết lập tỉ lệ ban đầu cho các cột
        splitter.setSizes([2, 1, 2])

        self.setCentralWidget(splitter)