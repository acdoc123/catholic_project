# src/app/controllers/main_controller.py

from PySide6.QtWidgets import QInputDialog, QMessageBox, QFileDialog
from PySide6.QtCore import QModelIndex

from app.models.database_model import DatabaseModel
from app.models.song_model import Song
from app.views.main_window import MainWindow
from app.views.dialogs import AddSongDialog, ThemeDialog
from utils.pptx_generator import generate_presentation

class MainController:
    """
    Lớp Controller chính, liên kết Model và View.
    """
    def __init__(self, model: DatabaseModel, view: MainWindow):
        self.model = model
        self.view = view
        self.all_songbooks_cache = []
        self.current_theme = self.model.get_theme()
        self.current_selected_playlist_song_id = None
        self.font_overrides = {}
        self._connect_signals()
        self._initial_load()
        self._update_preview()

    def _connect_signals(self):
        """Kết nối tất cả các tín hiệu từ các widget của View."""
        sb_view = self.view.songbook_view
        pl_view = self.view.playlist_view
        pr_view = self.view.preview_view

        # --- Cột Songbook (Bên trái) ---
        sb_view.add_songbook_clicked.connect(self._handle_add_songbook)
        sb_view.add_song_clicked.connect(self._handle_add_song)
        sb_view.add_to_playlist_clicked.connect(self._handle_add_to_playlist)
        sb_view.edit_song_clicked.connect(self._handle_edit_song)
        sb_view.delete_song_clicked.connect(self._handle_delete_song)
        sb_view.rename_songbook_clicked.connect(self._handle_rename_songbook)
        sb_view.delete_songbook_clicked.connect(self._handle_delete_songbook)
        sb_view.search_widget.filters_changed.connect(self._handle_filters_changed)

        # --- Cột Playlist (Ở giữa) ---
        pl_view.export_button_clicked.connect(self._handle_export_pptx)
        pl_view.song_selected.connect(self._handle_playlist_song_selected)
        pl_view.theme_button_clicked.connect(self._handle_open_theme_dialog)
        pl_view.remove_song_clicked.connect(self._handle_remove_from_playlist)
        pl_view.list_widget.model().rowsInserted.connect(self._update_songbook_view_buttons)
        pl_view.list_widget.model().rowsRemoved.connect(self._update_songbook_view_buttons)

        # --- Cột Preview (Bên phải) ---
        pr_view.font_size_changed.connect(self._handle_font_size_changed)

    def _initial_load(self):
        """Tải toàn bộ dữ liệu lần đầu và điền vào các widget."""
        self.all_songbooks_cache = self.model.get_songbooks_with_songs()
        self.view.songbook_view.search_widget.populate_songbooks(self.all_songbooks_cache)
        self.view.songbook_view.populate_tree(self.all_songbooks_cache)

    def _reload_all_data(self):
        """Tải lại toàn bộ dữ liệu sau khi có thay đổi và áp dụng lại bộ lọc."""
        self.all_songbooks_cache = self.model.get_songbooks_with_songs()
        self.view.songbook_view.search_widget.populate_songbooks(self.all_songbooks_cache)
        self._handle_filters_changed()

    def _handle_filters_changed(self):
        """Xử lý khi người dùng thay đổi bộ lọc và cập nhật danh sách."""
        filters = self.view.songbook_view.search_widget.get_filters()
        search_results = self.model.search_songs(**filters)
        self.view.songbook_view.populate_tree(search_results)
        self._update_songbook_view_buttons()

    def _update_songbook_view_buttons(self):
        """Cập nhật trạng thái các nút trong SongbookView một cách hiệu quả."""
        playlist_ids = self.view.playlist_view.get_playlist_song_ids()
        self.view.songbook_view.set_playlist_ids(playlist_ids)
        self.view.songbook_view.update_button_states()

    # --- Các hàm xử lý cho Songbook View ---
    def _handle_add_songbook(self):
        text, ok = QInputDialog.getText(self.view, "Sách bài hát mới", "Nhập tên sách bài hát:")
        if ok and text:
            songbook_id = self.model.add_songbook(text)
            if songbook_id:
                QMessageBox.information(self.view, "Thành công", f"Đã tạo sách bài hát '{text}'.")
                self._reload_all_data()
            else:
                QMessageBox.warning(self.view, "Lỗi", "Tên sách bài hát này đã tồn tại.")

    def _handle_add_song(self):
        songbooks = self.model.get_songbooks_with_songs()
        if not songbooks:
            QMessageBox.warning(self.view, "Chưa có Sách bài hát", "Vui lòng tạo một sách bài hát trước.")
            return
        dialog = AddSongDialog(songbooks, model=self.model, parent=self.view)
        if dialog.exec():
            data = dialog.get_song_data()
            new_song = Song(id=None, **data)
            self.model.add_song(new_song)
            QMessageBox.information(self.view, "Thành công", f"Đã thêm bài hát '{data['title']}'.")
            self._reload_all_data()

    def _handle_edit_song(self, song_id: int):
        song_to_edit = self.model.get_song_by_id(song_id)
        if not song_to_edit: return
        
        # <<< SỬA LỖI Ở ĐÂY: Thêm `model=self.model` vào lời gọi hàm >>>
        dialog = AddSongDialog(
            songbooks=self.all_songbooks_cache, 
            model=self.model, 
            song=song_to_edit, 
            parent=self.view
        )
        
        if dialog.exec():
            data = dialog.get_song_data()
            updated_song = Song(id=song_id, **data)
            self.model.update_song(updated_song)
            QMessageBox.information(self.view, "Thành công", f"Đã cập nhật bài hát '{data['title']}'.")
            self._reload_all_data()

    def _handle_delete_song(self, song_id: int):
        song = self.model.get_song_by_id(song_id)
        if not song: return
        reply = QMessageBox.question(self.view, "Xác nhận xóa",
                                     f"Bạn có chắc chắn muốn xóa bài hát '{song.title}' không?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.model.delete_song(song_id)
            self._reload_all_data() # <<< SỬA LỖI Ở ĐÂY: Thêm ()

    def _handle_rename_songbook(self, songbook_id: int):
        old_name = ""
        for sb in self.all_songbooks_cache:
            if sb.id == songbook_id:
                old_name = sb.name
                break
        new_name, ok = QInputDialog.getText(self.view, "Đổi tên Sách bài hát",
                                            "Nhập tên mới:", text=old_name)
        if ok and new_name and new_name!= old_name:
            if not self.model.rename_songbook(songbook_id, new_name):
                QMessageBox.warning(self.view, "Lỗi", "Tên sách bài hát này đã tồn tại.")
            else:
                self._reload_all_data() # <<< SỬA LỖI Ở ĐÂY: Thêm ()

    def _handle_delete_songbook(self, songbook_id: int):
        songbook_name = ""
        for sb in self.all_songbooks_cache:
            if sb.id == songbook_id:
                songbook_name = sb.name
                break
        reply = QMessageBox.question(self.view, "Xác nhận xóa",
                                     f"Bạn có chắc chắn muốn xóa sách '{songbook_name}' và TOÀN BỘ bài hát bên trong không?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.model.delete_songbook(songbook_id)
            self.view.playlist_view.clear_playlist()
            self._reload_all_data() # <<< SỬA LỖI Ở ĐÂY: Thêm ()

    def _handle_add_to_playlist(self, song_id: int):
        song = self.model.get_song_by_id(song_id)
        if song:
            self.view.playlist_view.add_song_to_list(song.title, song.id)

    # --- Các hàm xử lý cho Playlist và Preview ---
    def _handle_playlist_song_selected(self, song_id: int):
        self.current_selected_playlist_song_id = song_id
        self._update_preview()

    def _handle_open_theme_dialog(self):
        dialog = ThemeDialog(self.current_theme, self.view)
        if dialog.exec():
            self.current_theme = dialog.get_theme_data()
            self.model.save_theme(self.current_theme)
            self._update_preview()
            QMessageBox.information(self.view, "Thành công", "Đã lưu thiết lập Theme.")

    def _handle_remove_from_playlist(self, index: QModelIndex):
        self.view.playlist_view.list_widget.takeItem(index.row())

    def _handle_export_pptx(self):
        #... (Hàm này giữ nguyên)
        playlist_ids = self.view.playlist_view.get_playlist_song_ids()
        if not playlist_ids:
            QMessageBox.warning(self.view, "Danh sách trống", "Vui lòng thêm ít nhất một bài hát vào danh sách phát.")
            return
        songs_to_export = [self.model.get_song_by_id(sid) for sid in playlist_ids]
        filePath, _ = QFileDialog.getSaveFileName(self.view, "Lưu file PowerPoint", "", "PowerPoint Files (*.pptx)")
        if filePath:
            try:
                generate_presentation(songs=songs_to_export, theme=self.current_theme, output_path=filePath, overrides=self.font_overrides)
                QMessageBox.information(self.view, "Hoàn tất", f"Đã xuất thành công file:\n{filePath}")
            except Exception as e:
                QMessageBox.critical(self.view, "Lỗi xuất file", f"Đã có lỗi xảy ra:\n{e}")

    def _handle_font_size_changed(self, font_type: str, value: int):
        #... (Hàm này giữ nguyên)
        if self.current_selected_playlist_song_id is None: return
        song_id = self.current_selected_playlist_song_id
        if song_id not in self.font_overrides:
            self.font_overrides[song_id] = {}
        if font_type == 'title':
            self.font_overrides[song_id]['title'] = value
        elif font_type == 'lyric':
            self.font_overrides[song_id]['lyric'] = value
        self._update_preview()

    def _update_preview(self):
        #... (Hàm này giữ nguyên)
        song = None
        title_size = self.current_theme.title_font_size
        lyric_size = self.current_theme.lyric_font_size
        if self.current_selected_playlist_song_id:
            song_id = self.current_selected_playlist_song_id
            song = self.model.get_song_by_id(song_id)
            if song_id in self.font_overrides:
                title_size = self.font_overrides[song_id].get('title', title_size)
                lyric_size = self.font_overrides[song_id].get('lyric', lyric_size)
        self.view.preview_view.update_preview(theme=self.current_theme, song=song, title_size=title_size, lyric_size=lyric_size)