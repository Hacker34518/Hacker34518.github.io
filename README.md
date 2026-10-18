# DualSense Windows Audio & Mic Mute Sync

Herramienta ligera e independiente para Windows que gestiona el audio nativo y el botón físico de silencio del mando **PlayStation 5 DualSense** conectado por cable USB.

![Plataforma](https://img.shields.io/badge/Plataforma-Windows_10%2F11-blue)
![Python](https://img.shields.io/badge/Python-3.8%2B-green)

---

## Características Principales

* **Sincronización de LED Naranja físico**: Al presionar el botón transparente de silencio bajo el logo de PS, se enciende/apaga el LED naranja integrado en el mando.
* **Muteo de Triple Capa (Ganancia Cero)**:
  * Silencio por hardware en el chip DAC USB del DualSense (`Byte 7 = 0x00`).
  * Muteo a nivel de sistema operativo mediante la API nativa de Windows `IMMDeviceEnumerator`.
  * Reducción forzada de ganancia al **0%** (`Scalar 0.0`) en todos los micrófonos activos para evitar filtraciones de audio en **WhatsApp, Discord y navegadores web**.
* **Restauración del Halo Lightbar (Touchpad)**: Mantiene encendida la iluminación azul/blanca oficial alrededor del panel táctil.
* **Sin Avisos de UAC**: Diseñado para ejecutarse en modo usuario estándar sin requerir permisos de Administrador forzados.
* **Auto-Arranque Silencioso**: Incluye scripts para iniciar automáticamente en segundo plano junto con Windows.

---

## Requisito de Hardware Importante

> **El mando debe estar conectado por cable USB.**
> Por limitaciones de firmware de Sony y del perfil de controlador inalámbrico en PC, las funciones de audio (micrófono, altavoz integrado, conector 3.5mm) y los paquetes HID de luces LED (`0x02`) no están disponibles bajo la conexión Bluetooth estándar en Windows.

---

## Cómo Usar / Compilar

### Opción 1: Ejecutar con Python
1. Instala las dependencias necesarias abriendo una terminal en la carpeta del proyecto:
   ```bash
   pip install hidapi pycaw comtypes pyinstaller
   ```
2. Inicia la aplicación ejecutando el script de la interfaz gráfica:
   ```bash
   python DualSense_Volume_Control_GUI.py
   ```

### Opción 2: Compilar a un archivo Ejecutable (.exe)
Si no quieres abrir la terminal cada vez, puedes empaquetar la aplicación:
1. Haz doble clic sobre el archivo **`Compilar_A_EXE.bat`** incluido en la carpeta.
2. El script automatizado utilizará `pyinstaller` para generar un ejecutable optimizado.
3. Encontrarás tu archivo `.exe` final listo para usar dentro de la nueva carpeta llamada `dist/`.

---

## Configuración de Auto-Arranque (Sin UAC)

Para lograr que el programa se abra de forma invisible y automática cada vez que enciendas tu computadora (sin molestas ventanas de confirmación de administrador):

* **Para Activar**: Haz doble clic sobre el archivo **`Instalar_AutoArranque_Sin_UAC.bat`**.
* **Para Desactivar**: Si en algún momento deseas quitarlo o cerrar la herramienta por completo, ejecuta **`Desinstalar_AutoArranque_Y_Cerrar_Proceso.bat`**.

---

## Estructura del Proyecto

* **`DualSense_Volume_Control_GUI.py`**: Código principal con la lógica de control del mando e interfaz.
* **`Compilar_A_EXE.bat`**: Script para compilar el código a binario ejecutable de Windows de forma automática.
* **`Instalar_AutoArranque_Sin_UAC.bat`**: Registra la aplicación en el inicio del sistema.
* **`Desinstalar_AutoArranque_Y_Cerrar_Proceso.bat`**: Limpia el inicio del sistema y detiene el proceso en segundo plano.
* **`LEEME.txt`**: Documentación rápida de usuario en texto plano.
