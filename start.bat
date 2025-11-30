@echo off
chcp 65001 >nul
title VK Content Analytics - Запуск приложения

echo ========================================
echo   VK Content Analytics
echo   Запуск приложения...
echo ========================================
echo.

:: Проверка наличия Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ОШИБКА] Python не найден!
    echo Установите Python с https://python.org
    pause
    exit /b 1
)

echo [✓] Python найден
echo.

:: Проверка виртуального окружения
if exist ".venv\Scripts\activate.bat" (
    echo [✓] Виртуальное окружение найдено
    call .venv\Scripts\activate.bat
) else (
    echo [!] Виртуальное окружение не найдено, используем глобальный Python
)

:: Проверка установки зависимостей
echo [*] Проверка зависимостей...
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo [!] Зависимости не установлены
    echo [*] Устанавливаем зависимости...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ОШИБКА] Не удалось установить зависимости
        pause
        exit /b 1
    )
)

echo [✓] Все зависимости установлены
echo.

:: Запуск бэкенда в фоновом режиме
echo ========================================
echo   Запуск бэкенда...
echo ========================================
echo [*] URL: http://localhost:8000
echo [*] Docs: http://localhost:8000/docs
echo.

start "VK Analytics Backend" cmd /k "cd /d "%~dp0app" && python -m uvicorn api.contents:app --host 0.0.0.0 --port 8000 --reload"

:: Небольшая задержка
timeout /t 3 /nobreak >nul

:: Запуск фронтенда
echo ========================================
echo   Запуск фронтенда...
echo ========================================
echo [*] URL: http://localhost:3000
echo.

start "VK Analytics Frontend" cmd /k "cd /d "%~dp0frontend" && python -m http.server 3000"

:: Еще одна задержка перед открытием браузера
timeout /t 2 /nobreak >nul

:: Открыть браузер
echo [*] Открываем приложение в браузере...
start http://localhost:3000

echo.
echo ========================================
echo   ✓ Приложение запущено!
echo ========================================
echo.
echo Бэкенд:   http://localhost:8000
echo Фронтенд: http://localhost:3000
echo API Docs: http://localhost:8000/docs
echo.
echo Для остановки закройте оба окна командной строки
echo.
pause
