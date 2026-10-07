$WshShell = New-Object -ComObject WScript.Shell
$DesktopPath = [System.Environment]::GetFolderPath("Desktop")
$ShortcutPath = Join-Path $DesktopPath "AI Job Search Dashboard.lnk"
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = "C:\Users\91879\Desktop\Launch AI Job Search.bat"
$Shortcut.WorkingDirectory = "d:\AI AUTOMATION\ai job search"
$Shortcut.Description = "Launch AI Job Search Assistant Dashboard"
$Shortcut.Save()
Write-Host "Created Desktop Shortcut: $ShortcutPath"
