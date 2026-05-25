@echo off
setlocal
cd /d "%~dp0"
powershell -ExecutionPolicy Bypass -File "%~dp0build_release.ps1" %*
set EXITCODE=%errorlevel%
if "%EXITCODE%"=="0" (
    echo.
    echo Build completed successfully.
    if exist "%~dp0release" start "" "%~dp0release"
) else (
    echo.
    echo Build failed. Review the messages above.
    pause
)
exit /b %EXITCODE%
