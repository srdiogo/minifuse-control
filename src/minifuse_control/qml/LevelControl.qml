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
    property bool dirty: false
    property bool conflict: false
    property real preview: minimum
    property bool released: false
    signal adjusted(var value, bool finish)
    signal cancelled()
    signal committed(var value)
    signal conflicted()
    spacing: 6

    function reset() { dirty = false; released = false; conflict = false; numeric.text = displayText(); numeric.focus = false }
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
    onConfirmedChanged: { if (!numeric.activeFocus) numeric.text = displayText() }

    Label { text: root.label; Layout.alignment: Qt.AlignHCenter; font.pixelSize: 12 }
    Label {
        text: root.dirty ? root.preview.toFixed(1) + " dB · adjusting" : root.displayText() + " dB"
        Layout.alignment: Qt.AlignHCenter
        font.family: "monospace"
        font.pixelSize: 12
        Accessible.name: root.label + " configured level " + text
    }
    Slider {
        id: slider
        objectName: "levelSlider"
        Layout.fillHeight: root.vertical
        Layout.fillWidth: !root.vertical
        Layout.alignment: Qt.AlignHCenter
        Layout.minimumHeight: root.vertical ? 130 : 34
        orientation: root.vertical ? Qt.Vertical : Qt.Horizontal
        from: root.minimum
        to: root.maximum
        stepSize: 0.25
        value: root.dirty ? root.preview : (root.confirmed === null ? root.minimum : root.confirmed)
        Accessible.name: root.label + " configured level"
        onMoved: {
            root.track(value, !pressed)
        }
        onPressedChanged: {
            if (pressed) root.released = false
            else if (root.dirty && !root.released) root.track(value, true)
        }
        Keys.onEscapePressed: { root.cancelled(); root.reset() }
    }
    RowLayout {
        Layout.alignment: Qt.AlignHCenter
        TextField {
            id: numeric
            Layout.preferredWidth: 66
            horizontalAlignment: Text.AlignHCenter
            text: root.displayText()
            selectByMouse: true
            Accessible.name: root.label + " numeric dB; Enter to apply"
            placeholderText: "dB"
            onAccepted: {
                const normalized = text.trim()
                const value = normalized === "-inf" || normalized === "−∞" ? null : Number(normalized)
                if (value === null || (normalized !== "" && Number.isFinite(value) && value >= root.minimum && value <= root.maximum)) root.finish(value)
                else text = root.displayText()
                focus = false
            }
            onActiveFocusChanged: { if (!activeFocus) text = root.displayText() }
            Keys.onEscapePressed: { root.reset(); focus = false }
        }
        ToolButton { text: "−∞"; Accessible.name: root.label + " silence"; onClicked: root.finish(null) }
    }
    Label { visible: root.conflict; text: qsTr("State changed; edit will be discarded"); wrapMode: Text.Wrap; Layout.maximumWidth: 140; font.pixelSize: 11 }
}
