' Launch the DELUX mouse battery tray without a console window.
' Keep this file in the same folder as tray.pyw (it locates tray.pyw by its own path).
Set fso = CreateObject("Scripting.FileSystemObject")
dir = fso.GetParentFolderName(WScript.ScriptFullName)

py = "C:\Users\Acer\.workbuddy\binaries\python\versions\3.13.12\pythonw.exe"
If Not fso.FileExists(py) Then py = "pythonw.exe"

Set sh = CreateObject("WScript.Shell")
sh.CurrentDirectory = dir
sh.Run """" & py & """ """ & dir & "\tray.pyw""", 0, False
