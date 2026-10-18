@echo off
title Desinstalador y Cierre Completo de DualSense Control
color 0C

net session >nul 2>&1
if %errorLevel% neq 0 (
    powershell -Command "Start-Process '%~0' -Verb RunAs"
    exit /b
)

echo ============================================================
echo   ELIMINANDO AUTO-ARRANQUE Y CERRANDO PROCESOS DUALSENSE
echo ============================================================
echo.

echo [*] Eliminando Tarea Programada de Windows...
schtasks /Delete /TN "DualSense_Volume_Control_Task" /F >nul 2>&1

echo [*] Cerrando cualquier instancia en ejecucion en segundo plano...
taskkill /F /IM DualSense_Volume_Control.exe >nul 2>&1

echo.
echo ============================================================
echo   ¡PROCESO FINALIZADO Y LIBERADO!
echo ============================================================
echo.
pause
