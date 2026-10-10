@echo off
chcp 65001 >nul
cd /d "%~dp0"
set "RAR="
if exist "%ProgramFiles%\WinRAR\WinRAR.exe" set "RAR=%ProgramFiles%\WinRAR\WinRAR.exe"
if exist "%ProgramFiles(x86)%\WinRAR\WinRAR.exe" set "RAR=%ProgramFiles(x86)%\WinRAR\WinRAR.exe"
if "%RAR%"=="" (
  echo WinRAR.exe не найден. Установите WinRAR и повторите запуск.
  pause
  exit /b 1
)
"%RAR%" a -r "NewsEditor_Windows.rar" *
echo Создан архив NewsEditor_Windows.rar
pause
