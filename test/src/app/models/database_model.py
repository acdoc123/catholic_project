# src/app/models/database_model.py

import sqlite3
from typing import List, Optional, Tuple
from.song_model import Songbook, Song, Theme

class DatabaseModel:
    """
    Lớp quản lý tất cả các tương tác với cơ sở dữ liệu SQLite.
    Đây là thành phần Model duy nhất giao tiếp trực tiếp với DB.
    """
    def __init__(self, db_path: str):
        self.conn = sqlite3.connect(db_path)
        
        # <<< SỬA LỖI UNICODE TẠI ĐÂY >>>
        # Dòng này đảm bảo dữ liệu văn bản đọc ra từ database
        # luôn là chuỗi Unicode (str) chuẩn của Python, xử lý tốt tiếng Việt.
        self.conn.text_factory = str
        
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON;")
        self._create_tables()
        self._ensure_default_theme()

    #... các phương thức còn lại giữ nguyên không thay đổi...

    def _create_tables(self):
        cursor = self.conn.cursor()
        # Bảng Sách bài hát
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS songbooks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            )
        """)
        # Bảng Bài hát
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS songs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                songbook_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                number TEXT,
                page TEXT,
                lyrics TEXT NOT NULL,
                FOREIGN KEY (songbook_id) REFERENCES songbooks (id) ON DELETE CASCADE,
                UNIQUE (songbook_id, title)
            )
        """)
        # Bảng Chủ đề - Đã cập nhật
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS themes (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                slide_width INTEGER NOT NULL,
                slide_height INTEGER NOT NULL,
                bg_color TEXT NOT NULL,
                title_font_name TEXT NOT NULL,
                title_font_size INTEGER NOT NULL,
                title_font_color TEXT NOT NULL,
                title_font_bold BOOLEAN NOT NULL,
                title_font_italic BOOLEAN NOT NULL,
                title_font_underline BOOLEAN NOT NULL,
                lyric_font_name TEXT NOT NULL,
                lyric_font_size INTEGER NOT NULL,
                lyric_font_color TEXT NOT NULL,
                lyric_alignment TEXT NOT NULL,
                lyric_font_bold BOOLEAN NOT NULL,
                lyric_font_italic BOOLEAN NOT NULL,
                lyric_font_underline BOOLEAN NOT NULL
            )
        """)
        self.conn.commit()

    def _ensure_default_theme(self):
        """Đảm bảo rằng có một chủ đề mặc định trong DB."""
        if not self.get_theme():
            default_theme = Theme()
            self.save_theme(default_theme)

    def get_theme(self) -> Optional:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM themes WHERE id = 1")
        row = cursor.fetchone()
        if row:
            return Theme(**dict(row))
        return None

    def save_theme(self, theme: Theme):
        cursor = self.conn.cursor()
        # Câu lệnh INSERT OR REPLACE - Đã cập nhật
        cursor.execute("""
            INSERT OR REPLACE INTO themes (
                id, name, slide_width, slide_height, bg_color, 
                title_font_name, title_font_size, title_font_color, 
                title_font_bold, title_font_italic, title_font_underline,
                lyric_font_name, lyric_font_size, lyric_font_color, 
                lyric_alignment, lyric_font_bold, lyric_font_italic, lyric_font_underline
            )
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            theme.id, theme.name, theme.slide_width, theme.slide_height, theme.bg_color,
            theme.title_font_name, theme.title_font_size, theme.title_font_color,
            theme.title_font_bold, theme.title_font_italic, theme.title_font_underline,
            theme.lyric_font_name, theme.lyric_font_size, theme.lyric_font_color,
            theme.lyric_alignment, theme.lyric_font_bold, theme.lyric_font_italic, theme.lyric_font_underline
        ))
        self.conn.commit()

    def get_songbooks_with_songs(self) -> List:
        songbooks_dict = {}
        cursor = self.conn.cursor()
        
        cursor.execute("SELECT id, name FROM songbooks ORDER BY name")
        songbook_rows = cursor.fetchall()
        for row in songbook_rows:
            songbook = Songbook(id=row['id'], name=row['name'])
            songbooks_dict[songbook.id] = songbook

        cursor.execute("SELECT * FROM songs ORDER BY title")
        song_rows = cursor.fetchall()
        for row in song_rows:
            song = Song(**dict(row))
            if song.songbook_id in songbooks_dict:
                songbooks_dict[song.songbook_id].songs.append(song)
        
        return list(songbooks_dict.values())
    
    def search_songs(self, keyword: str = "", songbook_id: int = 0, search_by: str = "title") -> List:
        """
        Tìm kiếm và lọc bài hát dựa trên các tiêu chí mới.
        - keyword: Từ khóa tìm kiếm.
        - songbook_id: Lọc theo ID của sách (0 = tất cả).
        - search_by: Cột để tìm kiếm ('title', 'lyrics', 'number', 'page').
        """
        songbooks_dict = {}
        cursor = self.conn.cursor()

        # Luôn lấy tất cả các sách để có thể điền kết quả vào
        cursor.execute("SELECT id, name FROM songbooks ORDER BY name")
        for row in cursor.fetchall():
            songbooks_dict[row['id']] = Songbook(id=row['id'], name=row['name'])

        # Nếu không có từ khóa, trả về tất cả bài hát (có thể lọc theo sách)
        if not keyword:
            query = "SELECT * FROM songs WHERE 1=1"
            params = []
            if songbook_id > 0:
                query += " AND songbook_id =?"
                params.append(songbook_id)
            
            query += " ORDER BY title"
            cursor.execute(query, tuple(params))
            for row in cursor.fetchall():
                song = Song(**dict(row))
                if song.songbook_id in songbooks_dict:
                    songbooks_dict[song.songbook_id].songs.append(song)
            return [sb for sb in songbooks_dict.values() if sb.songs]

        # Xây dựng câu truy vấn động nếu có từ khóa
        query = "SELECT * FROM songs WHERE 1=1"
        params = []

        # Xử lý trường tìm kiếm
        if search_by in ('title', 'lyrics'):
            query += f" AND {search_by} LIKE?"
            params.append(f"%{keyword}%")
        elif search_by in ('number', 'page'):
            # Cố gắng chuyển từ khóa thành số, nếu thất bại sẽ không có kết quả
            try:
                number_val = int(keyword)
                query += f" AND {search_by} =?"
                params.append(number_val)
            except ValueError:
                return # Trả về danh sách rỗng nếu nhập chữ vào ô tìm số
        
        # Xử lý bộ lọc sách
        if songbook_id > 0:
            query += " AND songbook_id =?"
            params.append(songbook_id)
        
        query += " ORDER BY title"
        
        # Thực thi truy vấn và điền kết quả
        cursor.execute(query, tuple(params))
        for row in cursor.fetchall():
            song = Song(**dict(row))
            if song.songbook_id in songbooks_dict:
                songbooks_dict[song.songbook_id].songs.append(song)

        # Chỉ trả về các sách có chứa kết quả tìm kiếm
        return [sb for sb in songbooks_dict.values() if sb.songs]

    def add_songbook(self, name: str) -> Optional[int]:
        try:
            cursor = self.conn.cursor()
            cursor.execute("INSERT INTO songbooks (name) VALUES (?)", (name,))
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            return None # Tên đã tồn tại

    def rename_songbook(self, songbook_id: int, new_name: str) -> bool:
        try:
            cursor = self.conn.cursor()
            cursor.execute("UPDATE songbooks SET name =? WHERE id =?", (new_name, songbook_id))
            self.conn.commit()
            return cursor.rowcount > 0
        except sqlite3.IntegrityError:
            return False

    def delete_songbook(self, songbook_id: int):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM songbooks WHERE id =?", (songbook_id,))
        self.conn.commit()

    def add_song(self, song: Song) -> Optional[int]:
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO songs (songbook_id, title, number, page, lyrics)
                VALUES (?,?,?,?,?)
            """, (song.songbook_id, song.title, song.number, song.page, song.lyrics))
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            return None # Bài hát đã tồn tại trong sách này

    def update_song(self, song: Song):
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE songs SET title =?, number =?, page =?, lyrics =?, songbook_id =?
            WHERE id =?
        """, (song.title, song.number, song.page, song.lyrics, song.songbook_id, song.id))
        self.conn.commit()

    def delete_song(self, song_id: int):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM songs WHERE id =?", (song_id,))
        self.conn.commit()

    def get_song_by_id(self, song_id: int) -> Optional:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM songs WHERE id =?", (song_id,))
        row = cursor.fetchone()
        return Song(**dict(row)) if row else None
    def song_exists(self, title: str, songbook_id: int, exclude_song_id: Optional[int] = None) -> bool:
        """
        Kiểm tra xem một bài hát có tồn tại trong một sách bài hát hay không.
        exclude_song_id: Dùng khi chỉnh sửa, để không tự so sánh với chính nó.
        """
        cursor = self.conn.cursor()
        query = "SELECT id FROM songs WHERE title =? AND songbook_id =?"
        params = (title, songbook_id)

        if exclude_song_id is not None:
            query += " AND id!=?"
            params = (title, songbook_id, exclude_song_id)

        cursor.execute(query, params)
        return cursor.fetchone() is not None

    def close(self):
        self.conn.close()