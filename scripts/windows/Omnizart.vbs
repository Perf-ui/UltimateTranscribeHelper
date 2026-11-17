Option Explicit
Dim shell, files, root, env, python, command
Set shell = CreateObject("WScript.Shell")
Set files = CreateObject("Scripting.FileSystemObject")
root = files.GetParentFolderName(WScript.ScriptFullName)
python = files.BuildPath(root, "runtime\pythonw.exe")
If Not files.FileExists(python) Then
    MsgBox "The Omnizart runtime is missing. Extract the entire ZIP before starting the app.", vbCritical, "Omnizart"
    WScript.Quit 1
End If
Set env = shell.Environment("PROCESS")
env("PATH") = files.BuildPath(root, "runtime\Library\bin") & ";" & files.BuildPath(root, "runtime") & ";" & env("PATH")
env("PYTHONNOUSERSITE") = "1"
env("PYTHONUTF8") = "1"
shell.CurrentDirectory = root
command = Chr(34) & python & Chr(34) & " -m omnizart.desktop.app"
shell.Run command, 0, False
