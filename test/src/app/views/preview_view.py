# src/app/views/preview_view.py

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QSpinBox, QFormLayout, 
                               QGroupBox, QLabel, QScrollArea)
from PySide6.QtGui import QPainter, QColor, QFont, QTextDocument
from PySide6.QtCore import Qt, Signal, QRectF, QSize
from typing import Optional

from app.models.song_model import Theme, Song
from utils.slide_layout_engine import split_lyrics_into_slides
from utils.text_formatter import format_lyrics_for_display

class SingleSlidePreviewWidget(QWidget):
    """Widget để vẽ một slide demo duy nhất."""
    def __init__(self, text_html: str, theme: Theme, parent=None):
        super().__init__(parent)
        self.text_html = text_html
        self.theme = theme
        self.aspect_ratio = 16 / 9 if theme.slide_width > 10000000 else 4 / 3
        self.setMinimumHeight(150)

    def sizeHint(self) -> QSize:
        width = self.width()
        height = int(width / self.aspect_ratio)
        return QSize(width, height)

    def resizeEvent(self, event):
        self.updateGeometry()
        super().resizeEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)

        painter.fillRect(self.rect(), QColor(self.theme.bg_color))

        lyric_font = QFont(self.theme.lyric_font_name)
        
        text_rect = self.rect().adjusted(
            self.width() * 0.05, self.height() * 0.05,
            -self.width() * 0.05, -self.height() * 0.05
        )
        
        doc = QTextDocument()
        doc.setHtml(self.text_html)
        doc.setDefaultFont(lyric_font)
        doc.setTextWidth(text_rect.width())

        alignment = Qt.AlignmentFlag.AlignCenter
        if self.theme.lyric_alignment == 'LEFT': alignment = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop
        elif self.theme.lyric_alignment == 'RIGHT': alignment = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop
        
        option = doc.defaultTextOption()
        option.setAlignment(alignment)
        doc.setDefaultTextOption(option)
        
        painter.save()
        painter.translate(text_rect.topLeft())
        doc.drawContents(painter)
        painter.restore()

class PreviewView(QWidget):
    """Cột bên phải, hiển thị bản xem trước và các tùy chọn tinh chỉnh."""
    font_size_changed = Signal(str, int)

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

    def clear_preview(self):
        """Xóa tất cả các slide demo cũ."""
        while self.slides_layout.count():
            child = self.slides_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def update_preview(self, theme: Theme, song: Optional, title_size: int, lyric_size: int):
        self.clear_preview()
        self.settings_box.setEnabled(song is not None)

        if not song:
            return

        self.title_font_size_spinbox.blockSignals(True)
        self.lyric_font_size_spinbox.blockSignals(True)
        self.title_font_size_spinbox.setValue(title_size)
        self.lyric_font_size_spinbox.setValue(lyric_size)
        self.title_font_size_spinbox.blockSignals(False)
        self.lyric_font_size_spinbox.blockSignals(False)

        # 1. Tạo slide tựa đề
        title_html = f"<div style='text-align: center; font-size: {title_size}pt; font-weight: bold; color: {theme.title_font_color};'>{song.title}</div>"
        title_slide_widget = SingleSlidePreviewWidget(title_html, theme)
        self.slides_layout.addWidget(title_slide_widget)

        # 2. Sử dụng Layout Engine để chia lời bài hát
        lyric_font = QFont(theme.lyric_font_name, lyric_size)
        slide_w_px, slide_h_px = (960, 540) if theme.slide_width > 10000000 else (720, 540)
        box_w = slide_w_px * 0.9
        box_h = slide_h_px * 0.8
        bounding_box = QRectF(0, 0, box_w, box_h)
        
        lyrics_slides = split_lyrics_into_slides(song.lyrics, lyric_font, bounding_box)

        # 3. Tạo widget cho mỗi slide lời bài hát
        for slide_text in lyrics_slides:
            text_html = format_lyrics_for_display(slide_text, theme.title_font_color)
            full_html = f"<div style='font-size: {lyric_size}pt; color: {theme.lyric_font_color};'>{text_html}</div>"
            lyric_slide_widget = SingleSlidePreviewWidget(full_html, theme)
            self.slides_layout.addWidget(lyric_slide_widget)