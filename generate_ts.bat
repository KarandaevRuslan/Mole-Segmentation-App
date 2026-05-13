@echo off
setlocal enabledelayedexpansion

if not exist translations mkdir translations

set "PRO_FILE=pyqt_project.pro"
set "TS_FILE=translations/app_ru.ts"

echo TRANSLATIONS = %TS_FILE% > "%PRO_FILE%"

for /R %%f in (*.py) do (
    set "file=%%f"

    rem исключаем мусорные папки
    echo !file! | findstr /i "\\.venv\\ \\venv\\ \\__pycache__\\ \\build\\ \\dist\\" >nul
    if errorlevel 1 (
        set "rel=!file:%CD%\=!"
        set "rel=!rel:\=/!"
        echo SOURCES += !rel! >> "%PRO_FILE%"
    )
)

C:\Users\secre\anaconda3\pylupdate5.bat "%PRO_FILE%"