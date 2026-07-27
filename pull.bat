@echo off
REM Convenience wrapper: pull only the messages off the iPhone, build the corpus.
python "%~dp0pull.py" %*
if %ERRORLEVEL% NEQ 0 pause
