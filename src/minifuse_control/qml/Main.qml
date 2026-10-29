import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
    id: window
    width: 1280
    height: 820
    minimumWidth: 840
    minimumHeight: 640
    visible: true
    title: qsTr("MiniFuse Control")
    color: palette.window
    required property var controller

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 22
        spacing: 16
        RowLayout {
            ColumnLayout {
                Label { text: qsTr("MINIFUSE CONTROL"); font.pixelSize: 23; font.bold: true; font.letterSpacing: 2 }
                Label { text: window.controller.status; opacity: 0.75; Accessible.role: Accessible.StatusBar }
            }
            Item { Layout.fillWidth: true }
            BusyIndicator { running: window.controller.busy; visible: running; Layout.preferredWidth: 32; Layout.preferredHeight: 32 }
            Button { text: qsTr("Start service"); visible: !window.controller.online; onClicked: window.controller.startService() }
        }
        Frame {
            objectName: "feedbackPanel"
            Layout.fillWidth: true
            Layout.minimumHeight: 64
            Layout.preferredHeight: 64
            Layout.maximumHeight: 64
            RowLayout {
                anchors.fill: parent
                ScrollView {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    contentWidth: availableWidth
                    TextArea {
                        objectName: "feedbackText"
                        text: window.controller.message || (window.controller.liveActive ? qsTr("Adjusting…") : window.controller.busy ? qsTr("Waiting for device verification…") : window.controller.canWrite ? qsTr("Ready") : window.controller.status)
                        readOnly: true
                        selectByMouse: true
                        wrapMode: TextEdit.Wrap
                        background: null
                        padding: 0
                        Accessible.role: Accessible.StatusBar
                        Accessible.name: text
                    }
                }
                Button { text: qsTr("Refresh and acknowledge"); visible: window.controller.uncertain; enabled: window.controller.online && window.controller.mixes.length > 0; onClicked: window.controller.acknowledge() }
            }
        }
        TabBar {
            id: tabs
            objectName: "workspaceTabs"
            Layout.preferredWidth: 530
            TabButton { text: qsTr("Mixer and routing") }
            TabButton { text: qsTr("Presets") }
            TabButton { text: qsTr("Device and desktop") }
        }
        StackLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentIndex: tabs.currentIndex
            MixerPage { controller: window.controller }
            PresetsPage { controller: window.controller }
            ScrollView {
                ColumnLayout {
                    width: parent.width
                    spacing: 18
                    Label { text: qsTr("Device capabilities"); font.pixelSize: 24; font.bold: true }
                    Label { text: qsTr("MiniFuse 4 mixer, routes and host snapshots are available with the matching service/module. MiniFuse 1/2 retain their established CLI toggles."); wrapMode: Text.Wrap; Layout.fillWidth: true }
                    Label { text: qsTr("INST / +48 V readback, signal meters and physical-button events are unavailable until validated. Input trims are read-only."); wrapMode: Text.Wrap; Layout.fillWidth: true }
                    Label { text: qsTr("Physical-button activation target"); font.bold: true }
                    ComboBox {
                        model: [qsTr("Disabled"), qsTr("Application"), qsTr("Omarchy panel")]
                        property var targets: ["disabled", "application", "omarchy_panel"]
                        currentIndex: targets.indexOf(window.controller.activationTarget)
                        Accessible.name: qsTr("Physical-button activation preference")
                        onActivated: window.controller.setActivationTarget(targets[currentIndex])
                    }
                    Label { text: qsTr("The optional agent requires a validated backend event and explicit session startup. Setting a preference does not enable unsupported hardware events or install startup entries."); wrapMode: Text.Wrap; Layout.fillWidth: true }
                    CheckBox { id: diagnostics; text: qsTr("Show local diagnostics") }
                    Button { visible: diagnostics.checked; text: qsTr("Refresh device state"); enabled: !window.controller.busy; onClicked: window.controller.refresh() }
                    TextArea { visible: diagnostics.checked; text: window.controller.diagnostics; readOnly: true; font.family: "monospace"; Layout.fillWidth: true; Accessible.name: qsTr("Device and operation diagnostics") }
                }
            }
        }
    }
    onClosing: { window.controller.cancelControl(); window.controller.discardEdits() }
}
