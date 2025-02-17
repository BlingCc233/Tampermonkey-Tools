#Requires AutoHotkey v2.0
#SingleInstance Force ; 确保脚本只运行一个实例

; 创建开机启动快捷方式
if !FileExist(A_Startup "\KeyboardRemap.lnk") {
    FileCreateShortcut A_ScriptFullPath, A_Startup "\KeyboardRemap.lnk"
}

; 初始化变量
CapsLockPressedTime := 0
ShiftState := 0

; 禁用原始的CapsLock和Shift键
*CapsLock::
{
    CapsLockPressedTime := A_TickCount
    KeyWait "CapsLock"
    if (A_TickCount - CapsLockPressedTime < 200)  ; 短按 (<200ms)
    {
        Send "{Shift down}"  ; 模拟按下Shift
        KeyWait "CapsLock"
        Send "{Shift up}"    ; 释放Shift
    }
    else  ; 长按
    {
        SetCapsLockState !GetKeyState("CapsLock", "T")  ; 切换大小写状态
    }
}

; 使Shift保持上档功能
*LShift::
{
    Send "{Shift down}"
    KeyWait "LShift"
    Send "{Shift up}"
}

*RShift::
{
    Send "{Shift down}"
    KeyWait "RShift"
    Send "{Shift up}"
}

; 交换Ctrl和Alt
*LCtrl::LAlt
*LAlt::LCtrl
*RCtrl::RAlt
*RAlt::RCtrl
