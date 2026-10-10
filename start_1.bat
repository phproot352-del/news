@echo off
chcp 65001 >nul
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
  py news_editor.py
) else (
  python news_editor.py
)
if errorlevel 1 pause
