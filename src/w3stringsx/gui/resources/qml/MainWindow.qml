import QtQuick 2.15
import QtQuick.Controls 2.15

ApplicationWindow {
    width: 800
    height: 400
    visible: true
    title: "w3stringsx GUI"

    StackView {
        id: stack
        anchors.fill: parent

        // initialItem: MainPage { stack: stack }
    }
}
