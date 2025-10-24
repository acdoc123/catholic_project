# src/utils/pptx_generator.py

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
from PySide6.QtGui import QFont
from PySide6.QtCore import QRectF

from app.models.song_model import Theme, Song
from.slide_layout_engine import split_lyrics_into_slides
from.text_formatter import PREFIXES_TO_HIGHLIGHT

def generate_presentation(songs: list, theme: Theme, output_path: str, overrides: dict):
    """
    Tạo một tệp PowerPoint với bố cục chuyên nghiệp hơn.
    """
    prs = Presentation()
    prs.slide_width = theme.slide_width
    prs.slide_height = theme.slide_height # 6858000
    blank_slide_layout = prs.slide_layouts[6] # Layout 6 thường là "Blank"

    # Xác định kích thước slide bằng Inches để định vị textbox
    is_widescreen = theme.slide_width > 10000000
    slide_width_inches = Inches(13.333) if is_widescreen else Inches(10)
    slide_height_inches = Inches(7.5)

    for i, song in enumerate(songs):
        # --- 1. Lấy tất cả các đoạn lời bài hát đã được chia ---
        lyric_size = overrides.get(song.id, {}).get('lyric', theme.lyric_font_size)
        lyric_font = QFont(theme.lyric_font_name, lyric_size)
        
        # Bounding box cho engine chia slide (chỉ dùng cho phần lời)
        slide_w_px, slide_h_px = (960, 540) if is_widescreen else (720, 540)
        # Box cho slide đầu tiên (sau khi trừ đi title)
        box_h_first = (slide_height_inches.emu - Inches(1).emu) / 914400.0 * 96
        # Box cho các slide sau (toàn màn hình)
        box_h_full = slide_height_inches.emu / 914400.0 * 96
        
        # Chia lời bài hát thành 2 phần: phần cho slide đầu và phần còn lại
        first_slide_lyric_chunk = "" # Sửa: Khởi tạo là chuỗi rỗng
        remaining_lyrics = song.lyrics
        
        # Tạm thời chia slide đầu tiên
        temp_bounding_box = QRectF(0, 0, slide_w_px * 0.9, box_h_first * 0.9)
        temp_slides = split_lyrics_into_slides(song.lyrics, lyric_font, temp_bounding_box)
        if temp_slides:
            first_slide_lyric_chunk = temp_slides[0] # Sửa: Chỉ lấy slide đầu tiên
            # Lấy phần lời còn lại
            # Sửa: Tính toán phần lời còn lại dựa trên độ dài của chuỗi đã lấy
            remaining_lyrics = song.lyrics[len(first_slide_lyric_chunk):].lstrip()

        # Chia phần lời còn lại cho các slide sau
        full_bounding_box = QRectF(0, 0, slide_w_px * 0.9, box_h_full * 0.9)
        lyrics_slides_remaining = split_lyrics_into_slides(remaining_lyrics, lyric_font, full_bounding_box)

        # --- 2. Tạo Slide Tựa đề (có lời) ---
        slide = prs.slides.add_slide(blank_slide_layout)
        background = slide.background
        fill = background.fill
        fill.solid()
        fill.fore_color.rgb = RGBColor.from_string(theme.bg_color[1:])

        # --- 2a. Thêm Textbox cho Tựa đề ---
        title_size = overrides.get(song.id, {}).get('title', theme.title_font_size)
        txBox_title = slide.shapes.add_textbox(Inches(0), Inches(0), slide_width_inches, Inches(1))
        tf_title = txBox_title.text_frame
        p_title = tf_title.paragraphs[0] # Sửa: Lấy đoạn văn đầu tiên
        p_title.text = song.title
        p_title.alignment = PP_ALIGN.CENTER
        font_title = p_title.font
        font_title.name = theme.title_font_name
        font_title.size = Pt(title_size)
        font_title.color.rgb = RGBColor.from_string(theme.title_font_color[1:])
        font_title.bold = theme.title_font_bold
        font_title.italic = theme.title_font_italic
        font_title.underline = theme.title_font_underline

        # --- 2b. Thêm Textbox cho phần lời đầu tiên ---
        if first_slide_lyric_chunk:
            txBox_content = slide.shapes.add_textbox(Inches(0), Inches(1), slide_width_inches, slide_height_inches - Inches(1))
            tf_content = txBox_content.text_frame
            tf_content.word_wrap = True
            p_content = tf_content.paragraphs[0] # Sửa: Lấy đoạn văn đầu tiên
            # Áp dụng logic tô màu và định dạng
            _apply_lyric_formatting(p_content, first_slide_lyric_chunk, theme, lyric_size)

        # --- 3. Tạo các slide lời bài hát tiếp theo ---
        for slide_text in lyrics_slides_remaining:
            if not slide_text.strip(): continue # Bỏ qua các slide trống
            
            slide = prs.slides.add_slide(blank_slide_layout)
            background = slide.background
            fill = background.fill
            fill.solid()
            fill.fore_color.rgb = RGBColor.from_string(theme.bg_color[1:])

            # Tạo một textbox duy nhất chiếm toàn bộ slide
            txBox_full = slide.shapes.add_textbox(Inches(0), Inches(0), slide_width_inches, slide_height_inches)
            tf_full = txBox_full.text_frame
            tf_full.word_wrap = True
            p_full = tf_full.paragraphs[0] # Sửa: Lấy đoạn văn đầu tiên
            # Áp dụng logic tô màu và định dạng
            _apply_lyric_formatting(p_full, slide_text, theme, lyric_size)

        # --- 4. Slide chuyển tiếp ---
        if i < len(songs) - 1:
            slide = prs.slides.add_slide(blank_slide_layout)
            background = slide.background
            fill = background.fill
            fill.solid()
            fill.fore_color.rgb = RGBColor.from_string("000000")

    prs.save(output_path)

def _apply_lyric_formatting(p: 'Paragraph', text: str, theme: Theme, lyric_size: int):
    """Hàm trợ giúp để áp dụng định dạng cho một đoạn văn bản lời bài hát."""
    # Đặt các thuộc tính chung cho cả đoạn văn
    if theme.lyric_alignment == "CENTER":
        p.alignment = PP_ALIGN.CENTER
    elif theme.lyric_alignment == "LEFT":
        p.alignment = PP_ALIGN.LEFT
    elif theme.lyric_alignment == "RIGHT":
        p.alignment = PP_ALIGN.RIGHT
    elif theme.lyric_alignment == "JUSTIFY":
        p.alignment = PP_ALIGN.JUSTIFY

    # Logic tô màu bằng cách thêm các "run"
    stripped_text = text.lstrip()
    found_prefix = None
    for prefix in PREFIXES_TO_HIGHLIGHT:
        if stripped_text.startswith(prefix):
            found_prefix = prefix
            break
    
    if found_prefix:
        run1 = p.add_run()
        run1.text = found_prefix
        font1 = run1.font
        font1.name = theme.title_font_name
        font1.color.rgb = RGBColor.from_string(theme.title_font_color[1:])
        font1.size = Pt(lyric_size)
        font1.bold = theme.lyric_font_bold
        font1.italic = theme.lyric_font_italic
        font1.underline = theme.lyric_font_underline
        
        run2 = p.add_run()
        run2.text = text[len(found_prefix):]
        font2 = run2.font
        font2.name = theme.lyric_font_name
        font2.size = Pt(lyric_size)
        font2.color.rgb = RGBColor.from_string(theme.lyric_font_color[1:])
        font2.bold = theme.lyric_font_bold
        font2.italic = theme.lyric_font_italic
        font2.underline = theme.lyric_font_underline
    else:
        run = p.add_run()
        run.text = text
        font = run.font
        font.name = theme.lyric_font_name
        font.size = Pt(lyric_size)
        font.color.rgb = RGBColor.from_string(theme.lyric_font_color[1:])
        font.bold = theme.lyric_font_bold
        font.italic = theme.lyric_font_italic
        font.underline = theme.lyric_font_underline