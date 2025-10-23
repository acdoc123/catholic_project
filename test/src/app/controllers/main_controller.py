import sys
from PySide6.QtWidgets import QInputDialog, QMessageBox, QFileDialog
from PySide6.QtCore import QModelIndex

from app.models.database_model import DatabaseModel
from app.models.song_model import Song, Theme
from app.views.main_window import MainWindow
from app.views.dialogs import AddSongDialog 
from PySide6.QtWidgets import QInputDialog, QMessageBox, QFileDialog
from PySide6.QtCore import QModelIndex
from app.views.dialogs import AddSongDialog, ThemeDialog # Thêm ThemeDialog
# Import các hàm tiện ích
from utils.pptx_generator import generate_presentation
# from utils.ai_parser import extract_text_from_file # Cho chức năng AI

class MainController:
    """
    Lớp Controller chính, liên kết Model và View.
    """
    def __init__(self, model: DatabaseModel, view: MainWindow):
        self.model = model
        self.view = view

        self.all_songbooks_cache = []  # Bộ nhớ đệm cho tất cả sách bài hát

        # Các biến trạng thái của ứng dụng
        self.current_theme = self.model.get_theme()
        self.current_selected_playlist_song_id = None
        self.font_overrides = {} # Dict để lưu các tùy chỉnh font cho từng bài hát

        # Kết nối tín hiệu từ View đến các hàm xử lý (slots) trong Controller
        self._connect_signals()

        # Tải dữ liệu ban đầu và hiển thị lên giao diện
        self._load_and_display_songbooks()
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
        
        # Kết nối các tín hiệu mới từ delegate
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
        # Thêm tín hiệu để cập nhật delegate khi playlist thay đổi
        pl_view.list_widget.model().rowsInserted.connect(self._update_delegate_playlist)
        pl_view.list_widget.model().rowsRemoved.connect(self._update_delegate_playlist)

        # --- Cột Preview (Bên phải) ---
        pr_view.font_size_changed.connect(self._handle_font_size_changed)

    def _initial_load(self):
        """Tải toàn bộ dữ liệu lần đầu và điền vào các widget."""
        self.all_songbooks_cache = self.model.get_songbooks_with_songs()
        self.view.songbook_view.search_widget.populate_songbooks(self.all_songbooks_cache)
        self.view.songbook_view.populate_tree(self.all_songbooks_cache)
    def _reload_all_data(self):
        """Tải lại toàn bộ dữ liệu sau khi có thay đổi (thêm/sửa/xóa)."""
        self.all_songbooks_cache = self.model.get_songbooks_with_songs()
        self.view.songbook_view.search_widget.populate_songbooks(self.all_songbooks_cache)
        # Sau khi tải lại, áp dụng lại bộ lọc hiện tại
        self._handle_filters_changed()
    def _handle_filters_changed(self):
        """Xử lý khi người dùng thay đổi bộ lọc và cập nhật danh sách."""
        filters = self.view.songbook_view.search_widget.get_filters()
        
        # Gọi hàm tìm kiếm trong model
        search_results = self.model.search_songs(**filters)
        
        # Hiển thị kết quả
        self.view.songbook_view.populate_tree(search_results)
        
        # Cập nhật lại trạng thái nút "Thêm" sau khi hiển thị kết quả
        self._update_songbook_view_buttons()
    def _load_and_display_songbooks(self):
        """Tải dữ liệu từ model và yêu cầu SongbookView hiển thị nó."""
        songbooks = self.model.get_songbooks_with_songs()
        self.view.songbook_view.populate_tree(songbooks) # Gọi hàm mới
        print("Đã tải lại danh sách Sách bài hát.")
    def _handle_open_theme_dialog(self):
        """Mở dialog để chỉnh sửa theme."""
        dialog = ThemeDialog(self.current_theme, self.view)
        if dialog.exec():
            self.current_theme = dialog.get_theme_data()
            self.model.save_theme(self.current_theme)
            self._update_preview() # Cập nhật preview ngay lập tức
            QMessageBox.information(self.view, "Thành công", "Đã lưu thiết lập Theme.")

    def _handle_remove_from_playlist(self, index: QModelIndex):
        """Xóa một bài hát khỏi playlist."""
        row = index.row()
        self.view.playlist_view.list_widget.takeItem(row)
        # Nếu bài hát bị xóa là bài đang được chọn, xóa preview
        if self.current_selected_playlist_song_id:
            if not any(self.current_selected_playlist_song_id == self.view.playlist_view.list_widget.item(i).data(Qt.UserRole) for i in range(self.view.playlist_view.list_widget.count())):
                 self.current_selected_playlist_song_id = None
                 self._update_preview()
# --- Các hàm xử lý mới cho các nút trên delegate ---

    def _handle_edit_song(self, song_id: int):
        song_to_edit = self.model.get_song_by_id(song_id)
        if not song_to_edit: return

        songbooks = self.model.get_songbooks_with_songs()
        dialog = AddSongDialog(songbooks, song=song_to_edit, parent=self.view)
        
        if dialog.exec():
            data = dialog.get_song_data()
            updated_song = Song(id=song_id, **data)
            self.model.update_song(updated_song)
            self._reload_all_data()

    def _handle_delete_song(self, song_id: int):
        song = self.model.get_song_by_id(song_id)
        if not song: return
        
        reply = QMessageBox.question(self.view, "Xác nhận xóa", 
                                     f"Bạn có chắc chắn muốn xóa bài hát '{song.title}' không?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.model.delete_song(song_id)
            self._reload_all_data

    def _handle_rename_songbook(self, songbook_id: int):
        # Cần một hàm mới trong model để lấy tên sách từ ID
        # (Hoặc có thể tìm trong danh sách đã tải)
        songbooks = self.model.get_songbooks_with_songs()
        old_name = ""
        for sb in songbooks:
            if sb.id == songbook_id:
                old_name = sb.name
                break
        
        new_name, ok = QInputDialog.getText(self.view, "Đổi tên Sách bài hát", 
                                            "Nhập tên mới:", text=old_name)
        
        if ok and new_name and new_name!= old_name:
            if not self.model.rename_songbook(songbook_id, new_name):
                QMessageBox.warning(self.view, "Lỗi", "Tên sách bài hát này đã tồn tại.")
            else:
                self._reload_all_data

    def _handle_delete_songbook(self, songbook_id: int):
        # Tương tự, cần lấy tên sách
        songbooks = self.model.get_songbooks_with_songs()
        songbook_name = ""
        for sb in songbooks:
            if sb.id == songbook_id:
                songbook_name = sb.name
                break

        reply = QMessageBox.question(self.view, "Xác nhận xóa", 
                                     f"Bạn có chắc chắn muốn xóa sách '{songbook_name}' và TOÀN BỘ bài hát bên trong không?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.model.delete_songbook(songbook_id)
            self._reload_all_data
            self.view.playlist_view.clear_playlist() 
            self._update_songbook_view_buttons()


    def _handle_add_to_playlist(self, song_id: int):
        song = self.model.get_song_by_id(song_id)
        if song:
            self.view.playlist_view.add_song_to_list(song.title, song.id)
            # Tín hiệu rowsInserted sẽ tự động gọi _update_songbook_view_buttons
    def _update_songbook_view_buttons(self):
        """Cập nhật trạng thái các nút trong SongbookView."""
        playlist_ids = self.view.playlist_view.get_playlist_song_ids()
        self.view.songbook_view.set_playlist_ids(playlist_ids)
        # Tải lại cây để áp dụng thay đổi - cách đơn giản nhất
        self._reload_all_data

    def _update_delegate_playlist(self):
        """Cập nhật danh sách ID trong delegate để nó biết nút nào cần vô hiệu hóa."""
        playlist_ids = self.view.playlist_view.get_playlist_song_ids()
        self.view.songbook_view.delegate.set_playlist_ids(playlist_ids)
        # Yêu cầu vẽ lại tree view để cập nhật trạng thái nút
        self.view.songbook_view.tree_view.viewport().update()
    # --- Các hàm xử lý cho Songbook View ---

    def _handle_add_songbook(self):
        """Xử lý khi người dùng nhấn nút 'Thêm Sách bài hát'."""
        text, ok = QInputDialog.getText(self.view, "Sách bài hát mới", "Nhập tên sách bài hát:")
        if ok and text:
            songbook_id = self.model.add_songbook(text)
            if songbook_id:
                QMessageBox.information(self.view, "Thành công", f"Đã tạo sách bài hát '{text}'.")
                self._reload_all_data()
            else:
                QMessageBox.warning(self.view, "Lỗi", "Tên sách bài hát này đã tồn tại.")

    def _handle_add_song(self):
        """Mở dialog để thêm bài hát mới."""
        songbooks = self.model.get_songbooks_with_songs()
        if not songbooks:
            QMessageBox.warning(self.view, "Chưa có Sách bài hát", "Vui lòng tạo một sách bài hát trước.")
            return

        dialog = AddSongDialog(songbooks, model=self.model, parent=self.view)
        if dialog.exec():
            data = dialog.get_song_data()
            new_song = Song(id=None, **data)
            self.model.add_song(new_song)
            
            # Thông báo thành công và tải lại
            QMessageBox.information(self.view, "Thành công", f"Đã thêm bài hát '{data['title']}'.")
            self._reload_all_data()

    def _handle_add_to_playlist(self, index: QModelIndex):
        """Thêm một bài hát từ cây thư mục vào danh sách phát."""
        # Logic để lấy song_id từ QModelIndex sẽ phụ thuộc vào cách bạn
        # cấu trúc QStandardItemModel. Giả sử ID được lưu trong item.data().
        item = self.view.songbook_view.tree_view.model().itemFromIndex(index)
        if item and item.data(): # Chỉ các item bài hát mới có data (ID)
            song_id = item.data()
            song = self.model.get_song_by_id(song_id)
            if song:
                self.view.playlist_view.add_song_to_list(song.title, song.id)

    # --- Các hàm xử lý cho Playlist View ---

    def _handle_playlist_song_selected(self, song_id: int):
        """Xử lý khi một bài hát trong playlist được chọn."""
        self.current_selected_playlist_song_id = song_id
        self._update_preview()

    def _handle_export_pptx(self):
        """Xử lý việc xuất file PowerPoint."""
        playlist_ids = self.view.playlist_view.get_playlist_song_ids()
        if not playlist_ids:
            QMessageBox.warning(self.view, "Danh sách trống", "Vui lòng thêm ít nhất một bài hát vào danh sách phát.")
            return

        songs_to_export = [self.model.get_song_by_id(sid) for sid in playlist_ids]
        
        # Mở dialog để chọn nơi lưu file
        filePath, _ = QFileDialog.getSaveFileName(
            self.view, "Lưu file PowerPoint", "", "PowerPoint Files (*.pptx)"
        )

        if filePath:
            try:
                generate_presentation(
                    songs=songs_to_export,
                    theme=self.current_theme,
                    output_path=filePath,
                    overrides=self.font_overrides
                )
                QMessageBox.information(self.view, "Hoàn tất", f"Đã xuất thành công file:\n{filePath}")
            except Exception as e:
                QMessageBox.critical(self.view, "Lỗi xuất file", f"Đã có lỗi xảy ra:\n{e}")


    # --- Các hàm xử lý cho Preview View ---

    def _handle_font_size_changed(self, font_type: str, value: int):
        """Cập nhật font size override khi người dùng thay đổi spinbox."""
        if self.current_selected_playlist_song_id is None:
            return

        song_id = self.current_selected_playlist_song_id
        if song_id not in self.font_overrides:
            self.font_overrides[song_id] = {}
        
        if font_type == 'title':
            self.font_overrides[song_id]['title'] = value
        elif font_type == 'lyric':
            self.font_overrides[song_id]['lyric'] = value
        
        self._update_preview()

    # --- Hàm tiện ích nội bộ ---

    def _update_preview(self):
        """Cập nhật cột xem trước với bài hát và theme hiện tại."""
        song = None
        title_size = self.current_theme.title_font_size
        lyric_size = self.current_theme.lyric_font_size

        if self.current_selected_playlist_song_id:
            song_id = self.current_selected_playlist_song_id
            song = self.model.get_song_by_id(song_id)
            
            # Lấy giá trị override nếu có
            if song_id in self.font_overrides:
                title_size = self.font_overrides[song_id].get('title', title_size)
                lyric_size = self.font_overrides[song_id].get('lyric', lyric_size)

        self.view.preview_view.update_preview(
            theme=self.current_theme,
            song=song,
            title_size=title_size,
            lyric_size=lyric_size
        )