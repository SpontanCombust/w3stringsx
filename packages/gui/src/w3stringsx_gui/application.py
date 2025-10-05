import w3stringsx_gui.resources # type: ignore # noqa: F401

import os
import sys
import logging

from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtWidgets import QApplication

from w3stringsx_lib.logging import init_logger
from w3stringsx_gui.views.main_window import MainWindow

def application() -> int:
    # path outside of the .pyzw archive
    W3STRINGSX_APP_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    init_logger(logging.INFO, W3STRINGSX_APP_DIR)

    app = QApplication(sys.argv)
    engine = QQmlApplicationEngine()

    window = MainWindow(engine)
    window.show()

    return app.exec()