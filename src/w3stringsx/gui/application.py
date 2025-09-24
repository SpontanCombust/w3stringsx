import sys
from PySide6.QtWidgets import QApplication

from w3stringsx.gui.views.main_window import MainWindow

def application() -> int:
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    return app.exec()