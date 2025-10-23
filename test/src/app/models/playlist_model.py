# src/app/models/playlist_model.py

from PySide6.QtCore import QObject, Signal
from app.models.song_model import Song

class PlaylistModel(QObject):
    """
    Mô hình quản lý trạng thái của playlist trong bộ nhớ.
    Đây là "Nguồn chân lý duy nhất" cho danh sách phát hiện tại.
    """
    # Tín hiệu phát ra mỗi khi playlist thay đổi (thêm, xóa, sắp xếp, xóa hết)
    # Nó sẽ gửi đi một bản sao của danh sách bài hát hiện tại.
    playlist_updated = Signal(list)

    def __init__(self):
        super().__init__()
        self._songs: list = []

    def add_song(self, song: Song):
        """Thêm một bài hát vào playlist nếu nó chưa tồn tại."""
        # Kiểm tra bằng ID để đảm bảo tính duy nhất
        if song.id not in {s.id for s in self._songs}:
            self._songs.append(song)
            self.playlist_updated.emit(list(self._songs)) # Gửi đi một bản sao

    def remove_song_by_id(self, song_id: int):
        """Xóa một bài hát khỏi playlist dựa trên ID."""
        initial_count = len(self._songs)
        self._songs = [s for s in self._songs if s.id!= song_id]
        # Chỉ phát tín hiệu nếu có sự thay đổi
        if len(self._songs) < initial_count:
            self.playlist_updated.emit(list(self._songs))

    def update_order_from_ids(self, new_ordered_ids: list[int]):
        """Sắp xếp lại danh sách bài hát dựa trên một danh sách ID mới."""
        song_map = {s.id: s for s in self._songs}
        self._songs = [song_map[song_id] for song_id in new_ordered_ids if song_id in song_map]
        self.playlist_updated.emit(list(self._songs))

    def clear(self):
        """Xóa tất cả bài hát khỏi playlist."""
        if self._songs:
            self._songs.clear()
            self.playlist_updated.emit()

    def get_playlist(self) -> list:
        """Trả về một bản sao của danh sách bài hát hiện tại."""
        return list(self._songs)

    def get_playlist_song_ids(self) -> set[int]:
        """Trả về một tập hợp các ID bài hát để kiểm tra nhanh."""
        return {s.id for s in self._songs}