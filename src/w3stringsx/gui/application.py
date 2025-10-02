import w3stringsx.gui.resources # type: ignore

import sys
import logging

from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtWidgets import QApplication

from w3stringsx.lib.logging import init_logger
from w3stringsx.gui.views.main_window import MainWindow

def application() -> int:
    init_logger(logging.INFO)

    app = QApplication(sys.argv)
    engine = QQmlApplicationEngine()

    window = MainWindow(engine)
    window.show()

    return app.exec()