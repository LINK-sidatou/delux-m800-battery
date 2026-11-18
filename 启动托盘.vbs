' 启动 DELUX 鼠标电量托盘（无控制台窗口）
Set fso = CreateObject("Scripting.FileSystemObject")
dir = fso.GetParentFolderName(WScript.ScriptFullName)

py = "C:\Users\Acer\.workbuddy\binaries\python\versions\3.13.12\pythonw.exe"
If Not fso.FileExists(py) Then py = "pythonw.exe"

Set sh = CreateObject("WScript.Shell")
sh.CurrentDirectory = dir
sh.Run """" & py & """ """ & dir & "\tray.pyw""", 0, False
