# src/app/views/songbook_view.py

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QTreeView, 
                               QHBoxLayout, QLabel)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QStandardItemModel, QStandardItem
import qtawesome as qta
from app.constants import (
    ICON_RENAME, ICON_DELETE, ICON_ADD_SLIDE, 
    ICON_EDIT_SONG, ICON_NEW_SONG, ICON_NEW_SONGBOOK, COLOR_ADD_BUTTON, COLOR_DELETE_BUTTON, COLOR_EDIT_BUTTON
)
from.search_filter_widget import SearchFilterWidget

class SongbookView(QWidget):
    """
    Cột bên trái, hiển thị cây thư mục Sách bài hát và các bài hát.
    Sử dụng phương pháp setItemWidget đơn giản và trực tiếp.
    """
    add_song_clicked = Signal()
    add_songbook_clicked = Signal()
    rename_songbook_clicked = Signal(int)
    delete_songbook_clicked = Signal(int)
    add_to_playlist_clicked = Signal(int)
    edit_song_clicked = Signal(int)
    delete_song_clicked = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.playlist_song_ids = set()

        self.song_widgets = {}

        self.add_song_button = QPushButton(qta.icon(ICON_NEW_SONG), "Thêm bài hát mới")
        self.add_songbook_button = QPushButton(qta.icon(ICON_NEW_SONGBOOK, color="#592b2b"), "Thêm Sách bài hát")

        self.search_widget = SearchFilterWidget()

        self.tree_view = QTreeView()
        self.tree_view.setHeaderHidden(True)
        self.tree_view.setIndentation(10)
        
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.add_song_button, stretch=2)
        button_layout.addWidget(self.add_songbook_button, stretch=1)
        
        self.layout.addLayout(button_layout)
        self.layout.addWidget(self.search_widget)
        self.layout.addWidget(self.tree_view)
        
        self.model = QStandardItemModel()
        self.tree_view.setModel(self.model)

        self.add_song_button.clicked.connect(self.add_song_clicked)
        self.add_songbook_button.clicked.connect(self.add_songbook_clicked)

    def set_playlist_ids(self, ids: set):
        """Cập nhật danh sách ID các bài hát đang có trong playlist."""
        self.playlist_song_ids = ids

    def update_button_states(self):
        """
        Cập nhật trạng thái của các nút một cách hiệu quả mà không cần vẽ lại toàn bộ cây.
        """
        for song_id, widgets in self.song_widgets.items():
            is_in_playlist = song_id in self.playlist_song_ids
            widgets['add_btn'].setEnabled(not is_in_playlist)
            widgets['edit_btn'].setEnabled(not is_in_playlist)
            widgets['delete_btn'].setEnabled(not is_in_playlist)

    def populate_tree(self, songbooks):
        """Điền dữ liệu (có thể là kết quả tìm kiếm) vào cây."""
        self.model.clear()
    
        self.song_widgets.clear() # Xóa các widget cũ trước khi tạo lại
        root_node = self.model.invisibleRootItem()

        for sb in songbooks:
            songbook_item = QStandardItem() 
            songbook_item.setEditable(False)
            root_node.appendRow(songbook_item)
            
            songbook_widget = self._create_songbook_widget(sb)
            self.tree_view.setIndexWidget(songbook_item.index(), songbook_widget)

            for song in sb.songs:
                song_item = QStandardItem()
                song_item.setEditable(False)
                songbook_item.appendRow(song_item)

                song_widget = self._create_song_widget(song)
                self.tree_view.setIndexWidget(song_item.index(), song_widget)
        
        self.tree_view.expandAll()

    def _create_songbook_widget(self, songbook):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        label = QLabel(f"{songbook.name}")
        label.setStyleSheet("font-weight: bold;")
        rename_btn = QPushButton(qta.icon(ICON_RENAME), "")
        delete_btn = QPushButton(qta.icon(ICON_DELETE), "")
        rename_btn.clicked.connect(lambda checked=False, sb_id=songbook.id: self.rename_songbook_clicked.emit(sb_id))
        delete_btn.clicked.connect(lambda checked=False, sb_id=songbook.id: self.delete_songbook_clicked.emit(sb_id))
        layout.addWidget(label, stretch=7)
        layout.addWidget(rename_btn, stretch=2)
        layout.addWidget(delete_btn, stretch=1)
        return widget

    def _create_song_widget(self, song):
        """Tạo widget chứa tên bài hát và các nút chức năng."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        label = QLabel(song.title)
        label.setToolTip(song.title)

        add_btn = QPushButton(qta.icon(ICON_ADD_SLIDE, color=COLOR_ADD_BUTTON), "")
        edit_btn = QPushButton(qta.icon(ICON_EDIT_SONG, color=COLOR_EDIT_BUTTON), "")
        delete_btn = QPushButton(qta.icon(ICON_DELETE, color=COLOR_DELETE_BUTTON), "")

        # Lưu lại các nút để có thể cập nhật trạng thái sau này
        self.song_widgets[song.id] = {
            'add_btn': add_btn,
            'edit_btn': edit_btn,
            'delete_btn': delete_btn
        }

        # Vô hiệu hóa nút "Thêm" nếu bài hát đã có trong playlist
        if song.id in self.playlist_song_ids:
            add_btn.setEnabled(False)
            edit_btn.setEnabled(False)
            delete_btn.setEnabled(False)

        add_btn.clicked.connect(lambda checked=False, s_id=song.id: self.add_to_playlist_clicked.emit(s_id))
        edit_btn.clicked.connect(lambda checked=False, s_id=song.id: self.edit_song_clicked.emit(s_id))
        delete_btn.clicked.connect(lambda checked=False, s_id=song.id: self.delete_song_clicked.emit(s_id))

        layout.addWidget(label, stretch=7)
        layout.addWidget(add_btn, stretch=1)
        layout.addWidget(edit_btn, stretch=1)
        layout.addWidget(delete_btn, stretch=1)

        return widget

    def on_playlist_updated(self, songs: list):
        """Slot này được kết nối với tín hiệu của PlaylistModel."""
        playlist_ids = {song.id for song in songs}
        self.set_playlist_ids(playlist_ids)
        self.update_button_states()