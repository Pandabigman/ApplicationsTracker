@echo off
:loop
cls
echo Starting server...
uvicorn app.main:app
echo Server stopped. Press R to restart or any key to exit.
set /p option=
if /I "%option%"=="R" goto loop
