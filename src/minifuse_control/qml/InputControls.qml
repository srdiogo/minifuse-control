pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Panel {
    id: root
    objectName: "inputControls"
    required property var controller
    property bool compact: false
    Layout.fillWidth: true
    padding: compact ? 6 : 10
    implicitHeight: compact ? 42 : 50
    RowLayout {
        anchors.fill: parent
        spacing: 12
        Label { text: qsTr("INPUT MODE"); font.pixelSize: 9; font.letterSpacing: 1; opacity: 0.55; Layout.preferredWidth: 82 }
        Repeater {
            model: [
                {target: "inst1", caption: qsTr("INST 1"), description: qsTr("Instrument mode for input 1")},
                {target: "inst2", caption: qsTr("INST 2"), description: qsTr("Instrument mode for input 2")},
                {target: "phantom_power", caption: qsTr("+48 V · 1–2"), description: qsTr("Shared phantom power for inputs 1 and 2")}
            ]
            delegate: StateButton {
                required property var modelData
                property var confirmed: root.controller.inputs[modelData.target]
                objectName: "inputSwitch-" + modelData.target
                Layout.preferredWidth: modelData.target === "phantom_power" ? 120 : 82
                text: modelData.caption
                active: confirmed === true
                enabled: root.controller.canWriteInputs && typeof confirmed === "boolean"
                description: modelData.description
                ToolTip.text: modelData.description + (typeof confirmed === "boolean" ? (confirmed ? qsTr(" · On") : qsTr(" · Off")) : qsTr(" · Readback unavailable"))
                onClicked: root.controller.setInputSwitch(modelData.target, !confirmed)
            }
        }
        Item { Layout.fillWidth: true }
        Label {
            text: root.controller.capabilities.switch_readback ? (root.controller.capabilities.input_switches ? qsTr("Confirmed device state") : qsTr("Read-only · update module")) : qsTr("Unavailable")
            opacity: 0.5
            font.pixelSize: 10
            horizontalAlignment: Text.AlignRight
        }
    }
}
