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
    readonly property bool compact: height < 740

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: window.compact ? 12 : 20
        spacing: window.compact ? 8 : 14
        RowLayout {
            Layout.fillWidth: true
            Layout.preferredHeight: window.compact ? 36 : 50
            spacing: 16
            ColumnLayout {
                spacing: 0
                Label { text: qsTr("MiniFuse"); font.pixelSize: window.compact ? 22 : 26; font.bold: true }
                Label { text: qsTr("CONTROL CENTER"); visible: !window.compact; font.pixelSize: 10; font.letterSpacing: 2; opacity: 0.55 }
            }
            Item { Layout.fillWidth: true }
            Rectangle {
                Layout.preferredWidth: 6
                Layout.preferredHeight: 6
                radius: 3
                color: window.controller.canWrite ? window.palette.highlight : window.palette.mid
            }
            Label {
                text: window.controller.status
                font.pixelSize: 12
                opacity: 0.75
                Layout.maximumWidth: 350
                elide: Text.ElideRight
                Accessible.role: Accessible.StatusBar
            }
            Button { text: qsTr("Start service"); visible: !window.controller.online; onClicked: window.controller.startService() }
        }
        Rectangle { Layout.fillWidth: true; implicitHeight: 1; color: Qt.alpha(window.palette.windowText, 0.12) }
        TabBar {
            id: tabs
            objectName: "workspaceTabs"
            Layout.preferredWidth: 470
            spacing: 4
            background: null
            NavigationTab { implicitHeight: window.compact ? 32 : 36; text: qsTr("Mixer and routing") }
            NavigationTab { implicitHeight: window.compact ? 32 : 36; text: qsTr("Presets") }
            NavigationTab { implicitHeight: window.compact ? 32 : 36; text: qsTr("Device and desktop") }
        }
        StackLayout {
            objectName: "workspacePages"
            clip: true
            Layout.minimumHeight: 0
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentIndex: tabs.currentIndex
            MixerPage { controller: window.controller; compact: window.compact }
            PresetsPage { controller: window.controller }
            DevicePage { controller: window.controller }
        }
        Panel {
            objectName: "feedbackPanel"
            Layout.fillWidth: true
            Layout.minimumHeight: window.compact ? 42 : 54
            Layout.preferredHeight: window.compact ? 42 : 54
            Layout.maximumHeight: window.compact ? 42 : 54
            padding: window.compact ? 6 : 10
            RowLayout {
                anchors.fill: parent
                spacing: 12
                Label {
                    text: window.controller.uncertain ? qsTr("REVIEW") : window.controller.liveActive ? qsTr("ADJUSTING") : window.controller.busy ? qsTr("VERIFYING") : qsTr("STATUS")
                    font.pixelSize: 10
                    font.bold: true
                    font.letterSpacing: 1
                    color: window.controller.uncertain ? window.palette.highlight : window.palette.windowText
                    opacity: 0.65
                    Layout.preferredWidth: 82
                }
                ScrollView {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    contentWidth: availableWidth
                    TextArea {
                        objectName: "feedbackText"
                        text: window.controller.message || (window.controller.liveActive ? qsTr("Adjusting…") : window.controller.busy ? qsTr("Waiting for device verification…") : window.controller.canWrite ? qsTr("Ready · Changes apply automatically") : window.controller.status)
                        readOnly: true
                        selectByMouse: true
                        wrapMode: TextEdit.Wrap
                        background: null
                        padding: 0
                        font.pixelSize: 12
                        Accessible.role: Accessible.StatusBar
                        Accessible.name: text
                    }
                }
                Button { text: qsTr("Refresh and acknowledge"); visible: window.controller.uncertain; enabled: window.controller.online && window.controller.mixes.length > 0; onClicked: window.controller.acknowledge() }
            }
        }
    }
    onClosing: { window.controller.cancelControl(); window.controller.discardEdits() }
}
