import sys
import os
from PySide6.QtWidgets import QApplication

from app.models.database_model import DatabaseModel
from app.views.main_window import MainWindow
from app.controllers.main_controller import MainController
from utils.resource_manager import resource_path
# from assets.styles.styles import STYLESHEET

def main():
    """
    Hàm chính để khởi tạo và chạy ứng dụng Lyric Presenter.
    """
    # Đảm bảo các thư mục cần thiết tồn tại
    data_dir = resource_path('data')
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    app = QApplication(sys.argv)
    try:
        # Sử dụng resource_path để đảm bảo đường dẫn đúng cả khi đã đóng gói
        qss_file_path = resource_path('src/assets/styles/style.qss')
        with open(qss_file_path, "r", encoding="utf-8") as f:
            style = f.read()
            app.setStyleSheet(style)
    except FileNotFoundError:
        print("Cảnh báo: Không tìm thấy tệp style.qss. Ứng dụng sẽ dùng giao diện mặc định.")

    # app.setStyleSheet(STYLESHEET)
    # Khởi tạo các thành phần theo kiến trúc MVC
    # 1. Model: Quản lý dữ liệu
    db_path = resource_path('data/lyrics.db')
    database_model = DatabaseModel(db_path)

    # 2. View: Giao diện người dùng
    main_view = MainWindow()

    # 3. Controller: Liên kết Model và View
    main_controller = MainController(model=database_model, view=main_view)

    main_view.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()