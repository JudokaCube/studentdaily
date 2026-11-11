import QtQuick
import QtQuick.Controls
import Quickshell
import Quickshell.Io

Rectangle {
    id: root
    property string app: "classes"
    property var status: ({})
    implicitWidth: 32
    implicitHeight: 32
    radius: 0
    color: mouse.containsMouse ? Qt.rgba(0.5, 0.6, 0.7, 0.15) : "transparent"
    readonly property color accent: status.color || status.glyphColor || "#88c0d0"
    Text {
        anchors.centerIn: parent
        text: root.app === "classes" ? "▦" : "▣"
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
    ToolTip.text: root.status.text || (root.app === "classes" ? "StudentDaily" : "KeepItNew")
    Process {
        id: poll
        command: ["sh", "-c", root.app === "classes" ? '"$HOME/.local/bin/classes" status --json' : '"$HOME/.local/bin/system-update" --status']
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
            const command = root.app === "classes"
                ? (event.button === Qt.RightButton ? '"$HOME/.local/bin/classes" reload' : '"$HOME/.local/bin/classes" pin')
                : (event.button === Qt.RightButton ? '"$HOME/.local/bin/system-update" --reload' : '"$HOME/.local/bin/system-update" --open');
            Quickshell.execDetached(["sh", "-c", command]);
        }
    }
}
