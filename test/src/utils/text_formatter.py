# src/utils/text_formatter.py

import re

# Các tiền tố cần được tô màu
PREFIXES_TO_HIGHLIGHT = ["ĐK.", "1"]
# Sắp xếp để các tiền tố dài hơn được kiểm tra trước (ví dụ: "ĐK:" trước "ĐK")
PREFIXES_TO_HIGHLIGHT.sort(key=len, reverse=True)

def format_lyrics_for_display(text: str, color: str) -> str:
    """
    Định dạng lời bài hát bằng HTML để tô màu các tiền tố.
    """
    if not text:
        return ""
        
    lines = text.split('\n')
    formatted_lines = []
    
    for line in lines:
        stripped_line = line.strip()
        found_prefix = None
        for prefix in PREFIXES_TO_HIGHLIGHT:
            if stripped_line.startswith(prefix):
                found_prefix = prefix
                break
        
        if found_prefix:
            # Tách tiền tố và phần còn lại
            rest_of_line = line[len(found_prefix):]
            # Bọc tiền tố trong thẻ font HTML
            formatted_line = f"<font color='{color}'>{found_prefix}</font>{rest_of_line}"
            formatted_lines.append(formatted_line)
        else:
            formatted_lines.append(line)
            
    # Nối các dòng lại bằng thẻ <br> của HTML
    return "<br>".join(formatted_lines)