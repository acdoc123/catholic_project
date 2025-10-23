from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
from app.models.song_model import Theme, Song

def generate_presentation(songs: list, theme: Theme, output_path: str, overrides: dict):
    """
    Tạo một tệp PowerPoint từ danh sách bài hát và chủ đề.
    `overrides` là một dict chứa các tùy chỉnh font size cho từng song_id.
    """
    prs = Presentation()
    prs.slide_width = theme.slide_width
    prs.slide_height = theme.slide_height
    
    blank_slide_layout = prs.slide_layouts[1] # Layout trống

    for i, song in enumerate(songs):
        # --- Slide Tựa đề ---
        slide = prs.slides.add_slide(blank_slide_layout)
        
        # Thêm nền đen
        background = slide.background
        fill = background.fill
        fill.solid()
        fill.fore_color.rgb = RGBColor.from_string(theme.bg_color[1:])

        # Thêm textbox cho tựa đề
        title_size = overrides.get(song.id, {}).get('title', theme.title_font_size)
        
        # Vị trí và kích thước textbox (điều chỉnh cho phù hợp)
        left = Inches(1)
        top = Inches(1)
        width = prs.slide_width - Inches(2)
        height = Inches(2)
        
        txBox = slide.shapes.add_textbox(left, top, width, height)
        tf = txBox.text_frame
        tf.word_wrap = True
        p = tf.paragraphs
        p.text = song.title
        p.alignment = PP_ALIGN.CENTER
        
        font = p.font
        font.name = theme.title_font_name
        font.size = Pt(title_size)
        font.color.rgb = RGBColor.from_string(theme.title_font_color[1:])
        # Áp dụng style mới
        font.bold = theme.title_font_bold
        font.italic = theme.title_font_italic
        font.underline = theme.title_font_underline

        # --- Các slide Lời bài hát ---
        lyric_size = overrides.get(song.id, {}).get('lyric', theme.lyric_font_size)
        lyrics_chunks = _split_lyrics_into_chunks(song.lyrics) # Hàm chia lời bài hát
        
        for chunk in lyrics_chunks:
            slide = prs.slides.add_slide(blank_slide_layout)
            background = slide.background
            fill = background.fill
            fill.solid()
            fill.fore_color.rgb = RGBColor.from_string(theme.bg_color[1:])

            left = Inches(0.5)
            top = Inches(0.5)
            width = prs.slide_width - Inches(1)
            height = prs.slide_height - Inches(1)

            txBox = slide.shapes.add_textbox(left, top, width, height)
            tf = txBox.text_frame
            tf.word_wrap = True
            p = tf.paragraphs
            p.text = chunk
            
            if theme.lyric_alignment == "CENTER":
                p.alignment = PP_ALIGN.CENTER
            elif theme.lyric_alignment == "LEFT":
                p.alignment = PP_ALIGN.LEFT
            elif theme.lyric_alignment == "RIGHT":
                p.alignment = PP_ALIGN.RIGHT

            font = p.font
            font.name = theme.lyric_font_name
            font.size = Pt(lyric_size)
            font.color.rgb = RGBColor.from_string(theme.lyric_font_color[1:])

            font.bold = theme.lyric_font_bold
            font.italic = theme.lyric_font_italic
            font.underline = theme.lyric_font_underline

        # --- Slide chuyển tiếp (nếu không phải bài hát cuối) ---
        if i < len(songs) - 1:
            slide = prs.slides.add_slide(blank_slide_layout)
            background = slide.background
            fill = background.fill
            fill.solid()
            fill.fore_color.rgb = RGBColor.from_string("000000")

    prs.save(output_path)

def _split_lyrics_into_chunks(lyrics: str, lines_per_slide=6) -> list[str]:
    """Hàm đơn giản để chia lời bài hát thành các đoạn nhỏ."""
    lines = lyrics.strip().split('\n')
    chunks = []
    current_chunk = []
    for line in lines:
        if line.strip() == "" and current_chunk: # Ngắt đoạn khi gặp dòng trống
            chunks.append("\n".join(current_chunk))
            current_chunk = []
        elif len(current_chunk) >= lines_per_slide:
            chunks.append("\n".join(current_chunk))
            current_chunk = [line]
        else:
            current_chunk.append(line)
    
    if current_chunk:
        chunks.append("\n".join(current_chunk))
        
    return chunks if chunks else [""]