@echo off
title Compilador DualSense Real MMDevice Mic Mute v25
color 0A

echo ============================================================
echo   COMPILANDO SOLUCION DEFINITIVA DE MUTEO REAL (v25)
echo ============================================================
echo.

echo [*] Instalando librerias necesarias...
pip install hidapi pycaw comtypes pyinstaller

echo.
echo [*] Creando ejecutable .EXE...
pyinstaller --onefile --noconsole --name "DualSense_Volume_Control" DualSense_Volume_Control_GUI.py

echo.
echo ============================================================
echo   ¡PROCESO FINALIZADO CON EXITO!
echo   Tu ejecutable .exe esta en la carpeta "dist".
echo ============================================================
echo.
pause
