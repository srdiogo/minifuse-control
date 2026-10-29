pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Frame {
    id: root
    objectName: "inputControls"
    required property var controller
    Layout.fillWidth: true
    RowLayout {
        anchors.fill: parent
        spacing: 12
        Label { text: qsTr("INPUTS"); font.bold: true }
        Repeater {
            model: [
                {target: "inst1", caption: qsTr("Input 1 · INST"), description: qsTr("Instrument mode for input 1")},
                {target: "inst2", caption: qsTr("Input 2 · INST"), description: qsTr("Instrument mode for input 2")},
                {target: "phantom_power", caption: qsTr("+48 V · Inputs 1–2"), description: qsTr("Shared phantom power for inputs 1 and 2")}
            ]
            delegate: Button {
                required property var modelData
                property var confirmed: root.controller.inputs[modelData.target]
                objectName: "inputSwitch-" + modelData.target
                Layout.preferredWidth: 180
                text: modelData.caption + (typeof confirmed === "boolean" ? (confirmed ? qsTr(" · On") : qsTr(" · Off")) : "")
                highlighted: confirmed === true
                enabled: root.controller.canWriteInputs && typeof confirmed === "boolean"
                Accessible.role: Accessible.CheckBox
                Accessible.checkable: true
                Accessible.checked: confirmed === true
                Accessible.name: modelData.description
                ToolTip.visible: hovered
                ToolTip.text: modelData.description + (typeof confirmed === "boolean" ? (confirmed ? qsTr(" · On") : qsTr(" · Off")) : qsTr(" · Readback unavailable"))
                onClicked: root.controller.setInputSwitch(modelData.target, !confirmed)
            }
        }
        Item { Layout.fillWidth: true }
        Label {
            text: root.controller.capabilities.switch_readback ? (root.controller.capabilities.input_switches ? qsTr("Device state") : qsTr("Read-only · update module")) : qsTr("Unavailable")
            opacity: 0.65
            font.pixelSize: 12
            Layout.fillWidth: true
            horizontalAlignment: Text.AlignRight
            wrapMode: Text.Wrap
        }
    }
}
