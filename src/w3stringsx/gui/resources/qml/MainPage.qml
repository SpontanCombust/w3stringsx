import QtQuick 6.9
import QtQuick.Controls 6.9
import QtQuick.Shapes 6.9

Item {
  property StackView stack

  id: root
  anchors.fill: parent

  Column {
    anchors.centerIn: parent
    spacing: 20

    Row {
      anchors.horizontalCenter: parent.horizontalCenter 
      spacing: 40

      MainPageButton {
        imageSource: "qrc:/icons/file-lock.svg"
        text: "ENCODE \n CSV to w3strings"
        onClicked: {

        }
      }
      MainPageButton {
        imageSource: "qrc:/icons/file-lock-open.svg"
        text: "DECODE \n w3strings to CSV"
        onClicked: {

        }
      }
      MainPageButton {
        imageSource: "qrc:/icons/file-find.svg"
        text: "FIND \n string keys"
        onClicked: {

        }
      }
    }
    Text {
      anchors.horizontalCenter: parent.horizontalCenter
      text: "OR"
      font.pointSize: 14
      font.bold: true
    }
    Rectangle {
      anchors.horizontalCenter: parent.horizontalCenter 
      width: 400
      height: 100
      color: "transparent"

      Shape {
        id: fileDropBorder
        anchors.fill: parent

        ShapePath {
          strokeColor: "gray"
          strokeWidth: 2
          strokeStyle: ShapePath.DashLine
          startX: 0; startY: 0
          PathLine { x: fileDropBorder.parent.width; y: 0 }
          PathLine { x: fileDropBorder.parent.width; y: fileDropBorder.parent.height }
          PathLine { x: 0; y: fileDropBorder.parent.height }
          PathLine { x: 0; y: 0 }
        }
      }
      Text {
        anchors.centerIn: parent
        text: "Drag and drop a file here \n to deduce action automatically"
        font.pointSize: 12
        horizontalAlignment: Text.AlignHCenter
      }
      DropArea {
        anchors.fill: parent
        onDropped: (drop) => {
          // console.log(JSON.stringify(drop))
        }
      }
    }
  }
}