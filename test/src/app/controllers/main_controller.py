# src/app/controllers/main_controller.py

from PySide6.QtWidgets import QInputDialog, QMessageBox, QFileDialog
from PySide6.QtCore import QModelIndex

from app.models.database_model import DatabaseModel
from app.models.playlist_model import PlaylistModel
from app.models.song_model import Song
from app.views.main_window import MainWindow
from app.views.dialogs import AddSongDialog, ThemeDialog
from utils.pptx_generator import generate_presentation

class MainController:
    """
    Lớp Controller chính, liên kết Model và View.
    """
    def __init__(self, model: DatabaseModel, view: MainWindow):
        self.db_model = model
        self.view = view

        self.playlist_model = PlaylistModel()
        self.all_songbooks_cache = []
        self.current_theme = self.db_model.get_theme()
        self.current_selected_playlist_song_id = None
        self.font_overrides = {}

        self._connect_signals()
        self._initial_load()
        self._update_preview()

    def _connect_signals(self):
        sb_view = self.view.songbook_view
        pl_view = self.view.playlist_view
        pr_view = self.view.preview_view
        # --- Kết nối tín hiệu từ Model đến View ---
        # Bất cứ khi nào playlist thay đổi, cả 2 view đều tự động cập nhật
        self.playlist_model.playlist_updated.connect(pl_view.on_playlist_updated)
        self.playlist_model.playlist_updated.connect(sb_view.on_playlist_updated)

        # --- Kết nối tín hiệu từ View đến Controller ---
        sb_view.add_songbook_clicked.connect(self._handle_add_songbook)
        sb_view.add_song_clicked.connect(self._handle_add_song)
        sb_view.add_to_playlist_clicked.connect(self._handle_add_to_playlist)
        sb_view.edit_song_clicked.connect(self._handle_edit_song)
        sb_view.delete_song_clicked.connect(self._handle_delete_song)
        sb_view.rename_songbook_clicked.connect(self._handle_rename_songbook)
        sb_view.delete_songbook_clicked.connect(self._handle_delete_songbook)
        sb_view.search_widget.filters_changed.connect(self._handle_filters_changed)

        pl_view.export_button_clicked.connect(self._handle_export_pptx)
        pl_view.song_selected.connect(self._handle_playlist_song_selected)
        pl_view.theme_button_clicked.connect(self._handle_open_theme_dialog)
        pl_view.song_removed.connect(self._handle_remove_from_playlist) # Tín hiệu mới
        pl_view.playlist_reordered.connect(self._handle_playlist_reordered) # Tín hiệu mới

        pr_view.font_size_changed.connect(self._handle_font_size_changed)

    def _initial_load(self):
        self.all_songbooks_cache = self.db_model.get_songbooks_with_songs()
        self.view.songbook_view.search_widget.populate_songbooks(self.all_songbooks_cache)
        self.view.songbook_view.populate_tree(self.all_songbooks_cache)

    def _reload_all_data(self):
        self.all_songbooks_cache = self.db_model.get_songbooks_with_songs()
        self.view.songbook_view.search_widget.populate_songbooks(self.all_songbooks_cache)
        self._handle_filters_changed()

    def _handle_filters_changed(self):
        filters = self.view.songbook_view.search_widget.get_filters()
        search_results = self.db_model.search_songs(**filters)
        self.view.songbook_view.populate_tree(search_results)

    def _update_songbook_view_buttons(self):
        """
        Cập nhật trạng thái các nút trong SongbookView bằng cách áp dụng lại bộ lọc hiện tại.
        """
        self._handle_filters_changed()

    # --- Các hàm xử lý cho Songbook View ---
    def _handle_add_songbook(self):
        text, ok = QInputDialog.getText(self.view, "Sách bài hát mới", "Nhập tên sách bài hát:")
        if ok and text:
            songbook_id = self.db_model.add_songbook(text)
            if songbook_id:
                QMessageBox.information(self.view, "Thành công", f"Đã tạo sách bài hát '{text}'.")
                self._reload_all_data()
            else:
                QMessageBox.warning(self.view, "Lỗi", "Tên sách bài hát này đã tồn tại.")

    def _handle_add_song(self):
        if not self.all_songbooks_cache:
            QMessageBox.warning(self.view, "Chưa có Sách bài hát", "Vui lòng tạo một sách bài hát trước.")
            return
        dialog = AddSongDialog(self.all_songbooks_cache, model=self.db_model, parent=self.view)
        if dialog.exec():
            data = dialog.get_song_data()
            new_song = Song(id=None, **data)
            self.db_model.add_song(new_song)
            QMessageBox.information(self.view, "Thành công", f"Đã thêm bài hát '{data['title']}'.")
            self._reload_all_data()

    def _handle_edit_song(self, song_id: int):
        song_to_edit = self.db_model.get_song_by_id(song_id)
        if not song_to_edit: return
        
        dialog = AddSongDialog(
            songbooks=self.all_songbooks_cache, 
            model=self.db_model, 
            song=song_to_edit, 
            parent=self.view
        )
        
        if dialog.exec():
            data = dialog.get_song_data()
            updated_song = Song(id=song_id, **data)
            self.db_model.update_song(updated_song)
            QMessageBox.information(self.view, "Thành công", f"Đã cập nhật bài hát '{data['title']}'.")
            self._reload_all_data()

    def _handle_delete_song(self, song_id: int):
        song = self.db_model.get_song_by_id(song_id)
        if not song: return
        reply = QMessageBox.question(self.view, "Xác nhận xóa",
                                     f"Bạn có chắc chắn muốn xóa bài hát '{song.title}' không?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.db_model.delete_song(song_id)
            self._reload_all_data()

    def _handle_rename_songbook(self, songbook_id: int):
        old_name = ""
        for sb in self.all_songbooks_cache:
            if sb.id == songbook_id:
                old_name = sb.name
                break
        new_name, ok = QInputDialog.getText(self.view, "Đổi tên Sách bài hát",
                                            "Nhập tên mới:", text=old_name)
        if ok and new_name and new_name!= old_name:
            if not self.db_model.rename_songbook(songbook_id, new_name):
                QMessageBox.warning(self.view, "Lỗi", "Tên sách bài hát này đã tồn tại.")
            else:
                self._reload_all_data()

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
            self.db_model.delete_songbook(songbook_id)
            self.playlist_model.clear() # Ra lệnh cho model xóa playlist
            self._reload_all_data()

    def _handle_add_to_playlist(self, song_id: int):
        song = self.db_model.get_song_by_id(song_id)
        if song:
            self.playlist_model.add_song(song)

    # --- Các hàm xử lý cho Playlist và Preview ---
    def _handle_playlist_song_selected(self, song_id: int):
        self.current_selected_playlist_song_id = song_id
        self._update_preview()

    def _handle_open_theme_dialog(self):
        dialog = ThemeDialog(self.current_theme, self.view)
        if dialog.exec():
            self.current_theme = dialog.get_theme_data()
            self.db_model.save_theme(self.current_theme)
            self._update_preview()
            QMessageBox.information(self.view, "Thành công", "Đã lưu thiết lập Theme.")

    def _handle_remove_from_playlist(self, song_id: int):
        self.playlist_model.remove_song_by_id(song_id)

    def _handle_playlist_reordered(self):
        new_ordered_ids = self.view.playlist_view.get_current_song_ids()
        self.playlist_model.update_order_from_ids(new_ordered_ids)

    def _handle_export_pptx(self):
        songs_to_export = self.playlist_model.get_playlist() # Lấy từ model
        if not songs_to_export:
            QMessageBox.warning(self.view, "Danh sách trống", "...")
            return
        filePath, _ = QFileDialog.getSaveFileName(self.view, "Lưu file PowerPoint", "", "PowerPoint Files (*.pptx)")
        if filePath:
            try:
                generate_presentation(songs=songs_to_export, theme=self.current_theme, output_path=filePath, overrides=self.font_overrides)
                QMessageBox.information(self.view, "Hoàn tất", f"Đã xuất thành công file:\n{filePath}")
            except Exception as e:
                QMessageBox.critical(self.view, "Lỗi xuất file", f"Đã có lỗi xảy ra:\n{e}")
                print(f"Lỗi khi xuất PPTX: {e}")

    def _handle_font_size_changed(self, font_type: str, value: int):
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
        song = None
        title_size = self.current_theme.title_font_size
        lyric_size = self.current_theme.lyric_font_size
        if self.current_selected_playlist_song_id:
            song_id = self.current_selected_playlist_song_id
            song = self.db_model.get_song_by_id(song_id)
            if song and song_id in self.font_overrides:
                title_size = self.font_overrides[song_id].get('title', title_size)
                lyric_size = self.font_overrides[song_id].get('lyric', lyric_size)
        self.view.preview_view.update_preview(theme=self.current_theme, song=song, title_size=title_size, lyric_size=lyric_size)