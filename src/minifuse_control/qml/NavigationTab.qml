import QtQuick
import QtQuick.Controls

TabButton {
    id: root
    implicitHeight: 36
    padding: 8
    focusPolicy: Qt.StrongFocus
    contentItem: Label {
        text: root.text
        font.bold: root.checked
        font.pixelSize: 12
        color: root.checked ? root.palette.highlight : root.palette.windowText
        opacity: root.enabled ? (root.checked ? 1 : 0.72) : 0.4
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }
    background: Rectangle {
        radius: 4
        color: root.checked ? Qt.alpha(root.palette.highlight, 0.10) : root.hovered ? Qt.alpha(root.palette.windowText, 0.05) : "transparent"
        border.color: root.checked ? Qt.alpha(root.palette.highlight, 0.55) : root.visualFocus ? root.palette.windowText : "transparent"
        Rectangle {
            anchors.bottom: parent.bottom
            anchors.horizontalCenter: parent.horizontalCenter
            width: parent.width - 20
            height: 2
            visible: root.checked
            color: root.palette.highlight
        }
    }
}
