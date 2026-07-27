@echo off
title Search iPhone Texts
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

echo ============================================================
echo   Search your iPhone texts
echo   Type words to look for and press Enter (no quotation marks needed).
echo   Leave it blank and press Enter to quit.
echo ============================================================

:loop
echo.
set "q="
set /p "q=Search for: "
if not defined q goto end
%PY% "%~dp0search.py" "%q%"
goto loop

:end
endlocal
