@echo off
chcp 65001 >nul
title KDP Puzzle Bot
cd /d "%~dp0"

set PY=
where py >nul 2>nul && set PY=py
if not defined PY where python >nul 2>nul && set PY=python
if not defined PY goto nopython

if not exist ".venv\Scripts\python.exe" (
    echo Первый запуск: готовлю всё нужное, это займёт 1-2 минуты...
    %PY% -m venv .venv
    if errorlevel 1 goto fail
)

echo Проверяю, всё ли установлено...
".venv\Scripts\python.exe" -m pip install -q --disable-pip-version-check -r requirements.txt
if errorlevel 1 goto fail

if not exist ".env" (
    copy ".env.example" ".env" >nul
    echo.
    echo Сейчас откроется файл .env. Вставьте токен бота после BOT_TOKEN= , сохраните файл и закройте Блокнот.
    echo Потом снова запустите start.bat
    notepad ".env"
    pause
    exit /b
)

".venv\Scripts\python.exe" bot.py
echo.
echo Бот остановлен.
pause
exit /b

:nopython
echo Python не найден.
echo Установите Python с сайта python.org - при установке поставьте галочку "Add python.exe to PATH".
echo Потом снова запустите start.bat
start https://www.python.org/downloads/
pause
exit /b

:fail
echo.
echo Не получилось подготовить бота. Сделайте скриншот этого окна и пришлите его Claude.
pause
