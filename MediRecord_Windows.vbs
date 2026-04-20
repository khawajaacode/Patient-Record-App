' MediRecord Silent Launcher for Windows
' Double-click this file to start MediRecord
' No CMD window will appear

Set WshShell = CreateObject("WScript.Shell")

' Get the folder where this script lives
Dim scriptDir
scriptDir = Left(WScript.ScriptFullName, InStrRev(WScript.ScriptFullName, "\") - 1)

' Check Python is installed
Dim pyCheck
pyCheck = WshShell.Run("python --version", 0, True)
If pyCheck <> 0 Then
    MsgBox "Python is not installed or not found." & vbCrLf & vbCrLf & _
           "Please install Python from https://www.python.org/downloads/" & vbCrLf & _
           "Make sure to check 'Add Python to PATH' during install.", _
           vbCritical, "MediRecord - Python Not Found"
    WScript.Quit
End If

' Run the bat file silently (window style 0 = hidden)
WshShell.Run "cmd /c """ & scriptDir & "\run_windows.bat""", 0, False

' Small pause then show confirmation
WScript.Sleep 2000
MsgBox "MediRecord is starting!" & vbCrLf & vbCrLf & _
       "Your browser will open automatically in a few seconds." & vbCrLf & vbCrLf & _
       "To stop the app, use the system tray or Task Manager.", _
       vbInformation, "MediRecord"
