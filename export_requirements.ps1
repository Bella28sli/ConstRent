#!/usr/bin/env pwsh
# Экспортирует зависимости текущего виртуального окружения в requirements.txt

if (-not (Get-Command pip -ErrorAction SilentlyContinue)) {
    Write-Error "pip не найден в PATH. Активируйте виртуальное окружение и повторите."
    exit 1
}

Write-Host "Экспорт зависимостей в requirements.txt..."
pip freeze > requirements.txt
Write-Host "Готово: requirements.txt обновлён."
