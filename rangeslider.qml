import QtQuick 2.6
import QtQuick.Controls 2.0

Pane {
    
    id: pane

    readonly property int itemWidth: Math.max(slider.implicitWidth, Math.min(slider.implicitWidth * 2, pane.availableWidth / 3))

    Column {
        spacing: 40
        anchors.fill: parent

        RangeSlider {
            id: slider
            first.value: 0.25
            second.value: 0.75
            width: itemWidth
            hoverEnabled: true
            antialiasing: true
            wheelEnabled: true
            clip: false
            anchors.horizontalCenter: parent.horizontalCenter
        }
    }
}
