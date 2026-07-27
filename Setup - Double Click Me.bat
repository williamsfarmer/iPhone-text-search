@echo off
title iPhone Text Search - Setup
setlocal
cd /d "%~dp0"

echo ============================================================
echo    iPhone Text Search  -  one-time setup
echo ============================================================
echo.

REM --- Refuse to run from inside the ZIP (Windows runs it from a Temp folder) ---
echo "%~dp0" | find /i "\Temp\" >nul
if not errorlevel 1 (
  echo It looks like you are running this from INSIDE the downloaded ZIP.
  echo.
  echo Please close this, right-click the .zip file, choose "Extract All...",
  echo open the extracted folder, and double-click "Setup - Double Click Me"
  echo from THERE.
  echo.
  pause
  exit /b 1
)

echo This will:
echo   1. check that Python is installed
echo   2. install the small iPhone connector it needs
echo   3. put two shortcuts on your Desktop
echo.
echo NOTE: you also need Apple's "Apple Devices" app from the Microsoft Store
echo (it is the iPhone driver). If you don't have it yet, install it before
echo using the "Pull iPhone Texts" icon.
echo.

REM --- Find a REAL Python. Do NOT trust "where": stock Windows 11 puts a fake
REM --- python.exe on PATH (a Microsoft Store stub) that "where" matches but that
REM --- is not a working Python. Probe each interpreter directly instead.
set "PY="
python --version >nul 2>nul && set "PY=python"
if not defined PY (
  py --version >nul 2>nul && set "PY=py"
)
if not defined PY (
  echo Python is not installed yet.
  echo.
  echo I'll open the Python download page in your browser.
  echo   1. Click the yellow "Download Python" button.
  echo   2. Run the file it downloads.
  echo   3. On the FIRST screen, CHECK the box "Add python.exe to PATH".
  echo   4. Click "Install Now" and let it finish.
  echo Then come back and double-click this Setup file again.
  echo If it STILL says Python isn't installed, sign out of Windows and back in
  echo (or restart), then run Setup again.
  echo.
  start "" "https://www.python.org/downloads/"
  echo.
  pause
  exit /b 1
)
echo Found Python:
%PY% --version
echo.

REM --- Install the iPhone connector ---
echo Installing the iPhone connector (pymobiledevice3). Please wait...
%PY% -m pip install --upgrade pip >nul 2>nul
%PY% -m pip install --upgrade pymobiledevice3
if errorlevel 1 (
  echo.
  echo Installing pymobiledevice3 failed. If you are on a work/clinic PC it may
  echo be blocked - try a personal PC. Otherwise copy everything in this window
  echo and send it to Claude so it can be fixed.
  echo.
  pause
  exit /b 1
)
echo.

REM --- Create Desktop shortcuts (pass this folder, minus the trailing slash) ---
set "HERE=%~dp0"
set "HERE=%HERE:~0,-1%"
echo Creating Desktop shortcuts...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0make-shortcuts.ps1" "%HERE%"
if errorlevel 1 (
  echo.
  echo Could not create the Desktop shortcuts. If this is a managed work PC its
  echo security policy may block scripts - try a personal PC, or send this window
  echo to Claude.
  echo.
  pause
  exit /b 1
)

echo.
echo ============================================================
echo    Done!  Look on your Desktop for two new icons:
echo.
echo      "Pull iPhone Texts"    - gets your texts onto this PC
echo      "Search iPhone Texts"  - searches them
echo.
echo    Keep THIS folder where it is - the two icons point back to it, so
echo    don't delete or move it. Your actual texts are saved in a separate
echo    private place (not this folder, and not OneDrive).
echo.
echo    Reminder: install the "Apple Devices" app from the Microsoft Store
echo    before using "Pull iPhone Texts", or the phone won't be detected.
echo ============================================================
echo.
pause
