import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

StripFrame {
    id: root
    required property var channel
    required property string mixName
    required property var controller
    property bool panDirty: false
    property bool panConflict: false
    property real panPreview: 0.5
    property string editRevision: ""
    objectName: "sourceStrip-" + channel.channel
    enabled: controller.online
    property string levelKey: "channel_level:" + mixName + ":" + channel.channel
    property string panKey: "channel_pan:" + mixName + ":" + channel.channel

    onMixNameChanged: { if (controller && controller.liveActive) controller.cancelControl(); if (level) level.reset(); panDirty = false; panConflict = false }
    function send(fields) {
        controller.change(Object.assign({kind: "channel", mix: mixName, source: channel.channel}, fields))
    }
    function adjustPan(finish) {
        if (panConflict) { controller.cancelControl(); controller.editConflict(); panDirty = false; return }
        controller.adjust({kind: "channel_pan", mix: mixName, source: channel.channel}, panPreview, finish)
    }
    Connections {
        target: root.controller
        function onDiscardEdits() { level.reset(); root.panDirty = false; root.panConflict = false }
        function onChanged() { if (root.panDirty && root.editRevision !== root.controller.editRevision) root.panConflict = true }
    }
    headerContent: ColumnLayout {
        anchors.fill: parent
        spacing: 6
        Label {
            text: root.channel.channel.toUpperCase()
            font.bold: true
            Layout.fillWidth: true
            Layout.minimumHeight: 20
            Layout.preferredHeight: 20
            Layout.maximumHeight: 20
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
        }
        Label {
            text: root.channel.mono_included ? qsTr("Mono source") : root.channel.stereo_pair_included ? qsTr("Stereo pair") : qsTr("Not included")
            font.pixelSize: 11
            opacity: 0.7
            Layout.fillWidth: true
            Layout.minimumHeight: 30
            Layout.preferredHeight: 30
            Layout.maximumHeight: 30
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
        }
        Item { Layout.fillHeight: true }
    }
    controlContent: LevelControl {
        id: level
        objectName: "sourceLevel-" + root.channel.channel
        anchors.fill: parent
        enabled: root.controller.canWrite || (root.controller.liveActive && root.controller.activeControlKey === root.levelKey)
        label: qsTr("Level")
        confirmed: root.channel.derived_level_db
        revision: root.controller.editRevision
        meterName: root.channel.channel.toUpperCase()
        metersAvailable: root.controller.meters.available === true
        meterValues: root.controller.meters.sources_dbfs ? [root.controller.meters.sources_dbfs[["analog1", "analog2", "analog3", "analog4", "usb1", "usb2", "usb3", "usb4", "usb5", "usb6"].indexOf(root.channel.channel)]] : []
        onAdjusted: (value, finish) => root.controller.adjust({kind: "channel_level", mix: root.mixName, source: root.channel.channel}, value, finish)
        onCancelled: root.controller.cancelControl()
        onCommitted: value => root.send({level_db: value})
        onConflicted: root.controller.editConflict()
    }
    footerContent: ColumnLayout {
        anchors.fill: parent
        spacing: 6
        Label {
            text: root.channel.derived_pan === null ? qsTr("Pan undefined") : qsTr("Pan ") + Number(root.channel.derived_pan).toFixed(2)
            Layout.fillWidth: true
            Layout.minimumHeight: 18
            Layout.preferredHeight: 18
            Layout.maximumHeight: 18
            horizontalAlignment: Text.AlignHCenter
            font.pixelSize: 11
            elide: Text.ElideRight
        }
        Slider {
            id: pan
            Layout.fillWidth: true
            Layout.minimumHeight: 30
            Layout.preferredHeight: 30
            Layout.maximumHeight: 30
            enabled: root.controller.canWrite || (root.controller.liveActive && root.controller.activeControlKey === root.panKey)
            from: 0; to: 1; stepSize: 0.01
            value: root.panDirty ? root.panPreview : (root.channel.derived_pan === null ? 0.5 : root.channel.derived_pan)
            Accessible.name: root.channel.channel + " pan"
            onMoved: { if (!root.panDirty) root.editRevision = root.controller.editRevision; root.panPreview = value; root.panDirty = true; root.adjustPan(!pressed) }
            onPressedChanged: { if (!pressed && root.panDirty) root.adjustPan(true) }
            Keys.onEscapePressed: { root.controller.cancelControl(); root.panDirty = false; root.panConflict = false }
        }
        RowLayout {
            Layout.alignment: Qt.AlignHCenter
            Layout.minimumHeight: 32
            Layout.preferredHeight: 32
            Layout.maximumHeight: 32
            Button { enabled: root.controller.canWrite; Layout.preferredWidth: 44; Layout.fillHeight: true; text: root.channel.mute ? "M ✓" : "M"; highlighted: root.channel.mute; Accessible.name: root.channel.channel + " mute"; onClicked: root.send({mute: !root.channel.mute}) }
            Button { enabled: root.controller.canWrite; Layout.preferredWidth: 44; Layout.fillHeight: true; text: root.channel.solo ? "S ✓" : "S"; highlighted: root.channel.solo; Accessible.name: root.channel.channel + " solo"; onClicked: root.send({solo: !root.channel.solo}) }
        }
        Item { Layout.fillHeight: true }
    }
}
