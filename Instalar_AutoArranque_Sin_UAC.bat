@echo off
title Instalador de Auto-Arranque Silencioso
color 0B

net session >nul 2>&1
if %errorLevel% neq 0 (
    powershell -Command "Start-Process '%~0' -Verb RunAs"
    exit /b
)

echo ============================================================
echo   INSTALADOR DE AUTO-ARRANQUE SILENCIOSO PARA DUALSENSE
echo ============================================================
echo.

set "EXE_PATH=%~dp0dist\DualSense_Volume_Control.exe"

if not exist "%EXE_PATH%" (
    echo [!] ERROR: No se encontro el archivo "dist\DualSense_Volume_Control.exe".
    echo     Primero debes ejecutar "Compilar_A_EXE.bat".
    echo.
    pause
    exit /b
)

schtasks /Create /TN "DualSense_Volume_Control_Task" /TR ""%EXE_PATH%" --autostart" /SC ONLOGON /RL HIGHEST /F

if %errorLevel% equ 0 (
    echo.
    echo ============================================================
    echo   ¡INSTALACION DE AUTO-ARRANQUE COMPLETADA CON EXITO!
    echo ============================================================
    echo.
) else (
    echo [!] Error al registrar la tarea programada.
)

pause
