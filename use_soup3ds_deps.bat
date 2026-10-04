@echo off
setlocal EnableExtensions

set "ROOT=%~dp0"
set "LOCAL_DEVKITPRO=%ROOT%.deps\devkitPro"
set "BASH=%LOCAL_DEVKITPRO%\msys2\usr\bin\bash.exe"

if not exist "%BASH%" (
    echo Soup3DS local devkitPro was not found.
    echo Run install_dependencies.bat first.
    pause
    exit /b 1
)

set "PATH=%LOCAL_DEVKITPRO%\msys2\usr\bin;%PATH%"
set "DEVKITPRO=/opt/devkitpro"
set "DEVKITARM=/opt/devkitpro/devkitARM"
set "MSYS2_PATH_TYPE=inherit"
set "CHERE_INVOKING=1"

if "%~1"=="" (
    echo Opening Soup3DS dev shell.
    echo Use: cd /c/path/to/generated-game
    echo Then: make
    "%BASH%" --login -i
) else (
    "%BASH%" --login -lc "%*"
)
