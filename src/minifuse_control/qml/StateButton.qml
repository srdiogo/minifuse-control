import QtQuick
import QtQuick.Controls

Button {
    id: root
    property bool active: false
    property string description: text
    highlighted: active
    checked: active
    focusPolicy: Qt.StrongFocus
    hoverEnabled: true
    implicitHeight: 28
    implicitWidth: 32
    padding: 5
    Accessible.role: Accessible.CheckBox
    Accessible.checkable: true
    Accessible.checked: active
    Accessible.name: description
    ToolTip.visible: hovered
    ToolTip.text: description + (active ? qsTr(" · On") : qsTr(" · Off"))
    contentItem: Label {
        text: root.text
        font.pixelSize: 11
        font.bold: root.active
        color: root.active ? root.palette.highlight : root.palette.windowText
        opacity: root.enabled ? (root.active ? 1 : 0.65) : 0.4
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }
    background: Rectangle {
        radius: 3
        color: root.active ? Qt.alpha(root.palette.highlight, 0.12) : root.hovered ? Qt.alpha(root.palette.windowText, 0.06) : "transparent"
        border.color: root.active ? root.palette.highlight : Qt.alpha(root.palette.windowText, root.visualFocus ? 0.65 : 0.20)
        Rectangle {
            anchors.bottom: parent.bottom
            anchors.horizontalCenter: parent.horizontalCenter
            height: 2
            width: parent.width - 10
            color: root.palette.highlight
            visible: root.active
        }
    }
}
