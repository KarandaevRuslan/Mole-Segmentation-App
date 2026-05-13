@echo off
setlocal

REM === Настройки ===
set "CONDA_ENV=base"
set "CONDA_ROOT=%USERPROFILE%\anaconda3"

REM === Переход в папку, где лежит этот .bat ===
cd /d "%~dp0"

REM === Выбор pythonw.exe ===
if /I "%CONDA_ENV%"=="base" (
    set "PYTHON_EXE=%CONDA_ROOT%\pythonw.exe"
) else (
    set "PYTHON_EXE=%CONDA_ROOT%\envs\%CONDA_ENV%\pythonw.exe"
)

REM === Проверка, что Python существует ===
if not exist "%PYTHON_EXE%" (
    msg * "Python not found: %PYTHON_EXE%"
    exit /b 1
)

REM === Запуск приложения без зависания консоли ===
start "" "%PYTHON_EXE%" "%~dp0main.py"

exit /b 0