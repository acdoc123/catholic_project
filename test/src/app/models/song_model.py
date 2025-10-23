from dataclasses import dataclass, field
from typing import Optional

@dataclass
class Song:
    """Lớp dữ liệu đại diện cho một bài hát."""
    id: int
    songbook_id: int
    title: str
    lyrics: str
    number: Optional[str] = None
    page: Optional[str] = None

@dataclass
class Songbook:
    """Lớp dữ liệu đại diện cho một sách bài hát."""
    id: int
    name: str
    songs: list = field(default_factory=list)

@dataclass
class Theme:
    """Lớp dữ liệu đại diện cho một chủ đề trình chiếu."""
    id: int = 1
    name: str = "Default"
    slide_width: int = 12192000  # 16:9 in EMUs
    slide_height: int = 6858000 # 16:9 in EMUs
    bg_color: str = "#000000"
    
    # Thuộc tính Tựa đề
    title_font_name: str = "Arial"
    title_font_size: int = 44
    title_font_color: str = "#FFFF00" # Yellow
    title_font_bold: bool = True
    title_font_italic: bool = False
    title_font_underline: bool = False
    
    # Thuộc tính Lời bài hát
    lyric_font_name: str = "Arial"
    lyric_font_size: int = 32
    lyric_font_color: str = "#FFFFFF" # White
    lyric_alignment: str = "CENTER" # LEFT, CENTER, RIGHT
    lyric_font_bold: bool = False
    lyric_font_italic: bool = False
    lyric_font_underline: bool = False