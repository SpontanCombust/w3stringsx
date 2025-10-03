import QtQuick 6.9
import QtQuick.Controls 6.9
import QtQuick.VectorImage 6.9

Item {
  property string imageSource
  property string text
  signal clicked()

  id: root
  width: 140
  height: 140

  Button {
    width: parent.width
    height: parent.height
    contentItem: Column {
      anchors.verticalCenter: parent.verticalCenter
      anchors.verticalCenterOffset: 10
      spacing: 8
      VectorImage {
        source: root.imageSource
        width: 64
        height: 64
        fillMode: Image.PreserveAspectFit
        anchors.horizontalCenter: parent.horizontalCenter
        preferredRendererType: VectorImage.CurveRenderer
      }
      Text {
        text: root.text
        font.pointSize: 10
        width: 120
        wrapMode: Text.WordWrap
        horizontalAlignment: Text.AlignHCenter
        anchors.horizontalCenter: parent.horizontalCenter
      }
    }
    onClicked: {
      root.clicked()
    }
  }
}
