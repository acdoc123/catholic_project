# src/app/views/preview_view.py

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QSpinBox, 
                               QFormLayout, QGroupBox)
from PySide6.QtGui import QPainter, QColor, QFont
from PySide6.QtCore import Qt, Signal, QRect
from typing import Optional
from app.models.song_model import Theme, Song

class PreviewWidget(QWidget):
    """Widget tùy chỉnh để vẽ bản xem trước của slide."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.theme = Theme()
        self.song = None
        self.custom_title_size = None
        self.custom_lyric_size = None
        self.setMinimumHeight(300)

    def set_data(self, theme: Theme, song: Optional, title_size: int, lyric_size: int):
        self.theme = theme
        self.song = song
        self.custom_title_size = title_size
        self.custom_lyric_size = lyric_size
        self.update() # Yêu cầu vẽ lại widget

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)

        # Vẽ nền slide
        bg_color = QColor(self.theme.bg_color)
        painter.fillRect(self.rect(), bg_color)

        if not self.song:
            return

        # Tính toán khu vực vẽ dựa trên tỉ lệ 16:9
        widget_ratio = self.width() / self.height()
        slide_ratio = 16 / 9
        
        if widget_ratio > slide_ratio:
            slide_height = self.height()
            slide_width = slide_height * slide_ratio
            offset_x = (self.width() - slide_width) / 2
            offset_y = 0
        else:
            slide_width = self.width()
            slide_height = slide_width / slide_ratio
            offset_x = 0
            offset_y = (self.height() - slide_height) / 2
            
        slide_rect = QRect(offset_x, offset_y, slide_width, slide_height)
        
        # Vẽ tựa đề
        title_font = QFont(self.theme.title_font_name, self.custom_title_size)
        title_font.setBold(self.theme.title_font_bold)
        painter.setFont(title_font)
        painter.setPen(QColor(self.theme.title_font_color))
        
        title_rect = QRect(slide_rect.x(), slide_rect.y() + 20, slide_rect.width(), 100)
        painter.drawText(title_rect, Qt.AlignCenter | Qt.TextWordWrap, self.song.title)

        # Vẽ lời bài hát
        lyric_font = QFont(self.theme.lyric_font_name, self.custom_lyric_size)
        painter.setFont(lyric_font)
        painter.setPen(QColor(self.theme.lyric_font_color))
        
        lyric_rect = QRect(slide_rect.x() + 20, title_rect.bottom(), slide_rect.width() - 40, slide_rect.height() - title_rect.height() - 40)
        
        alignment = Qt.AlignCenter
        if self.theme.lyric_alignment == 'LEFT':
            alignment = Qt.AlignLeft
        elif self.theme.lyric_alignment == 'RIGHT':
            alignment = Qt.AlignRight

        painter.drawText(lyric_rect, alignment | Qt.TextWordWrap, self.song.lyrics)


class PreviewView(QWidget):
    """Cột bên phải, hiển thị bản xem trước và các tùy chọn tinh chỉnh."""
    font_size_changed = Signal(str, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        
        self.preview_widget = PreviewWidget()
        
        self.settings_box = QGroupBox("Tùy chỉnh Font chữ cho bài hát này")
        self.settings_layout = QFormLayout()

        self.title_font_size_spinbox = QSpinBox()
        self.title_font_size_spinbox.setRange(10, 100)
        
        self.lyric_font_size_spinbox = QSpinBox()
        self.lyric_font_size_spinbox.setRange(10, 100)

        self.settings_layout.addRow("Cỡ chữ Tựa đề:", self.title_font_size_spinbox)
        self.settings_layout.addRow("Cỡ chữ Lời:", self.lyric_font_size_spinbox)
        self.settings_box.setLayout(self.settings_layout)

        self.layout.addWidget(self.preview_widget)
        self.layout.addWidget(self.settings_box)
        
        self.title_font_size_spinbox.valueChanged.connect(lambda val: self.font_size_changed.emit('title', val))
        self.lyric_font_size_spinbox.valueChanged.connect(lambda val: self.font_size_changed.emit('lyric', val))

    def update_preview(self, theme: Theme, song: Optional, title_size: int, lyric_size: int):
        self.title_font_size_spinbox.blockSignals(True)
        self.lyric_font_size_spinbox.blockSignals(True)
        
        self.title_font_size_spinbox.setValue(title_size)
        self.lyric_font_size_spinbox.setValue(lyric_size)
        
        self.title_font_size_spinbox.blockSignals(False)
        self.lyric_font_size_spinbox.blockSignals(False)
        
        self.preview_widget.set_data(theme, song, title_size, lyric_size)
        self.settings_box.setEnabled(song is not None)