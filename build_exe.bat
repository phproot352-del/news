@echo off
chcp 65001 >nul
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (set PY=py) else (set PY=python)
%PY% -m pip install --upgrade pyinstaller
%PY% -m PyInstaller --noconfirm --clean --onefile --windowed --name NewsEditor news_editor.py
if exist dist\NewsEditor.exe (
  echo.
  echo Готово: dist\NewsEditor.exe
) else (
  echo Не удалось собрать EXE.
)
pause
