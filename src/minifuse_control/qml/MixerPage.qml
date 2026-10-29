pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ColumnLayout {
    id: root
    objectName: "mixerPage"
    required property var controller
    property int selected: 0
    onSelectedChanged: { controller.cancelControl(); controller.discardEdits() }
    property var mix: controller.mixes.length > selected ? controller.mixes[selected] : null
    property var mixCapabilities: controller.capabilities.mixes && controller.capabilities.mixes.length > selected ? controller.capabilities.mixes[selected] : null
    spacing: 14
    InputControls { controller: root.controller }
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
        Label {
            text: root.controller.meters.available === true ? qsTr("Source peaks · Mix peaks after master · dBFS") : root.controller.capabilities.signal_meters ? qsTr("Waiting for fresh meters…") : qsTr("Meters unavailable")
            opacity: 0.65
            font.pixelSize: 11
            Layout.fillWidth: true
            Layout.preferredWidth: 310
            horizontalAlignment: Text.AlignRight
            elide: Text.ElideRight
        }
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
    ScrollView {
        id: stripViewport
        objectName: "stripViewport"
        Layout.fillWidth: true
        Layout.fillHeight: true
        clip: true
        contentWidth: availableWidth
        contentHeight: stripArea.height
        ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
        RowLayout {
            id: stripArea
            width: stripViewport.availableWidth
            height: Math.max(480, stripViewport.availableHeight)
            spacing: 16
            ScrollView {
                id: sourceScroll
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                contentWidth: strips.implicitWidth
                contentHeight: strips.height
                ScrollBar.horizontal.policy: ScrollBar.AlwaysOn
                ScrollBar.vertical.policy: ScrollBar.AlwaysOff
                RowLayout {
                    id: strips
                    height: Math.max(0, sourceScroll.availableHeight - sourceScroll.effectiveScrollBarHeight)
                    spacing: 10
                    Repeater {
                        // Stable delegates retain the active preview across readbacks.
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
            StripFrame {
                objectName: "masterStrip"
                Layout.preferredWidth: 205
                Layout.bottomMargin: sourceScroll.effectiveScrollBarHeight
                visible: root.mix !== null
                headerContent: ColumnLayout {
                    anchors.fill: parent
                    spacing: 6
                    Label {
                        text: qsTr("MIX MASTER")
                        font.bold: true
                        Layout.fillWidth: true
                        Layout.minimumHeight: 20
                        Layout.preferredHeight: 20
                        Layout.maximumHeight: 20
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                        elide: Text.ElideRight
                    }
                    ComboBox {
                        id: route
                        Layout.fillWidth: true
                        Layout.minimumHeight: 30
                        Layout.preferredHeight: 30
                        Layout.maximumHeight: 30
                        model: root.mixCapabilities ? root.mixCapabilities.routes : []
                        currentIndex: root.mix ? model.indexOf(root.mix.route) : -1
                        enabled: root.controller.canWrite
                        Accessible.name: qsTr("Output route")
                        onActivated: root.controller.change({kind: "route", mix: root.mix.mix, source: currentText})
                    }
                    Item { Layout.fillHeight: true }
                }
                controlContent: LevelControl {
                    id: master
                    objectName: "masterControl"
                    anchors.fill: parent
                    enabled: root.controller.canWrite || (root.controller.liveActive && root.controller.activeControlKey === "master_level:" + root.mix.mix + ":")
                    label: qsTr("Master")
                    minimum: -64
                    maximum: 0
                    confirmed: root.mix ? root.mix.master_db : null
                    revision: root.controller.editRevision
                    meterName: root.mix ? root.mix.mix.toUpperCase() + qsTr(" mix") : qsTr("Mix")
                    metersAvailable: root.controller.meters.available === true
                    meterValues: root.controller.meters.mixes_dbfs ? root.controller.meters.mixes_dbfs[root.selected] : [null, null]
                    onAdjusted: (value, finish) => root.controller.adjust({kind: "master_level", mix: root.mix.mix}, value, finish)
                    onCancelled: root.controller.cancelControl()
                    onCommitted: value => root.controller.change({kind: "master", mix: root.mix.mix, level_db: value})
                    onConflicted: root.controller.editConflict()
                }
                footerContent: Label {
                    anchors.fill: parent
                    text: root.mix && root.mix.route !== "mix" ? qsTr("This destination bypasses its custom mix. The faders still edit that mix.") : qsTr("Hardware mix level")
                    horizontalAlignment: Text.AlignHCenter
                    wrapMode: Text.Wrap
                    font.pixelSize: 11
                    opacity: 0.7
                }
                Connections { target: root.controller; function onDiscardEdits() { master.reset() } }
            }
        }
    }
}
