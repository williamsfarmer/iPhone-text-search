@echo off
title Pull iPhone Texts
setlocal
cd /d "%~dp0"

REM Find a real Python (see "Setup - Double Click Me.bat" for why "where" is
REM not trusted - the Microsoft Store puts a fake python.exe on PATH).
set "PY="
python --version >nul 2>nul && set "PY=python"
if not defined PY (
  py --version >nul 2>nul && set "PY=py"
)
if not defined PY (
  echo Python isn't set up yet. Double-click "Setup - Double Click Me" first.
  echo.
  pause
  exit /b 1
)

echo Getting your texts. Keep your iPhone plugged in and UNLOCKED.
echo (If the phone asks "Trust This Computer?", tap Trust and enter your passcode.)
echo.
%PY% "%~dp0pull.py"
if errorlevel 1 (
  echo.
  echo ============================================================
  echo   Something went wrong above and NOTHING was captured.
  echo   Read the message above this line, fix it, then double-click
  echo   "Pull iPhone Texts" again.
  echo ============================================================
  echo.
  pause
  exit /b 1
)

echo.
echo ============================================================
echo   Finished. Read the summary above - especially the DATE RANGE,
echo   so you know how far back your texts were captured.
echo   You can close this window now.
echo ============================================================
pause
