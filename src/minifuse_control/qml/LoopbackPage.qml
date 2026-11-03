pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ColumnLayout {
    id: root
    required property var controller
    property bool compact: false
    readonly property var mix: controller.mixes.length ? controller.mixes[0] : null
    spacing: 12

    Flow {
        Layout.fillWidth: true
        spacing: 8
        StateButton {
            implicitWidth: contentItem.implicitWidth + 24
            objectName: "loopbackEnabled"
            text: qsTr("Loopback")
            description: qsTr("Send the hardware mix to the loopback recording channels")
            active: root.controller.loopbackRouting.enabled === true
            enabled: root.controller.canWrite
            onClicked: root.controller.change({kind: "loopback_routing", enabled: !active})
        }
        StateButton {
            implicitWidth: contentItem.implicitWidth + 24
            objectName: "loopbackUsb12"
            text: qsTr("Also record on USB 1–2")
            description: qsTr("Duplicate the loopback mix onto recording inputs 1–2")
            active: root.controller.loopbackRouting.usb12 === true
            enabled: root.controller.canWrite
            onClicked: root.controller.change({kind: "loopback_routing", usb12: !active})
        }
        StateButton {
            implicitWidth: contentItem.implicitWidth + 24
            objectName: "loopbackMonitor"
            text: qsTr("Monitor mix")
            description: qsTr("Play the loopback mix through the physical outputs and headphones")
            active: root.controller.loopbackRouting.monitor === true
            enabled: root.controller.canWrite
            onClicked: root.controller.change({kind: "loopback_routing", monitor: !active})
        }
    }
    RowLayout {
        visible: root.controller.modelProfile.id === "mf2_otg"
        Layout.fillWidth: true
        spacing: 8
        Label { text: qsTr("Main → OTG") }
        ComboBox {
            objectName: "mainToOtg"
            model: [qsTr("OTG 3–4"), qsTr("Output 1–2")]
            currentIndex: root.controller.otgRouting.main_to_otg || 0
            enabled: root.controller.canWrite
            onActivated: root.controller.change({kind: "otg_routing", main_to_otg: currentIndex})
        }
        StateButton {
            implicitWidth: contentItem.implicitWidth + 24
            objectName: "otgToMonitor"
            text: qsTr("Monitor OTG")
            description: qsTr("Use OTG playback as the monitoring source")
            active: root.controller.otgRouting.otg_to_monitor === true
            enabled: root.controller.canWrite
            onClicked: root.controller.change({kind: "otg_routing", otg_to_monitor: !active})
        }
        Label { text: qsTr("LED meters") }
        ComboBox {
            objectName: "otgMeterSource"
            Layout.fillWidth: true
            model: [qsTr("Monitor out"), qsTr("OTG in"), qsTr("OTG out"), qsTr("Computer out")]
            currentIndex: root.controller.otgRouting.meter_source || 0
            enabled: root.controller.canWrite
            onActivated: root.controller.change({kind: "otg_routing", meter_source: currentIndex})
        }
    }
    RowLayout {
        Layout.fillWidth: true
        Layout.minimumHeight: root.compact ? 330 : 396
        Layout.preferredHeight: root.compact ? 330 : 396
        spacing: 10
        Repeater {
            model: root.mix ? root.mix.channels.length : 0
            delegate: ChannelStrip {
                required property int index
                channel: root.mix.channels[index]
                mixName: "loopback"
                controller: root.controller
                compact: root.compact
                Layout.fillWidth: true
            }
        }
        StripFrame {
            objectName: "loopbackMaster"
            master: true
            compact: root.compact
            Layout.fillWidth: true
            headerContent: ColumnLayout {
                anchors.fill: parent
                Label { text: qsTr("Loopback"); font.bold: true; Layout.fillWidth: true; horizontalAlignment: Text.AlignHCenter }
                Label { text: qsTr("MASTER"); font.pixelSize: 9; opacity: 0.6; Layout.fillWidth: true; horizontalAlignment: Text.AlignHCenter }
                Item { Layout.fillHeight: true }
            }
            controlContent: LevelControl {
                id: master
                objectName: "loopbackMasterLevel"
                anchors.fill: parent
                label: qsTr("MASTER")
                compact: root.compact
                minimum: -64
                maximum: 0
                confirmed: root.mix ? root.mix.master_db : null
                revision: root.controller.editRevision
                enabled: root.controller.canWrite || (root.controller.liveActive && root.controller.activeControlKey === "master_level:loopback:")
                meterName: qsTr("Loopback mix")
                meterValues: root.controller.meters.loopback_dbfs || []
                metersAvailable: root.controller.meters.available === true
                onAdjusted: (value, finish) => root.controller.adjust({kind: "master_level", mix: "loopback"}, value, finish)
                onCancelled: root.controller.cancelControl()
                onCommitted: value => root.controller.change({kind: "master", mix: "loopback", level_db: value})
                onConflicted: root.controller.editConflict()
                Connections {
                    target: root.controller
                    function onDiscardEdits() { master.reset() }
                }
            }
        }
    }
    RowLayout {
        visible: root.controller.modelProfile.id === "mf2_otg"
        Label { text: qsTr("OTG input peaks") }
        Repeater {
            model: 2
            delegate: SignalMeter {
                required property int index
                Layout.preferredWidth: 7
                Layout.preferredHeight: 46
                available: root.controller.meters.available === true
                peakDbfs: root.controller.meters.otg_dbfs ? root.controller.meters.otg_dbfs[index] : null
                channelName: index === 0 ? qsTr("OTG left") : qsTr("OTG right")
            }
        }
        Item { Layout.fillWidth: true }
    }
    Label {
        Layout.fillWidth: true
        wrapMode: Text.Wrap
        opacity: 0.6
        text: qsTr("This is the interface's native loopback mix. Windows SLS virtual devices and independent software mixes are separate features. USB playback strips have no individual hardware peak readings.")
    }
}
