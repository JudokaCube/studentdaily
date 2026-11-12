import QtQuick
import QtQuick.Controls
import Quickshell
import Quickshell.Io

Rectangle {
    id: root
    property var status: ({})
    visible: status.visible !== false
    implicitWidth: visible ? 32 : 0
    implicitHeight: visible ? 32 : 0
    radius: 0
    color: mouse.containsMouse ? Qt.rgba(0.5, 0.6, 0.7, 0.15) : "transparent"
    readonly property color accent: status.color || status.glyphColor || "#88c0d0"
    Text {
        anchors.centerIn: parent
        text: "▦"
        color: root.accent
        font.pixelSize: 20
    }
    Rectangle {
        anchors.left: parent.left
        anchors.bottom: parent.bottom
        height: 2
        width: parent.width * Math.max(0, Math.min(100, root.status.classProgress || 0)) / 100
        color: root.accent
        visible: root.status.classProgress !== undefined && root.status.classProgress !== null
    }
    ToolTip.visible: mouse.containsMouse || (root.status.expandUntil || 0) * 1000 > Date.now()
    ToolTip.text: root.status.text || "StudentDaily"
    Process {
        id: poll
        command: ["sh", "-c", 'if command -v studentdaily >/dev/null 2>&1; then studentdaily status --json; else "$HOME/.local/bin/classes" status --json; fi']
        stdout: StdioCollector {
            onStreamFinished: {
                try { root.status = JSON.parse(text); } catch (error) { console.warn("App status unavailable:", error); }
            }
        }
    }
    Timer { interval: 10000; running: true; repeat: true; triggeredOnStart: true; onTriggered: { if (!poll.running) poll.running = true; } }
    MouseArea {
        id: mouse
        anchors.fill: parent
        hoverEnabled: true
        acceptedButtons: Qt.LeftButton | Qt.RightButton
        onClicked: event => {
            const command = event.button === Qt.RightButton ? 'if command -v studentdaily >/dev/null 2>&1; then studentdaily reload; else "$HOME/.local/bin/classes" reload; fi' : 'if command -v studentdaily >/dev/null 2>&1; then studentdaily pin; else "$HOME/.local/bin/classes" pin; fi';
            Quickshell.execDetached(["sh", "-c", command]);
        }
    }
}
