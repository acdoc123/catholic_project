from PySide6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit, 
                               QTextEdit, QDialogButtonBox, QComboBox, QFileDialog, 
                               QPushButton, QColorDialog, QFontDialog, QSpinBox,
                               QCheckBox, QGroupBox, QHBoxLayout, QLabel, QMessageBox)
from PySide6.QtGui import QColor, QFont
from PySide6.QtCore import Signal
from app.models.song_model import Song, Songbook, Theme
from typing import Optional
from app.models.database_model import DatabaseModel
import copy

class AddSongDialog(QDialog):
    """Dialog để thêm hoặc sửa một bài hát."""
    import_from_file_clicked = Signal(str) # Gửi đi 'pdf' hoặc 'image'

    def __init__(self, songbooks: list, model: DatabaseModel, song: Optional = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Thêm/Sửa bài hát")

        self.model = model # Dialog giờ đã biết về database model
        self.existing_song_id = song.id if song else None
        
        self.layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.songbook_combo = QComboBox()
        for sb in songbooks:
            self.songbook_combo.addItem(sb.name, sb.id)

        self.title_edit = QLineEdit()
        self.number_edit = QLineEdit()
        self.page_edit = QLineEdit()
        self.lyrics_edit = QTextEdit()
        self.lyrics_edit.setAcceptRichText(False)

        form_layout.addRow("Sách bài hát:", self.songbook_combo)
        form_layout.addRow("Tựa đề:", self.title_edit)
        form_layout.addRow("Số thứ tự:", self.number_edit)
        form_layout.addRow("Số trang:", self.page_edit)
        form_layout.addRow("Lời bài hát:", self.lyrics_edit)

        self.layout.addLayout(form_layout)

        # Phần nhập từ file
        import_group = QGroupBox("Nhập lời từ tệp (Yêu cầu API Key)")
        import_layout = QVBoxLayout()
        self.import_pdf_button = QPushButton("Nhập từ PDF")
        self.import_image_button = QPushButton("Nhập từ Ảnh")
        import_layout.addWidget(self.import_pdf_button)
        import_layout.addWidget(self.import_image_button)
        import_group.setLayout(import_layout)
        self.layout.addWidget(import_group)

        # Nút OK và Cancel
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.validate_and_accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

        # Kết nối tín hiệu
        self.import_pdf_button.clicked.connect(lambda: self.import_from_file_clicked.emit('pdf'))
        self.import_image_button.clicked.connect(lambda: self.import_from_file_clicked.emit('image'))

        # Điền dữ liệu nếu là sửa bài hát
        if song:
            self.title_edit.setText(song.title)
            self.number_edit.setText(song.number)
            self.page_edit.setText(song.page)
            self.lyrics_edit.setPlainText(song.lyrics)
            index = self.songbook_combo.findData(song.songbook_id)
            if index >= 0:
                self.songbook_combo.setCurrentIndex(index)
    def validate_and_accept(self):
        """Kiểm tra dữ liệu, nếu hợp lệ thì mới đóng dialog."""
        data = self.get_song_data()

        # 1. Kiểm tra các trường bắt buộc
        if not data['title'] or not data['lyrics']:
            QMessageBox.warning(self, "Thiếu thông tin", "Tựa đề và Lời bài hát không được để trống.")
            return # Không đóng dialog

        # 2. Kiểm tra trùng lặp
        is_duplicate = self.model.song_exists(
            title=data['title'],
            songbook_id=data['songbook_id'],
            exclude_song_id=self.existing_song_id
        )
        if is_duplicate:
            QMessageBox.warning(self, "Lỗi trùng lặp", "Bài hát có tựa đề này đã tồn tại trong sách được chọn.")
            return # Không đóng dialog

        # Nếu tất cả đều hợp lệ, gọi hàm accept() gốc để đóng dialog
        super().accept()

    def get_song_data(self) -> dict:
        return {
            "songbook_id": self.songbook_combo.currentData(),
            "title": self.title_edit.text().strip(),
            "number": self.number_edit.text().strip(),
            "page": self.page_edit.text().strip(),
            "lyrics": self.lyrics_edit.toPlainText().strip()
        }
    
    def set_lyrics(self, text: str):
        self.lyrics_edit.setPlainText(text)

# (Code cho ThemeDialog sẽ tương tự, với các widget để chỉnh sửa màu sắc, font chữ, v.v.)

class ThemeDialog(QDialog):
    """Dialog để chỉnh sửa Theme trình chiếu mặc định."""
    def __init__(self, current_theme: Theme, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Thiết lập Theme Mặc định")
        self.setMinimumWidth(450)

        # Quan trọng: Làm việc trên một bản sao để có thể hủy bỏ thay đổi
        self.theme = copy.deepcopy(current_theme)

        # Lưu trữ các đối tượng QFont để mở FontDialog
        self.title_font = QFont(self.theme.title_font_name)
        self.lyric_font = QFont(self.theme.lyric_font_name)

        # --- Bố cục chính ---
        self.layout = QVBoxLayout(self)

        # --- Cài đặt chung ---
        general_group = QGroupBox("Cài đặt chung")
        general_layout = QFormLayout()
        self.slide_size_combo = QComboBox()
        self.slide_size_combo.addItems(["16:9", "4:3"])
        self.bg_color_button = QPushButton()
        self.bg_color_button.setFixedSize(100, 25)
        self.bg_color_button.clicked.connect(self._pick_bg_color)
        general_layout.addRow("Kích thước Slide:", self.slide_size_combo)
        general_layout.addRow("Màu nền:", self.bg_color_button)
        general_group.setLayout(general_layout)
        self.layout.addWidget(general_group)

        # --- Cài đặt Tựa đề ---
        title_group = QGroupBox("Định dạng Tựa đề")
        title_layout = QFormLayout()
        font_layout_title = QHBoxLayout()
        self.title_font_label = QLabel()
        self.title_font_button = QPushButton("Chọn Font")
        self.title_font_button.clicked.connect(self._pick_title_font)
        font_layout_title.addWidget(self.title_font_label)
        font_layout_title.addWidget(self.title_font_button)
        self.title_color_button = QPushButton()
        self.title_color_button.setFixedSize(100, 25)
        self.title_color_button.clicked.connect(self._pick_title_color)
        style_layout_title = QHBoxLayout()
        self.title_bold_check = QCheckBox("In đậm")
        self.title_italic_check = QCheckBox("In nghiêng")
        self.title_underline_check = QCheckBox("Gạch chân")
        style_layout_title.addWidget(self.title_bold_check)
        style_layout_title.addWidget(self.title_italic_check)
        style_layout_title.addWidget(self.title_underline_check)
        title_layout.addRow("Font:", font_layout_title)
        title_layout.addRow("Màu chữ:", self.title_color_button)
        title_layout.addRow("Kiểu:", style_layout_title)
        title_group.setLayout(title_layout)
        self.layout.addWidget(title_group)

        # --- Cài đặt Lời bài hát ---
        lyric_group = QGroupBox("Định dạng Lời bài hát")
        lyric_layout = QFormLayout()
        font_layout_lyric = QHBoxLayout()
        self.lyric_font_label = QLabel()
        self.lyric_font_button = QPushButton("Chọn Font")
        self.lyric_font_button.clicked.connect(self._pick_lyric_font)
        font_layout_lyric.addWidget(self.lyric_font_label)
        font_layout_lyric.addWidget(self.lyric_font_button)
        self.lyric_color_button = QPushButton()
        self.lyric_color_button.setFixedSize(100, 25)
        self.lyric_color_button.clicked.connect(self._pick_lyric_color)
        self.lyric_align_combo = QComboBox()
        self.lyric_align_combo.addItems(["CENTER", "LEFT", "RIGHT", "JUSTIFY"])
        style_layout_lyric = QHBoxLayout()
        self.lyric_bold_check = QCheckBox("In đậm")
        self.lyric_italic_check = QCheckBox("In nghiêng")
        self.lyric_underline_check = QCheckBox("Gạch chân")
        style_layout_lyric.addWidget(self.lyric_bold_check)
        style_layout_lyric.addWidget(self.lyric_italic_check)
        style_layout_lyric.addWidget(self.lyric_underline_check)
        lyric_layout.addRow("Font:", font_layout_lyric)
        lyric_layout.addRow("Màu chữ:", self.lyric_color_button)
        lyric_layout.addRow("Căn lề:", self.lyric_align_combo)
        lyric_layout.addRow("Kiểu:", style_layout_lyric)
        lyric_group.setLayout(lyric_layout)
        self.layout.addWidget(lyric_group)

        # --- Nút OK / Cancel ---
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

        self._populate_data()

    def _populate_data(self):
        """Điền dữ liệu từ theme hiện tại vào các widget."""
        # General
        if self.theme.slide_width == 9144000: # 4:3
            self.slide_size_combo.setCurrentIndex(1)
        else:
            self.slide_size_combo.setCurrentIndex(0)
        self._update_color_button(self.bg_color_button, self.theme.bg_color)
        
        # Title
        self.title_font_label.setText(f"{self.theme.title_font_name}")
        self._update_color_button(self.title_color_button, self.theme.title_font_color)
        self.title_bold_check.setChecked(self.theme.title_font_bold)
        self.title_italic_check.setChecked(self.theme.title_font_italic)
        self.title_underline_check.setChecked(self.theme.title_font_underline)

        # Lyric
        self.lyric_font_label.setText(f"{self.theme.lyric_font_name}")
        self._update_color_button(self.lyric_color_button, self.theme.lyric_font_color)
        self.lyric_align_combo.setCurrentText(self.theme.lyric_alignment)
        self.lyric_bold_check.setChecked(self.theme.lyric_font_bold)
        self.lyric_italic_check.setChecked(self.theme.lyric_font_italic)
        self.lyric_underline_check.setChecked(self.theme.lyric_font_underline)

        print("ThemeDialog: Dữ liệu đã được điền vào các widget.")

    def _update_color_button(self, button, color_hex):
        """Cập nhật màu nền cho nút chọn màu."""
        button.setStyleSheet(f"background-color: {color_hex}; border: 1px solid #555;")

    def _pick_color(self, initial_color_hex):
        """Mở QColorDialog và trả về màu đã chọn."""
        color = QColorDialog.getColor(QColor(initial_color_hex), self, "Chọn màu")
        return color.name() if color.isValid() else initial_color_hex

    def _pick_bg_color(self):
        new_color = self._pick_color(self.theme.bg_color)
        self.theme.bg_color = new_color
        self._update_color_button(self.bg_color_button, new_color)

    def _pick_title_color(self):
        new_color = self._pick_color(self.theme.title_font_color)
        self.theme.title_font_color = new_color
        self._update_color_button(self.title_color_button, new_color)

    def _pick_lyric_color(self):
        new_color = self._pick_color(self.theme.lyric_font_color)
        self.theme.lyric_font_color = new_color
        self._update_color_button(self.lyric_color_button, new_color)

    def _pick_title_font(self):
        ok, font = QFontDialog.getFont(self.title_font, self, "Chọn font cho Tựa đề")
        if ok:
            self.title_font = font
            self.title_font_label.setText(font.family())

    def _pick_lyric_font(self):
        ok, font = QFontDialog.getFont(self.lyric_font, self, "Chọn font cho Lời bài hát")
        if ok:
            self.lyric_font = font
            self.lyric_font_label.setText(font.family())

    def get_theme_data(self) -> Theme:
        """
        Lấy dữ liệu từ các widget và cập nhật vào đối tượng theme.
        Hàm này được Controller gọi sau khi dialog được accept.
        """
        # General
        if self.slide_size_combo.currentIndex() == 1: # 4:3
            self.theme.slide_width = 9144000
            self.theme.slide_height = 6858000
        else: # 16:9
            self.theme.slide_width = 12192000
            self.theme.slide_height = 6858000
        
        # Title
        self.theme.title_font_name = self.title_font.family()
        self.theme.title_font_bold = self.title_bold_check.isChecked()
        self.theme.title_font_italic = self.title_italic_check.isChecked()
        self.theme.title_font_underline = self.title_underline_check.isChecked()

        # Lyric
        self.theme.lyric_font_name = self.lyric_font.family()
        self.theme.lyric_alignment = self.lyric_align_combo.currentText()
        self.theme.lyric_font_bold = self.lyric_bold_check.isChecked()
        self.theme.lyric_font_italic = self.lyric_italic_check.isChecked()
        self.theme.lyric_font_underline = self.lyric_underline_check.isChecked()

        return self.theme