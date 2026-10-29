pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts

ColumnLayout {
    id: root
    required property var controller
    spacing: 14
    Label { text: qsTr("Host presets"); font.pixelSize: 20; font.bold: true }
    Label { text: qsTr("Save mixer snapshots on this computer. Compare changes before restoring them to the interface."); wrapMode: Text.Wrap; Layout.fillWidth: true }
    RowLayout {
        Layout.fillWidth: true
        TextField { id: name; Layout.fillWidth: true; placeholderText: qsTr("New preset name"); maximumLength: 128; Accessible.name: qsTr("New preset name") }
        Button { text: qsTr("Save current state"); enabled: root.controller.canWrite && name.text.trim().length > 0; onClicked: root.controller.savePreset(name.text.trim()) }
        Button { text: qsTr("Import snapshot…"); enabled: root.controller.online; onClicked: importing.open() }
        Button { text: qsTr("Refresh list"); enabled: root.controller.online; onClicked: root.controller.loadPresets() }
    }
    RowLayout {
        Layout.fillWidth: true
        Layout.fillHeight: true
        Panel {
            Layout.preferredWidth: root.width < 1000 ? 190 : 250
            Layout.fillHeight: true
            ScrollView {
                anchors.fill: parent
                ColumnLayout {
                    width: parent.width
                    Repeater {
                        model: root.controller.presets
                        delegate: Button {
                            required property var modelData
                            text: modelData.name
                            Layout.fillWidth: true
                            enabled: root.controller.online
                            onClicked: root.controller.inspectPreset(modelData.preset_id)
                        }
                    }
                    Label { visible: root.controller.presets.length === 0; text: qsTr("No saved presets"); opacity: 0.7 }
                }
            }
        }
        Panel {
            Layout.fillWidth: true
            Layout.fillHeight: true
            ColumnLayout {
                anchors.fill: parent
                spacing: 12
                Label { text: root.controller.preview.plan_id ? qsTr("Restore preview") : qsTr("Snapshot inspection"); font.pixelSize: 18; font.bold: true }
                Label {
                    Layout.fillWidth: true
                    wrapMode: Text.Wrap
                    text: root.controller.preview.summary ? qsTr("Changes in this preview: ") + root.controller.previewRows.length : qsTr("Select or import a snapshot. Inspection does not write to the interface.")
                }
                ComboBox { id: scope; model: [qsTr("All mixes"), "out12", "out34", "loopback"]; Accessible.name: qsTr("Restore scope") }
                Flow {
                    Layout.fillWidth: true
                    spacing: 8
                    Button { text: qsTr("Compare / preview restore"); enabled: root.controller.canWrite && Object.keys(root.controller.preview).length > 0; onClicked: root.controller.previewRestore(scope.currentIndex === 0 ? "" : scope.currentText) }
                    Button { text: qsTr("Apply this preview"); enabled: root.controller.canWrite && !!root.controller.preview.plan_id; onClicked: root.controller.applyRestore() }
                    Button { text: qsTr("Export…"); enabled: Object.keys(root.controller.preview).length > 0; onClicked: exporting.open() }
                }
                Label { text: qsTr("Only selected mixer fields are restored. Removing a source mutes it and clears solo. Host presets do not confirm saving to device memory."); Layout.fillWidth: true; wrapMode: Text.Wrap; font.pixelSize: 11; opacity: 0.65 }
                ListView {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    model: root.controller.previewRows
                    delegate: RowLayout {
                        id: changeRow
                        required property var modelData
                        width: ListView.view.width
                        Label { text: changeRow.modelData.field; Layout.fillWidth: true; elide: Text.ElideRight }
                        Label { text: changeRow.modelData.before; Layout.preferredWidth: 85; font.family: "monospace" }
                        Label { text: "→ " + changeRow.modelData.after; Layout.preferredWidth: 100; font.family: "monospace" }
                    }
                }
            }
        }
    }
    FileDialog { id: importing; title: qsTr("Import a host snapshot"); nameFilters: [qsTr("JSON snapshots (*.json)")]; onAccepted: root.controller.importSnapshot(selectedFile) }
    FileDialog { id: exporting; title: qsTr("Export a new snapshot file"); fileMode: FileDialog.SaveFile; nameFilters: [qsTr("JSON snapshots (*.json)")]; onAccepted: root.controller.exportSnapshot(selectedFile) }
}
