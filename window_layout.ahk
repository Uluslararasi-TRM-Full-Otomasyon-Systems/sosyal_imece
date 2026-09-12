; window_layout.ahk - AutoHotkey Script for 2x3 Grid Window Layout
; This script arranges 6 agent windows in a 2-row x 3-column grid

#NoEnv
#SingleInstance Force
SetWorkingDir %A_ScriptDir%

; Get screen dimensions
SysGet, MonitorWorkArea, MonitorWorkArea
ScreenWidth := MonitorWorkAreaRight - MonitorWorkAreaLeft
ScreenHeight := MonitorWorkAreaBottom - MonitorWorkAreaTop

; Calculate zone dimensions (2 rows x 3 columns)
ZoneWidth := ScreenWidth / 3
ZoneHeight := ScreenHeight / 2

; Define zones (1-6)
Zone1_X := MonitorWorkAreaLeft
Zone1_Y := MonitorWorkAreaTop
Zone1_W := ZoneWidth
Zone1_H := ZoneHeight

Zone2_X := MonitorWorkAreaLeft + ZoneWidth
Zone2_Y := MonitorWorkAreaTop
Zone2_W := ZoneWidth
Zone2_H := ZoneHeight

Zone3_X := MonitorWorkAreaLeft + (ZoneWidth * 2)
Zone3_Y := MonitorWorkAreaTop
Zone3_W := ZoneWidth
Zone3_H := ZoneHeight

Zone4_X := MonitorWorkAreaLeft
Zone4_Y := MonitorWorkAreaTop + ZoneHeight
Zone4_W := ZoneWidth
Zone4_H := ZoneHeight

Zone5_X := MonitorWorkAreaLeft + ZoneWidth
Zone5_Y := MonitorWorkAreaTop + ZoneHeight
Zone5_W := ZoneWidth
Zone5_H := ZoneHeight

Zone6_X := MonitorWorkAreaLeft + (ZoneWidth * 2)
Zone6_Y := MonitorWorkAreaTop + ZoneHeight
Zone6_W := ZoneWidth
Zone6_H := ZoneHeight

; Function to move window to specific zone
MoveWindowToZone(WindowTitle, ZoneX, ZoneY, ZoneW, ZoneH)
{
    WinActivate, %WindowTitle%
    WinWaitActive, %WindowTitle%, , 5
    if ErrorLevel
    {
        OutputDebug, Window not found: %WindowTitle%
        return
    }
    
    WinMove, %WindowTitle%, , ZoneX, ZoneY, ZoneW, ZoneH
    WinSet, Redraw, , %WindowTitle%
    OutputDebug, Moved window %WindowTitle% to zone
    return
}

; Main layout function
ArrangeAllWindows()
{
    ; Wait for windows to be ready
    Sleep, 2000
    
    ; Arrange windows in 2x3 grid
    MoveWindowToZone("Elif", Zone1_X, Zone1_Y, Zone1_W, Zone1_H)
    Sleep, 500
    MoveWindowToZone("Amara", Zone2_X, Zone2_Y, Zone2_W, Zone2_H)
    Sleep, 500
    MoveWindowToZone("Lucia", Zone3_X, Zone3_Y, Zone3_W, Zone3_H)
    Sleep, 500
    MoveWindowToZone("Sophie", Zone4_X, Zone4_Y, Zone4_W, Zone4_H)
    Sleep, 500
    MoveWindowToZone("Emma", Zone5_X, Zone5_Y, Zone5_W, Zone5_H)
    Sleep, 500
    MoveWindowToZone("Yuki", Zone6_X, Zone6_Y, Zone6_W, Zone6_H)
    
    MsgBox, 64, Window Layout, All 6 agent windows arranged in 2x3 grid successfully!, 3
}

; Hotkey to trigger layout
^!l:: ; Ctrl+Alt+L
    ArrangeAllWindows()
    return

; Auto-run on script start
ArrangeAllWindows()
