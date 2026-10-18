@echo off
rem Little Prince 3D prototype - local server (ASCII only in this file)
rem python-path.txt (gitignored) can override the interpreter.
cd /d %~dp0web
set PY=python
if exist "%~dp0..\python-path.txt" set /p PY=<"%~dp0..\python-path.txt"
start "" http://127.0.0.1:8850/
"%PY%" -m http.server 8850 --bind 127.0.0.1
