pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ColumnLayout {
    id: root
    objectName: "mixerPage"
    Layout.minimumWidth: 0
    required property var controller
    property int selected: 0
    property bool compact: false
    onSelectedChanged: { controller.cancelControl(); controller.discardEdits() }
    property var mix: controller.mixes.length > selected ? controller.mixes[selected] : null
    property var mixCapabilities: controller.capabilities.mixes && controller.capabilities.mixes.length > selected ? controller.capabilities.mixes[selected] : null
    readonly property var destinations: [qsTr("Monitor · Phones 1"), qsTr("Line outputs · Phones 2"), qsTr("Loopback · Computer capture")]
    spacing: root.compact ? 8 : 12
    TabBar {
        Layout.fillWidth: true
        currentIndex: root.selected
        onCurrentIndexChanged: root.selected = currentIndex
        spacing: 6
        background: null
        NavigationTab { implicitHeight: root.compact ? 32 : 36; text: qsTr("Outputs 1–2") }
        NavigationTab { implicitHeight: root.compact ? 32 : 36; text: qsTr("Outputs 3–4") }
        NavigationTab { implicitHeight: root.compact ? 32 : 36; text: qsTr("Loopback") }
    }
    RowLayout {
        Layout.fillWidth: true
        spacing: 12
        ColumnLayout {
            Layout.fillWidth: true
            Layout.minimumWidth: 0
            spacing: 3
            Label { text: root.destinations[root.selected]; font.pixelSize: 16; font.bold: true; Layout.fillWidth: true; elide: Text.ElideRight }
            Label { text: qsTr("INPUTS & COMPUTER PLAYBACK"); font.pixelSize: 9; font.letterSpacing: 1; opacity: 0.5; Layout.fillWidth: true; elide: Text.ElideRight }
        }
        Button {
            id: sourcesButton
            objectName: "sourcesButton"
            text: qsTr("Mix sources…")
            enabled: root.mix !== null
            onClicked: membership.open()
            Popup {
                id: membership
                objectName: "membershipPopup"
                y: sourcesButton.height + 6
                x: sourcesButton.width - width
                width: 360
                padding: 16
                closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
                background: Rectangle { color: membership.palette.window; border.color: membership.palette.mid; radius: 6 }
                contentItem: ColumnLayout {
                    spacing: 12
                    Label { text: qsTr("Sources in this mix"); font.bold: true }
                    Label { text: qsTr("Removing a source mutes it and clears solo."); Layout.fillWidth: true; wrapMode: Text.Wrap; font.pixelSize: 11; opacity: 0.7 }
                    Flow {
                        Layout.fillWidth: true
                        spacing: 6
                        Repeater {
                            model: root.mixCapabilities ? root.mixCapabilities.membership : []
                            delegate: StateButton {
                                id: member
                                objectName: "membershipSource-" + modelData
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
                                implicitWidth: 98
                                text: modelData.replace("analog", "Analog ").replace("usb", "USB ")
                                active: included
                                enabled: root.controller.canWrite && topologyAllowed
                                description: modelData + qsTr(" included in mix")
                                ToolTip.text: topologyAllowed ? qsTr("Include or remove this source") : qsTr("Current mono/stereo conversion is unavailable")
                                onClicked: root.controller.change({kind: "membership", mix: root.mix.mix, source: modelData, included: !included})
                            }
                        }
                    }
                }
            }
        }
        Label { text: qsTr("Route"); font.pixelSize: 11; opacity: 0.65 }
        ComboBox {
            id: route
            objectName: "routeSelector"
            Layout.preferredWidth: 150
            model: root.mixCapabilities ? root.mixCapabilities.routes : []
            currentIndex: root.mix ? model.indexOf(root.mix.route) : -1
            displayText: currentText === "mix" ? qsTr("Custom mix") : currentText.toUpperCase().replace("USB", "USB ")
            enabled: root.controller.canWrite
            Accessible.name: qsTr("Output route")
            onActivated: root.controller.change({kind: "route", mix: root.mix.mix, source: currentText})
        }
    }
    Label {
        visible: !root.mix
        text: qsTr("Connect a supported interface to enable the mixer.")
        wrapMode: Text.Wrap
        Layout.fillWidth: true
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
        ScrollBar.vertical.policy: contentHeight > availableHeight ? ScrollBar.AlwaysOn : ScrollBar.AlwaysOff
        RowLayout {
            id: stripArea
            width: stripViewport.availableWidth
            height: Math.max(root.compact ? 306 : 396, stripViewport.availableHeight)
            spacing: 14
            ScrollView {
                id: sourceScroll
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                contentWidth: strips.width
                contentHeight: strips.height
                ScrollBar.horizontal.policy: ScrollBar.AsNeeded
                ScrollBar.vertical.policy: ScrollBar.AlwaysOff
                RowLayout {
                    id: strips
                    width: Math.max(implicitWidth, sourceScroll.availableWidth)
                    height: Math.max(0, sourceScroll.availableHeight - 12)
                    spacing: 5
                    Repeater {
                        // Stable delegates retain the active preview across readbacks.
                        model: root.mix ? root.mix.channels.length : 0
                        delegate: ChannelStrip {
                            required property int index
                            Layout.fillWidth: true
                            compact: root.compact
                            channel: root.mix.channels[index]
                            mixName: root.mix.mix
                            controller: root.controller
                        }
                    }
                }
            }
            StripFrame {
                objectName: "masterStrip"
                master: true
                compact: root.compact
                Layout.preferredWidth: 146
                Layout.bottomMargin: 12
                visible: root.mix !== null
                headerContent: ColumnLayout {
                    anchors.fill: parent
                    spacing: 4
                    Label {
                        text: qsTr("Mix master")
                        font.bold: true
                        font.pixelSize: 13
                        Layout.fillWidth: true
                        Layout.preferredHeight: 20
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    Label {
                        text: [qsTr("OUTPUTS 1–2"), qsTr("OUTPUTS 3–4"), qsTr("LOOPBACK")][root.selected]
                        font.pixelSize: 8
                        font.letterSpacing: 0.8
                        opacity: 0.5
                        Layout.fillWidth: true
                        Layout.preferredHeight: 14
                        horizontalAlignment: Text.AlignHCenter
                    }
                    Item { Layout.fillHeight: true }
                    Label {
                        text: root.mix && root.mix.route !== "mix" ? qsTr("DIRECT USB") : qsTr("CUSTOM MIX")
                        font.pixelSize: 9
                        font.letterSpacing: 1
                        color: palette.highlight
                        Layout.fillWidth: true
                        horizontalAlignment: Text.AlignHCenter
                    }
                    Label {
                        visible: !root.compact
                        text: root.mix && root.mix.route !== "mix" ? qsTr("Faders edit the bypassed mix") : qsTr("Stereo output level")
                        font.pixelSize: 10
                        opacity: 0.65
                        Layout.fillWidth: true
                        Layout.preferredHeight: 32
                        wrapMode: Text.Wrap
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }
                    Item { Layout.fillHeight: true }
                }
                controlContent: LevelControl {
                    id: master
                    objectName: "masterControl"
                    anchors.fill: parent
                    enabled: root.controller.canWrite || (root.controller.liveActive && root.controller.activeControlKey === "master_level:" + root.mix.mix + ":")
                    label: qsTr("MASTER")
                    compact: root.compact
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
                Connections { target: root.controller; function onDiscardEdits() { master.reset() } }
            }
        }
    }
    RowLayout {
        Layout.fillWidth: true
        Label {
            text: root.controller.meters.available === true ? qsTr("Source peaks · Mix peaks after master · dBFS") : root.controller.capabilities.signal_meters ? qsTr("Waiting for fresh meters…") : qsTr("Meters unavailable")
            opacity: 0.5
            font.pixelSize: 10
            Layout.fillWidth: true
            elide: Text.ElideRight
        }
        Label { text: qsTr("Gain in dB · Enter to apply a numeric value"); font.pixelSize: 10; opacity: 0.5 }
    }
    InputControls { controller: root.controller; compact: root.compact }
}
