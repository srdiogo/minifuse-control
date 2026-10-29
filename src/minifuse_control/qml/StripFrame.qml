import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Frame {
    id: root
    property alias headerContent: header.data
    property alias controlContent: control.data
    property bool master: false
    property bool compact: false
    Layout.minimumWidth: 102
    Layout.preferredWidth: 102
    Layout.fillHeight: true
    padding: 8
    background: Rectangle {
        radius: 5
        color: root.master ? Qt.tint(root.palette.base, Qt.alpha(root.palette.highlight, 0.05)) : root.palette.base
        border.color: Qt.alpha(root.master ? root.palette.highlight : root.palette.windowText, root.master ? 0.35 : 0.09)
    }
    contentItem: ColumnLayout {
        spacing: 8
        Item {
            id: header
            Layout.fillWidth: true
            Layout.minimumHeight: root.compact ? 82 : 126
            Layout.preferredHeight: root.compact ? 82 : 126
            Layout.maximumHeight: root.compact ? 82 : 126
        }
        Rectangle { Layout.fillWidth: true; implicitHeight: 1; color: Qt.alpha(root.palette.windowText, 0.09) }
        Item {
            id: control
            Layout.fillWidth: true
            Layout.fillHeight: true
        }
    }
}
