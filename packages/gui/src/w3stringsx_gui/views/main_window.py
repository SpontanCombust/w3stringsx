from typing import cast

from PySide6.QtQuick import QQuickWindow
from PySide6.QtQml import QQmlApplicationEngine, QQmlContext, QQmlComponent

from w3stringsx_lib.logging import get_logger


logger = get_logger()


class MainWindow:
    __comp: QQmlComponent
    __view: QQuickWindow

    def __init__(self, engine: QQmlApplicationEngine):
        ctx = QQmlContext(engine)
        self.__comp = QQmlComponent(engine, "qrc:/qml/MainWindow.qml")
        view = self.__comp.create(ctx)
        if self.__comp.isError():
            logger.error(self.__comp.errorString())
        self.__view = cast(QQuickWindow, view)

    def show(self):
        self.__view.show()