@echo off
REM Convenience wrapper so you can double-click or run "extract" without typing python.
python "%~dp0extract.py" %*
if %ERRORLEVEL% NEQ 0 pause
