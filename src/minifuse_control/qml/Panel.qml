import QtQuick
import QtQuick.Controls

Frame {
    id: root
    padding: 16
    background: Rectangle {
        color: root.palette.base
        radius: 6
        border.color: Qt.alpha(root.palette.windowText, 0.12)
    }
}
