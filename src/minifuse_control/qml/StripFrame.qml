import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Frame {
    id: root
    property alias headerContent: header.data
    property alias controlContent: control.data
    property alias footerContent: footer.data
    Layout.preferredWidth: 148
    Layout.fillHeight: true
    padding: 12

    contentItem: ColumnLayout {
        spacing: 10
        Item {
            id: header
            Layout.fillWidth: true
            Layout.minimumHeight: 64
            Layout.preferredHeight: 64
            Layout.maximumHeight: 64
        }
        Item {
            id: control
            Layout.fillWidth: true
            Layout.fillHeight: true
        }
        Item {
            id: footer
            Layout.fillWidth: true
            Layout.minimumHeight: 104
            Layout.preferredHeight: 104
            Layout.maximumHeight: 104
        }
    }
}
