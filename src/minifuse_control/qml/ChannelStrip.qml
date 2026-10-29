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
    readonly property bool included: channel.mono_included || channel.stereo_pair_included
    readonly property string sourceName: channel.channel.replace("analog", "Analog ").replace("usb", "USB ")
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
    function panText(value) {
        if (value === null) return qsTr("Undefined")
        if (Math.abs(value - 0.5) < 0.005) return qsTr("Center")
        return (value < 0.5 ? "L " : "R ") + Math.round(Math.abs(value - 0.5) * 200)
    }
    Connections {
        target: root.controller
        function onDiscardEdits() { level.reset(); root.panDirty = false; root.panConflict = false }
        function onChanged() { if (root.panDirty && root.editRevision !== root.controller.editRevision) root.panConflict = true }
    }
    headerContent: ColumnLayout {
        anchors.fill: parent
        spacing: 4
        Label {
            text: root.sourceName
            font.bold: true
            font.pixelSize: 12
            Layout.fillWidth: true
            Layout.preferredHeight: 20
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
            opacity: root.included ? 1 : 0.5
        }
        Label {
            visible: !root.compact
            text: !root.included ? qsTr("OUTSIDE MIX") : root.channel.channel.startsWith("analog") ? qsTr("INPUT") : qsTr("PLAYBACK")
            font.pixelSize: 8
            font.letterSpacing: 0.8
            opacity: 0.5
            Layout.fillWidth: true
            Layout.preferredHeight: 14
            horizontalAlignment: Text.AlignHCenter
            elide: Text.ElideRight
        }
        Label {
            visible: !root.compact
            text: root.panText(root.panDirty ? root.panPreview : root.channel.derived_pan)
            Layout.fillWidth: true
            Layout.preferredHeight: 16
            horizontalAlignment: Text.AlignHCenter
            font.pixelSize: 10
            opacity: 0.6
            elide: Text.ElideRight
        }
        Slider {
            id: pan
            objectName: "sourcePan-" + root.channel.channel
            Layout.fillWidth: true
            Layout.preferredHeight: 24
            enabled: root.controller.canWrite || (root.controller.liveActive && root.controller.activeControlKey === root.panKey)
            from: 0; to: 1; stepSize: 0.01
            leftPadding: 6; rightPadding: 6
            value: root.panDirty ? root.panPreview : (root.channel.derived_pan === null ? 0.5 : root.channel.derived_pan)
            Accessible.name: root.sourceName + " pan"
            ToolTip.visible: hovered
            ToolTip.text: root.panText(root.panDirty ? root.panPreview : root.channel.derived_pan)
            onMoved: { if (!root.panDirty) root.editRevision = root.controller.editRevision; root.panPreview = value; root.panDirty = true; root.adjustPan(!pressed) }
            onPressedChanged: { if (!pressed && root.panDirty) root.adjustPan(true) }
            Keys.onEscapePressed: { root.controller.cancelControl(); root.panDirty = false; root.panConflict = false }
            background: Rectangle {
                x: pan.leftPadding; y: (pan.height - height) / 2
                width: pan.availableWidth; height: 2
                color: Qt.alpha(pan.palette.windowText, 0.22)
                Rectangle { anchors.centerIn: parent; width: 1; height: 6; color: pan.palette.mid }
            }
            handle: Rectangle {
                x: pan.leftPadding + pan.visualPosition * (pan.availableWidth - width)
                y: (pan.height - height) / 2
                implicitWidth: 8; implicitHeight: 12; radius: 2
                color: pan.pressed ? pan.palette.highlight : pan.palette.button
                border.color: pan.visualFocus || pan.pressed ? pan.palette.highlight : Qt.alpha(pan.palette.windowText, 0.55)
            }
        }
        RowLayout {
            Layout.alignment: Qt.AlignHCenter
            Layout.preferredHeight: 28
            spacing: 6
            StateButton { objectName: "sourceMute-" + root.channel.channel; enabled: root.controller.canWrite; text: "M"; active: root.channel.mute; description: root.sourceName + " mute"; onClicked: root.send({mute: !root.channel.mute}) }
            StateButton { objectName: "sourceSolo-" + root.channel.channel; enabled: root.controller.canWrite; text: "S"; active: root.channel.solo; description: root.sourceName + " solo"; onClicked: root.send({solo: !root.channel.solo}) }
        }
        Item { Layout.fillHeight: true }
    }
    controlContent: LevelControl {
        id: level
        objectName: "sourceLevel-" + root.channel.channel
        anchors.fill: parent
        enabled: root.controller.canWrite || (root.controller.liveActive && root.controller.activeControlKey === root.levelKey)
        label: qsTr("GAIN")
        compact: root.compact
        confirmed: root.channel.derived_level_db
        revision: root.controller.editRevision
        meterName: root.sourceName
        metersAvailable: root.controller.meters.available === true
        meterValues: root.controller.meters.sources_dbfs ? [root.controller.meters.sources_dbfs[["analog1", "analog2", "analog3", "analog4", "usb1", "usb2", "usb3", "usb4", "usb5", "usb6"].indexOf(root.channel.channel)]] : []
        onAdjusted: (value, finish) => root.controller.adjust({kind: "channel_level", mix: root.mixName, source: root.channel.channel}, value, finish)
        onCancelled: root.controller.cancelControl()
        onCommitted: value => root.send({level_db: value})
        onConflicted: root.controller.editConflict()
    }
}
