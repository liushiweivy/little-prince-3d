@echo off
rem Little Prince desktop launcher.
rem Runs the built release exe; builds it first if missing (first build takes 10-20 min).
setlocal
set "EXE=%~dp0src-tauri\target\release\little-prince.exe"
if exist "%EXE%" (
  start "" "%EXE%"
  exit /b 0
)
echo [little-prince] exe not found, building...
set "PATH=%USERPROFILE%\.cargo\bin;%PATH%"
cd /d "%~dp0"
call npm run tauri:build
if exist "%EXE%" (
  start "" "%EXE%"
) else (
  echo [little-prince] build failed, see output above
  pause
)
