@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "ROOT=%~dp0"
set "DEPS=%ROOT%.deps"
set "LOCAL_DEVKITPRO=%DEPS%\devkitPro"
set "DOWNLOADS=%DEPS%\downloads"
set "INSTALLER=%DOWNLOADS%\devkitProUpdater-latest.exe"

echo.
echo Soup3DS dependency installer
echo ----------------------------
echo This downloads the official devkitPro updater, installs it under:
echo   %LOCAL_DEVKITPRO%
echo.
echo Notes:
echo   - The devkitPro updater may ask for admin permission.
echo   - On the component screen, choose at least:
echo       Minimal System
echo       NDS Development
echo       3DS Development
echo   - The script will also run pacman for 3ds-dev and nds-dev after the updater exits.
echo.

where powershell >nul 2>nul
if errorlevel 1 (
    echo ERROR: PowerShell was not found. Windows PowerShell is needed to download the installer.
    pause
    exit /b 1
)

if not exist "%DOWNLOADS%" mkdir "%DOWNLOADS%"
if errorlevel 1 (
    echo ERROR: Could not create "%DOWNLOADS%".
    pause
    exit /b 1
)

echo Downloading latest devkitPro updater from GitHub...
set "INSTALLER_PATH=%INSTALLER%"
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ErrorActionPreference = 'Stop';" ^
  "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12;" ^
  "$release = Invoke-RestMethod 'https://api.github.com/repos/devkitPro/installer/releases/latest';" ^
  "$asset = $release.assets | Where-Object { $_.name -match '\.exe$' } | Select-Object -First 1;" ^
  "if (-not $asset) { throw 'No Windows .exe asset was found on the latest devkitPro installer release.' }" ^
  "Invoke-WebRequest $asset.browser_download_url -OutFile $env:INSTALLER_PATH;" ^
  "Write-Host ('Downloaded ' + $asset.name)"

if errorlevel 1 (
    echo.
    echo ERROR: Download failed.
    echo Check your internet connection, then try again.
    pause
    exit /b 1
)

if not exist "%INSTALLER%" (
    echo ERROR: The installer was not downloaded to "%INSTALLER%".
    pause
    exit /b 1
)

echo.
echo Launching devkitPro updater.
echo If it asks for an install folder, use:
echo   %LOCAL_DEVKITPRO%
echo.
echo Waiting for installer to finish...
"%INSTALLER%" /D=%LOCAL_DEVKITPRO%

if errorlevel 1 (
    echo.
    echo ERROR: devkitPro updater reported a problem.
    pause
    exit /b 1
)

set "BASH=%LOCAL_DEVKITPRO%\msys2\usr\bin\bash.exe"
if not exist "%BASH%" (
    echo.
    echo ERROR: Could not find the local MSYS2 shell at:
    echo   %BASH%
    echo Re-run this BAT and make sure Minimal System was selected.
    pause
    exit /b 1
)

echo.
echo Installing the 3DS and DS development package groups...
"%BASH%" --login -lc "pacman -Syu --noconfirm && pacman -S --needed --noconfirm 3ds-dev nds-dev"

if errorlevel 1 (
    echo.
    echo ERROR: pacman could not finish installing 3ds-dev and nds-dev.
    echo You can retry later by running this same BAT again.
    pause
    exit /b 1
)

echo.
echo Checking local dependency folders...
set "MISSING="
if not exist "%LOCAL_DEVKITPRO%\devkitARM" set "MISSING=!MISSING! devkitARM"
if not exist "%LOCAL_DEVKITPRO%\libctru" set "MISSING=!MISSING! libctru"
if not exist "%LOCAL_DEVKITPRO%\citro2d" set "MISSING=!MISSING! citro2d"
if not exist "%LOCAL_DEVKITPRO%\citro3d" set "MISSING=!MISSING! citro3d"
if not exist "%LOCAL_DEVKITPRO%\libnds" set "MISSING=!MISSING! libnds"

if defined MISSING (
    echo WARNING: These expected folders were not found:!MISSING!
    echo Open the devkitPro updater again or run pacman manually from use_soup3ds_deps.bat.
) else (
    echo All expected Soup3DS folders were found.
)

echo.
echo Done.
echo To build generated projects, open use_soup3ds_deps.bat, cd to your project, then run make.
echo To uninstall the local files, use "%LOCAL_DEVKITPRO%\uninst.exe" if it exists, then delete ".deps".
echo.
pause
exit /b 0
