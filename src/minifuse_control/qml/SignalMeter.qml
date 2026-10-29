import QtQuick
import QtQuick.Controls

Control {
    id: root
    objectName: "signalMeter"
    property bool available: false
    property var peakDbfs: null
    property string channelName: ""
    property real floorDbfs: -96
    readonly property real fraction: available && peakDbfs !== null ? Math.max(0, Math.min(1, (peakDbfs - floorDbfs) / -floorDbfs)) : 0
    readonly property string readout: !available ? qsTr("Unavailable") : peakDbfs === null ? "−∞ dBFS" : Number(peakDbfs).toFixed(1) + " dBFS"
    implicitWidth: 9
    implicitHeight: 130
    hoverEnabled: true
    Accessible.role: Accessible.ProgressBar
    Accessible.name: channelName + " peak · " + readout
    ToolTip.visible: hovered
    ToolTip.text: channelName + " peak · " + readout + qsTr(" · Scale −96 to 0 dBFS")
    background: Rectangle { color: Qt.alpha(root.palette.windowText, 0.04); border.color: Qt.alpha(root.palette.windowText, 0.16); radius: 2 }
    contentItem: Item {
        Rectangle {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            height: root.fraction * parent.height
            color: root.palette.highlight
            radius: 1
        }
        Rectangle { width: parent.width; height: 1; y: parent.height / 2; color: Qt.alpha(root.palette.windowText, 0.15) }
    }
}
