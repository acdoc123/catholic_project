# src/utils/slide_layout_engine.py

from PySide6.QtGui import QFont, QFontMetrics
from PySide6.QtCore import QRectF, Qt

def split_lyrics_into_slides(lyrics: str, font: QFont, bounding_box: QRectF) -> list[str]:
    """
    Chia lời bài hát thành các slide dựa trên kích thước font và một hộp giới hạn (bounding box).
    """
    if not lyrics:
        return [""]

    metrics = QFontMetrics(font)
    lines = lyrics.strip().split('\n')
    
    slides = []
    current_slide_lines = []
    
    for line in lines:
        test_lines = current_slide_lines + [line]
        test_text = "\n".join(test_lines)
        
        # <<< SỬA LỖI Ở ĐÂY: Chuyển đổi QRectF thành QRect bằng.toRect() >>>
        required_rect = metrics.boundingRect(bounding_box.toRect(), Qt.TextFlag.TextWordWrap, test_text)
        
        if required_rect.height() > bounding_box.height() and current_slide_lines:
            slides.append("\n".join(current_slide_lines))
            current_slide_lines = [line]
        else:
            current_slide_lines.append(line)
            
    if current_slide_lines:
        slides.append("\n".join(current_slide_lines))
        
    return slides if slides else [""]