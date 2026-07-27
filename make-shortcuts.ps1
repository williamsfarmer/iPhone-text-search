# Creates the two Desktop shortcuts. Called by "Setup - Double Click Me.bat".
# The tool folder is passed in as the only argument (no trailing backslash).
param([Parameter(Mandatory = $true)][string]$Here)

$ErrorActionPreference = 'Stop'

# Files extracted from a downloaded ZIP carry the "Mark of the Web", which makes
# Windows pop a security prompt on every launch. Clear it so the Desktop icons
# open cleanly from now on.
Get-ChildItem -LiteralPath $Here -Recurse -File -ErrorAction SilentlyContinue |
    Unblock-File -ErrorAction SilentlyContinue

$ws = New-Object -ComObject WScript.Shell
# GetFolderPath('Desktop') returns the REAL Desktop, including a OneDrive-
# redirected one -- do not hard-code %USERPROFILE%\Desktop.
$desktop = [Environment]::GetFolderPath('Desktop')
$shell32 = Join-Path $env:SystemRoot 'System32\shell32.dll'

function New-Sc {
    param($Name, $Target, $IconIndex, $Desc)
    $linkPath = Join-Path $desktop ($Name + '.lnk')
    $lnk = $ws.CreateShortcut($linkPath)
    $lnk.TargetPath       = (Join-Path $Here $Target)
    $lnk.WorkingDirectory = $Here
    $lnk.IconLocation     = "$shell32,$IconIndex"
    $lnk.Description       = $Desc
    $lnk.Save()
    Write-Host "  created: $linkPath"
}

New-Sc 'Pull iPhone Texts'   'launch-pull.bat'   44 'Pull your iPhone texts onto this PC'
New-Sc 'Search iPhone Texts' 'launch-search.bat' 22 'Search your iPhone texts'
