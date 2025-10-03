import QtQuick 6.9
import QtQuick.Controls.Imagine
import QtQuick.Controls 6.9

ApplicationWindow {
  width: 1000
  height: 600
  visible: true
  title: "w3stringsx GUI"

  StackView {
    id: stack
    anchors.fill: parent

    initialItem: MainPage { stack: stack }
  }
}
