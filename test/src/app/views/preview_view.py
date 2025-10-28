# src/app/views/preview_view.py

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QSpinBox, QFormLayout, 
                               QGroupBox, QLabel, QScrollArea, QTextEdit,
                               QSizePolicy)
from PySide6.QtGui import QPainter, QColor, QFont, QTextDocument
from PySide6.QtCore import Qt, Signal, QRectF, QSize, QTimer
from typing import Optional, List
import functools

from app.models.song_model import Theme, Song
# Chúng ta không cần split_lyrics_into_slides ở đây nữa
# Controller sẽ thực hiện việc đó và gửi danh sách slide cho View
from utils.text_formatter import format_lyrics_for_display

class EditableSlideWidget(QTextEdit):
    """
    Widget mới thay thế SingleSlidePreviewWidget.
    Đây là một QTextEdit được tùy chỉnh để trông giống slide
    và gửi tín hiệu khi nội dung thay đổi.
    """
    
    # Tín hiệu này sẽ gửi đi nội dung MỚI (dưới dạng plain text)
    content_changed = Signal(str)

    def __init__(self, theme: Theme, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.aspect_ratio = 16 / 9 if theme.slide_width > 10000000 else 4 / 3
        
        # Thiết lập giao diện
        self.setStyleSheet(f"""
            QTextEdit {{
                background-color: {self.theme.bg_color};
                border: 1px solid #555;
            }}
        """)
        
        # Đặt chiều cao tối thiểu và chính sách kích thước
        self.setMinimumHeight(150)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # Kết nối tín hiệu textChanged
        # Chúng ta dùng QTimer để "debounce" tín hiệu
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(750) # Chờ 750ms sau khi ngừng gõ
        self._timer.timeout.connect(self._emit_content_changed)
        
        self.textChanged.connect(self._timer.start)

    def _emit_content_changed(self):
        """Gửi đi nội dung plain text"""
        self.content_changed.emit(self.toPlainText())

    def set_slide_content(self, text_html: str, font: QFont, alignment: Qt.AlignmentFlag):
        """Đặt nội dung và định dạng cho slide"""
        self.blockSignals(True)
        self.setHtml(text_html)
        self.setFont(font)
        self.setAlignment(alignment)
        self.blockSignals(False)

    # Chúng ta cần ghi đè sizeHint để duy trì tỷ lệ khung hình
    def sizeHint(self) -> QSize:
        width = self.width()
        height = int(width / self.aspect_ratio)
        return QSize(width, height)

    def resizeEvent(self, event):
        # Cập nhật lại geometry để sizeHint hoạt động
        self.updateGeometry()
        super().resizeEvent(event)

class PreviewView(QWidget):
    """Cột bên phải, hiển thị bản xem trước và các tùy chọn tinh chỉnh."""
    font_size_changed = Signal(str, int)
    
    # Tín hiệu MỚI: (song_id, slide_index, new_plain_text)
    slide_content_edited = Signal(int, int, str) 
    
    # Tín hiệu MỚI: (song_id, new_title_html)
    title_content_edited = Signal(int, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area_content = QWidget()
        self.slides_layout = QVBoxLayout(self.scroll_area_content)
        self.scroll_area.setWidget(self.scroll_area_content)
        
        self.settings_box = QGroupBox("Tùy chỉnh Font chữ cho bài hát này")
        self.settings_layout = QFormLayout()
        self.title_font_size_spinbox = QSpinBox()
        self.title_font_size_spinbox.setRange(10, 100)
        self.lyric_font_size_spinbox = QSpinBox()
        self.lyric_font_size_spinbox.setRange(10, 100)
        self.settings_layout.addRow("Cỡ chữ Tựa đề:", self.title_font_size_spinbox)
        self.settings_layout.addRow("Cỡ chữ Lời:", self.lyric_font_size_spinbox)
        self.settings_box.setLayout(self.settings_layout)

        self.layout.addWidget(self.scroll_area)
        self.layout.addWidget(self.settings_box)
        
        self.title_font_size_spinbox.valueChanged.connect(lambda val: self.font_size_changed.emit('title', val))
        self.lyric_font_size_spinbox.valueChanged.connect(lambda val: self.font_size_changed.emit('lyric', val))
        
        self.current_song_id = None

    def clear_preview(self):
        """Xóa tất cả các slide demo cũ."""
        while self.slides_layout.count():
            child = self.slides_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        self.current_song_id = None

    def _on_lyric_slide_edited(self, index: int, new_text: str):
        """Slot nội bộ, kích hoạt khi một slide lời được sửa"""
        if self.current_song_id is not None:
            # Gửi tín hiệu lên Controller
            self.slide_content_edited.emit(self.current_song_id, index, new_text)

    def _on_title_slide_edited(self, new_text: str):
        """Slot nội bộ, kích hoạt khi slide tựa đề được sửa"""
        if self.current_song_id is not None:
            # Gửi tín hiệu lên Controller
            self.title_content_edited.emit(self.current_song_id, new_text)

    def update_preview(self, theme: Theme, song: Optional[Song], 
                         title_size: int, lyric_size: int, 
                         lyric_slides: List[str]):
        """
        Cập nhật bản xem trước.
        Hàm này giờ nhận một danh sách các slide lời bài hát (lyric_slides)
        đã được chia sẵn (do Controller cung cấp).
        """
        self.clear_preview()
        self.settings_box.setEnabled(song is not None)

        if not song:
            return
            
        self.current_song_id = song.id

        self.title_font_size_spinbox.blockSignals(True)
        self.lyric_font_size_spinbox.blockSignals(True)
        self.title_font_size_spinbox.setValue(title_size)
        self.lyric_font_size_spinbox.setValue(lyric_size)
        self.title_font_size_spinbox.blockSignals(False)
        self.lyric_font_size_spinbox.blockSignals(False)

        # 1. Tạo slide tựa đề (Cũng có thể chỉnh sửa)
        title_font = QFont(theme.title_font_name, title_size)
        title_font.setBold(theme.title_font_bold)
        title_font.setItalic(theme.title_font_italic)
        title_font.setUnderline(theme.title_font_underline)
        
        # Định dạng HTML cho tựa đề
        title_html = f"""
        <div style='
            font-size: {title_size}pt; 
            font-family: "{theme.title_font_name}";
            font-weight: {'bold' if theme.title_font_bold else 'normal'};
            font-style: {'italic' if theme.title_font_italic else 'normal'};
            text-decoration: {'underline' if theme.title_font_underline else 'none'};
            color: {theme.title_font_color};
        '>{song.title}</div>
        """
        
        title_slide_widget = EditableSlideWidget(theme)
        title_slide_widget.set_slide_content(title_html, title_font, Qt.AlignmentFlag.AlignCenter)
        # Kết nối tín hiệu chỉnh sửa
        title_slide_widget.content_changed.connect(self._on_title_slide_edited)
        self.slides_layout.addWidget(title_slide_widget)

        # 2. Tạo widget cho mỗi slide lời bài hát
        lyric_font = QFont(theme.lyric_font_name, lyric_size)
        lyric_font.setBold(theme.lyric_font_bold)
        lyric_font.setItalic(theme.lyric_font_italic)
        lyric_font.setUnderline(theme.lyric_font_underline)

        # Căn lề
        alignment = Qt.AlignmentFlag.AlignCenter
        if theme.lyric_alignment == 'LEFT': alignment = Qt.AlignmentFlag.AlignLeft
        elif theme.lyric_alignment == 'RIGHT': alignment = Qt.AlignmentFlag.AlignRight
        elif theme.lyric_alignment == 'JUSTIFY': alignment = Qt.AlignmentFlag.AlignJustify

        for index, slide_text in enumerate(lyric_slides):
            # Định dạng HTML (tô màu ĐK, 1.)
            text_html = format_lyrics_for_display(slide_text, theme.title_font_color)
            
            # Bọc trong thẻ div chính để kiểm soát font
            full_html = f"""
            <div style='
                font-size: {lyric_size}pt; 
                font-family: "{theme.lyric_font_name}";
                font-weight: {'bold' if theme.lyric_font_bold else 'normal'};
                font-style: {'italic' if theme.lyric_font_italic else 'normal'};
                text-decoration: {'underline' if theme.lyric_font_underline else 'none'};
                color: {theme.lyric_font_color};
            '>{text_html}</div>
            """
            
            lyric_slide_widget = EditableSlideWidget(theme)
            lyric_slide_widget.set_slide_content(full_html, lyric_font, alignment)
            
            # Kết nối tín hiệu, dùng functools.partial để gửi kèm 'index'
            lyric_slide_widget.content_changed.connect(
                functools.partial(self._on_lyric_slide_edited, index)
            )
            
            self.slides_layout.addWidget(lyric_slide_widget)