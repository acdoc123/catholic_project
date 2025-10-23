import sys
import os

def resource_path(relative_path: str) -> str:
    """
    Lấy đường dẫn tuyệt đối đến tài nguyên, hoạt động cho cả môi trường
    phát triển và khi đã được đóng gói bằng PyInstaller.
    """
    try:
        # PyInstaller tạo một thư mục tạm thời và lưu đường dẫn trong _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # Nếu không ở trong môi trường PyInstaller, sử dụng đường dẫn thông thường
        # Giả định rằng thư mục gốc của dự án là thư mục cha của thư mục 'src'
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

    return os.path.join(base_path, relative_path)