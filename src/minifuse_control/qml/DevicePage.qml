import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ScrollView {
    id: root
    required property var controller
    clip: true
    contentWidth: availableWidth
    ColumnLayout {
        width: root.availableWidth
        spacing: 16
        Label { text: qsTr("Device and desktop"); font.pixelSize: 20; font.bold: true }
        RowLayout {
            Layout.fillWidth: true
            spacing: 16
            Panel {
                Layout.fillWidth: true
                Layout.alignment: Qt.AlignTop
                ColumnLayout {
                    anchors.fill: parent
                    spacing: 12
                    Label { text: qsTr("DEVICE SUPPORT"); font.pixelSize: 10; font.letterSpacing: 1; opacity: 0.55 }
                    Label { text: qsTr("MiniFuse 4"); font.pixelSize: 18; font.bold: true }
                    Label { text: qsTr("Mixer, output routes, host presets, INST and shared +48 V follow confirmed device state. Input writes and signal meters require matching module features."); wrapMode: Text.Wrap; Layout.fillWidth: true }
                    Label { text: qsTr("Mix meters follow master gain, before routing. Direct USB can bypass that mix. Input trims are read-only."); wrapMode: Text.Wrap; Layout.fillWidth: true; opacity: 0.65; font.pixelSize: 12 }
                    Label { text: qsTr("MiniFuse 1 and 2 retain their established CLI controls. This application does not infer their mixer layouts."); wrapMode: Text.Wrap; Layout.fillWidth: true; opacity: 0.65; font.pixelSize: 12 }
                }
            }
            Panel {
                Layout.fillWidth: true
                Layout.alignment: Qt.AlignTop
                ColumnLayout {
                    anchors.fill: parent
                    spacing: 12
                    Label { text: qsTr("DESKTOP ACTIVATION"); font.pixelSize: 10; font.letterSpacing: 1; opacity: 0.55 }
                    Label { text: qsTr("Physical logo button"); font.pixelSize: 18; font.bold: true }
                    Label { text: qsTr("Choose the target for a validated button event."); Layout.fillWidth: true; wrapMode: Text.Wrap }
                    ComboBox {
                        model: [qsTr("Disabled"), qsTr("Application"), qsTr("Omarchy panel")]
                        property var targets: ["disabled", "application", "omarchy_panel"]
                        currentIndex: targets.indexOf(root.controller.activationTarget)
                        Accessible.name: qsTr("Physical-button activation preference")
                        onActivated: root.controller.setActivationTarget(targets[currentIndex])
                    }
                    Label { text: qsTr("Logo-button events remain unavailable. The optional agent requires a validated event and explicit session startup. This preference does not install startup entries or enable unsupported hardware."); wrapMode: Text.Wrap; Layout.fillWidth: true; opacity: 0.65; font.pixelSize: 12 }
                }
            }
        }
        Panel {
            Layout.fillWidth: true
            ColumnLayout {
                anchors.fill: parent
                spacing: 12
                RowLayout {
                    Layout.fillWidth: true
                    CheckBox { id: diagnostics; text: qsTr("Show local diagnostics") }
                    Item { Layout.fillWidth: true }
                    Button { visible: diagnostics.checked; text: qsTr("Refresh device state"); enabled: !root.controller.busy; onClicked: root.controller.refresh() }
                }
                TextArea { visible: diagnostics.checked; text: root.controller.diagnostics; readOnly: true; selectByMouse: true; wrapMode: TextEdit.WrapAnywhere; font.family: "monospace"; font.pixelSize: 11; Layout.fillWidth: true; Accessible.name: qsTr("Device and operation diagnostics") }
            }
        }
        Item { Layout.fillHeight: true }
    }
}
