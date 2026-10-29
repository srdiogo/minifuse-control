pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ColumnLayout {
    id: root
    required property string label
    property var confirmed: null
    property string revision: ""
    property real minimum: -60
    property real maximum: 12
    property bool vertical: true
    property bool compact: false
    property bool dirty: false
    property bool conflict: false
    property real preview: minimum
    property bool released: false
    property var meterValues: []
    property bool metersAvailable: false
    property string meterName: label
    signal adjusted(var value, bool finish)
    signal cancelled()
    signal committed(var value)
    signal conflicted()
    spacing: root.compact ? 4 : 6

    function reset() { dirty = false; released = false; conflict = false; numeric.text = displayText() + " dB"; numeric.focus = false }
    function displayText() { return confirmed === null ? "−∞" : Number(confirmed).toFixed(2) }
    function finish(value) {
        if (conflict) { reset(); conflicted(); return }
        dirty = false
        committed(value)
    }
    function track(value, finish) {
        if (released) return
        if (conflict) { cancelled(); reset(); conflicted(); return }
        preview = value
        dirty = true
        released = finish
        adjusted(value, finish)
    }
    onRevisionChanged: { if (dirty || numeric.activeFocus) conflict = true }

    Label {
        objectName: "levelCaption"
        text: root.label
        Layout.fillWidth: true
        Layout.minimumHeight: root.compact ? 12 : 16
        Layout.preferredHeight: root.compact ? 12 : 16
        Layout.maximumHeight: root.compact ? 12 : 16
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
        font.pixelSize: 9
        font.letterSpacing: 1
        opacity: 0.5
    }
    Slider {
        id: slider
        objectName: "levelSlider"
        Layout.fillHeight: root.vertical
        Layout.fillWidth: !root.vertical
        Layout.alignment: Qt.AlignHCenter
        Layout.minimumHeight: root.vertical ? 130 : 34
        Layout.preferredWidth: root.vertical ? 34 : -1
        Layout.minimumWidth: root.vertical ? 34 : 0
        Layout.maximumWidth: root.vertical ? 34 : Number.POSITIVE_INFINITY
        orientation: root.vertical ? Qt.Vertical : Qt.Horizontal
        from: root.minimum
        to: root.maximum
        stepSize: 0.25
        padding: 0
        value: root.dirty ? root.preview : (root.confirmed === null ? root.minimum : root.confirmed)
        Accessible.name: root.label + " configured level"
        onMoved: root.track(value, !pressed)
        onPressedChanged: {
            if (pressed) root.released = false
            else if (root.dirty && !root.released) root.track(value, true)
        }
        Keys.onEscapePressed: { root.cancelled(); root.reset() }
        background: Item {
            Rectangle {
                x: slider.horizontal ? 6 : (parent.width - 4) / 2
                y: slider.vertical ? 6 : (parent.height - 4) / 2
                width: slider.horizontal ? parent.width - 12 : 4
                height: slider.vertical ? parent.height - 12 : 4
                radius: 2
                color: Qt.alpha(slider.palette.windowText, 0.18)
            }
            Repeater {
                model: root.vertical ? (root.maximum === 0 ? [0, -12, -24, -36, -48, -64] : [12, 0, -12, -24, -36, -48, -60]) : []
                delegate: Label {
                    required property real modelData
                    x: -23
                    y: 6 + (root.maximum - modelData) / (root.maximum - root.minimum) * (slider.height - 12) - height / 2
                    width: 21
                    text: modelData > 0 ? "+" + modelData : modelData
                    font.pixelSize: 9
                    opacity: 0.4
                    horizontalAlignment: Text.AlignRight
                }
            }
        }
        handle: Rectangle {
            x: slider.leftPadding + (slider.horizontal ? slider.visualPosition * (slider.availableWidth - width) : (slider.availableWidth - width) / 2)
            y: slider.topPadding + (slider.vertical ? slider.visualPosition * (slider.availableHeight - height) : (slider.availableHeight - height) / 2)
            implicitWidth: slider.vertical ? 26 : 12
            implicitHeight: slider.vertical ? 12 : 26
            radius: 2
            color: slider.pressed ? slider.palette.highlight : slider.palette.button
            border.color: slider.pressed || slider.visualFocus ? slider.palette.highlight : Qt.alpha(slider.palette.windowText, 0.6)
            Rectangle {
                anchors.centerIn: parent
                width: slider.vertical ? parent.width - 6 : 1
                height: slider.vertical ? 1 : parent.height - 6
                color: slider.pressed ? slider.palette.highlightedText : slider.palette.windowText
                opacity: 0.7
            }
        }
        Row {
            anchors.left: parent.right
            anchors.leftMargin: 5
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            spacing: 2
            Repeater {
                model: root.meterValues.length || 1
                delegate: SignalMeter {
                    required property int index
                    height: parent.height
                    width: 7
                    available: root.metersAvailable
                    peakDbfs: root.meterValues.length > index ? root.meterValues[index] : null
                    channelName: root.meterName + (root.meterValues.length > 1 ? (index === 0 ? " L" : " R") : "")
                }
            }
        }
    }
    RowLayout {
        objectName: "levelEntry"
        Layout.alignment: Qt.AlignHCenter
        Layout.minimumHeight: 28
        Layout.preferredHeight: 28
        Layout.maximumHeight: 28
        spacing: 3
        TextField {
            id: numeric
            objectName: "levelValue"
            Layout.minimumWidth: 64
            Layout.preferredWidth: 64
            Layout.maximumWidth: 64
            Layout.fillHeight: true
            font.pixelSize: 10
            horizontalAlignment: Text.AlignHCenter
            leftPadding: 2
            rightPadding: 2
            Binding {
                target: numeric
                property: "text"
                value: (root.dirty ? root.preview.toFixed(2) : root.displayText()) + " dB"
                when: !numeric.activeFocus
                restoreMode: Binding.RestoreBindingOrValue
            }
            selectByMouse: true
            Accessible.name: root.label + " numeric dB; Enter to apply"
            ToolTip.visible: hovered
            ToolTip.text: qsTr("Configured gain · Type a value and press Enter")
            background: Rectangle {
                radius: 3
                color: numeric.activeFocus ? numeric.palette.base : "transparent"
                border.color: Qt.alpha(numeric.activeFocus ? numeric.palette.highlight : numeric.palette.windowText, numeric.activeFocus ? 1 : 0.16)
            }
            onAccepted: {
                const normalized = text.trim().replace(/\s*dB$/i, "")
                const value = normalized === "-inf" || normalized === "−∞" ? null : Number(normalized)
                if (value === null || (normalized !== "" && Number.isFinite(value) && value >= root.minimum && value <= root.maximum)) root.finish(value)
                else text = root.displayText() + " dB"
                focus = false
            }
            onActiveFocusChanged: { if (!activeFocus) text = root.displayText() + " dB" }
            Keys.onEscapePressed: { root.reset(); focus = false }
        }
        ToolButton {
            Layout.minimumWidth: 21
            Layout.preferredWidth: 21
            Layout.maximumWidth: 21
            Layout.fillHeight: true
            padding: 0
            text: "−∞"
            font.pixelSize: 11
            Accessible.name: root.label + " silence"
            ToolTip.visible: hovered
            ToolTip.text: qsTr("Set configured level to silence")
            onClicked: root.finish(null)
        }
    }
    Label {
        visible: !root.compact
        text: root.conflict ? qsTr("Edit cancelled") : ""
        Layout.fillWidth: true
        Layout.minimumHeight: root.compact ? 12 : 16
        Layout.preferredHeight: root.compact ? 12 : 16
        Layout.maximumHeight: root.compact ? 12 : 16
        horizontalAlignment: Text.AlignHCenter
        elide: Text.ElideRight
        font.pixelSize: 9
        ToolTip.visible: root.conflict && editHover.hovered
        ToolTip.text: qsTr("State changed; edit will be discarded")
        HoverHandler { id: editHover }
    }
}
