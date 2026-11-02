import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ScrollView {
    id: root
    objectName: "modelPage"
    required property var controller
    property bool compact: false
    clip: true
    contentWidth: availableWidth
    ColumnLayout {
        width: root.availableWidth
        spacing: 16
        Label { visible: root.controller.panelLayout !== "loopback_mixer"; text: root.controller.modelName; font.pixelSize: 22; font.bold: true }
        Label {
            text: root.controller.panelLayout === "initialization" ? qsTr("Interface initialization mode") : (root.controller.panelLayout === "loopback_mixer" ? qsTr("Hardware loopback mixer · Firmware %1 · Experimental").arg(root.controller.firmwareInfo.version || qsTr("unknown")) : qsTr("Inputs and direct monitoring"))
            font.pixelSize: 14
            opacity: 0.7
        }
        Panel {
            Layout.fillWidth: true
            visible: root.controller.panelLayout !== "loopback_mixer"
            ColumnLayout {
                anchors.fill: parent
                spacing: 10
                Label { text: qsTr("DEVICE STATUS"); font.pixelSize: 10; font.letterSpacing: 1; opacity: 0.55 }
                Label {
                    objectName: "modelValidationStatus"
                    text: root.controller.panelLayout === "loopback_mixer" ? qsTr("Experimental controls · firmware %1 · hardware acceptance pending").arg(root.controller.firmwareInfo.version || qsTr("unknown")) : root.controller.panelLayout === "initialization" ? qsTr("Audio controls are unavailable in this USB mode. Device mode and firmware are not changed by this application.") : (root.controller.canWriteInputs ? qsTr("Experimental controls ready for hardware testing. Check the interface LEDs and monitoring behavior before regular use.") : qsTr("Hardware validation is pending. Controls require an explicitly enabled test session with confirmed device state."))
                    Layout.fillWidth: true
                    wrapMode: Text.Wrap
                }
            }
        }
        InputControls {
            Layout.fillWidth: true
            visible: root.controller.panelLayout !== "initialization"
            controller: root.controller
            compact: root.compact
        }
        Panel {
            Layout.fillWidth: true
            visible: root.controller.panelLayout !== "initialization" && root.controller.panelLayout !== "loopback_mixer"
            ColumnLayout {
                anchors.fill: parent
                spacing: 10
                Label { text: qsTr("MODEL FEATURES"); font.pixelSize: 10; font.letterSpacing: 1; opacity: 0.55 }
                Label {
                    text: qsTr("%1 physical inputs · %2 physical outputs").arg(root.controller.modelProfile.analog_inputs || 0).arg(root.controller.modelProfile.analog_outputs || 0)
                    Layout.fillWidth: true
                    wrapMode: Text.Wrap
                }
                Label {
                    text: qsTr("Input gain is adjusted with the interface's physical knobs. MiniFuse 4 mixer routes and meters are not used for this model.")
                    Layout.fillWidth: true
                    wrapMode: Text.Wrap
                    opacity: 0.7
                }
                Label {
                    visible: root.controller.modelProfile.id === "mf2_otg"
                    text: qsTr("OTG routing requires its own verified protocol and is not inferred from the MiniFuse 2 or 4.")
                    Layout.fillWidth: true
                    wrapMode: Text.Wrap
                    opacity: 0.7
                }
            }
        }
        LoopbackPage {
            Layout.fillWidth: true
            visible: root.controller.panelLayout === "loopback_mixer"
            controller: root.controller
            compact: root.compact
        }
        Label {
            visible: root.controller.panelLayout !== "loopback_mixer" && root.controller.panelLayout !== "mf4_mixer" && root.controller.panelLayout !== "initialization"
            text: root.controller.firmwareInfo.version ? (root.controller.firmwareInfo.loopback_compatible ? qsTr("Firmware %1 · Loopback requires a matching module and an explicitly enabled test session.").arg(root.controller.firmwareInfo.version) : qsTr("Firmware %1 is outside the experimental loopback family %2.").arg(root.controller.firmwareInfo.version).arg(root.controller.firmwareInfo.required_family || qsTr("unknown"))) : qsTr("Firmware version could not be confirmed. Loopback controls remain unavailable.")
            Layout.fillWidth: true
            wrapMode: Text.Wrap
            opacity: 0.65
        }
        Item { Layout.fillHeight: true }
    }
}
