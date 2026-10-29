pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ColumnLayout {
    id: root
    required property var controller
    property int selected: 0
    onSelectedChanged: { controller.cancelControl(); controller.discardEdits() }
    property var mix: controller.mixes.length > selected ? controller.mixes[selected] : null
    property var mixCapabilities: controller.capabilities.mixes && controller.capabilities.mixes.length > selected ? controller.capabilities.mixes[selected] : null
    spacing: 14
    RowLayout {
        TabBar {
            Layout.preferredWidth: 420
            currentIndex: root.selected
            onCurrentIndexChanged: root.selected = currentIndex
            TabButton { text: qsTr("Outputs 1–2") }
            TabButton { text: qsTr("Outputs 3–4") }
            TabButton { text: qsTr("Loopback") }
        }
        Item { Layout.fillWidth: true }
        Label { text: qsTr("Configured levels · meters unavailable"); opacity: 0.65; font.pixelSize: 12 }
    }
    Label {
        visible: !root.mix
        text: qsTr("Connect a supported interface and obtain confirmed state to enable the mixer.")
        wrapMode: Text.Wrap
        Layout.fillWidth: true
    }
    Flow {
        Layout.fillWidth: true
        spacing: 6
        visible: root.mix !== null
        Repeater {
            model: root.mixCapabilities ? root.mixCapabilities.membership : []
            delegate: Button {
                id: member
                required property string modelData
                property var channels: {
                    if (!root.mix) return []
                    const names = {usb12: ["usb1", "usb2"], usb34: ["usb3", "usb4"], usb56: ["usb5", "usb6"]}
                    const wanted = names[modelData] || [modelData]
                    return root.mix.channels.filter(c => wanted.includes(c.channel))
                }
                property bool analog: modelData.startsWith("analog")
                property bool included: channels.length > 0 && (analog ? channels[0].mono_included : channels[0].stereo_pair_included)
                property bool topologyAllowed: channels.length > 0 && (analog ? !channels[0].stereo_pair_included : !channels.some(c => c.mono_included))
                text: (included ? "✓ " : "+ ") + modelData.toUpperCase()
                highlighted: included
                enabled: root.controller.canWrite && topologyAllowed
                Accessible.name: modelData + (included ? " included" : " excluded")
                ToolTip.visible: hovered
                ToolTip.text: topologyAllowed ? qsTr("Include or remove this source") : qsTr("Current mono/stereo conversion is unavailable")
                onClicked: root.controller.change({kind: "membership", mix: root.mix.mix, source: modelData, included: !included})
            }
        }
    }
    RowLayout {
        Layout.fillWidth: true
        Layout.fillHeight: true
        spacing: 16
        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            contentWidth: strips.implicitWidth
            ScrollBar.horizontal.policy: ScrollBar.AlwaysOn
            RowLayout {
                id: strips
                height: parent.height
                spacing: 10
                Repeater {
                    // A stable numeric model keeps active edits alive when a
                    // confirmed revision changes, so conflicts can be shown.
                    model: root.mix ? root.mix.channels.length : 0
                    delegate: ChannelStrip {
                        required property int index
                        channel: root.mix.channels[index]
                        mixName: root.mix.mix
                        controller: root.controller
                    }
                }
            }
        }
        Frame {
            Layout.preferredWidth: 205
            Layout.fillHeight: true
            visible: root.mix !== null
            ColumnLayout {
                anchors.fill: parent
                spacing: 12
                Label { text: qsTr("MIX MASTER"); font.bold: true; Layout.alignment: Qt.AlignHCenter }
                ComboBox {
                    id: route
                    Layout.fillWidth: true
                    model: root.mixCapabilities ? root.mixCapabilities.routes : []
                    currentIndex: root.mix ? model.indexOf(root.mix.route) : -1
                    enabled: root.controller.canWrite
                    Accessible.name: qsTr("Output route")
                    onActivated: root.controller.change({kind: "route", mix: root.mix.mix, source: currentText})
                }
                Label {
                    Layout.fillWidth: true
                    visible: root.mix && root.mix.route !== "mix"
                    text: qsTr("This destination bypasses its custom mix. The faders still edit that mix.")
                    wrapMode: Text.Wrap
                    font.pixelSize: 12
                }
                LevelControl {
                    id: master
                    objectName: "masterControl"
                    Layout.fillHeight: true
                    Layout.fillWidth: true
                    enabled: root.controller.canWrite || (root.controller.liveActive && root.controller.activeControlKey === "master_level:" + root.mix.mix + ":")
                    label: qsTr("Master")
                    minimum: -64
                    maximum: 0
                    confirmed: root.mix ? root.mix.master_db : null
                    revision: root.controller.editRevision
                    onAdjusted: (value, finish) => root.controller.adjust({kind: "master_level", mix: root.mix.mix}, value, finish)
                    onCancelled: root.controller.cancelControl()
                    onCommitted: value => root.controller.change({kind: "master", mix: root.mix.mix, level_db: value})
                    onConflicted: root.controller.editConflict()
                }
                Connections { target: root.controller; function onDiscardEdits() { master.reset() } }
                Label { text: qsTr("Hardware mix level"); Layout.alignment: Qt.AlignHCenter; font.pixelSize: 11; opacity: 0.7 }
            }
        }
    }
}
