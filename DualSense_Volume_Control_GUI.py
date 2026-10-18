# -*- coding: utf-8 -*-
"""
DualSense Native Audio & Real IMMDeviceEnumerator Mic Mute Fix (v25)
===================================================================
SOLUCIÓN DEFINITIVA A LA ENTRADA DE AUDIO EN WHATSAPP Y GRABADORAS:

¿Por qué fallaba en la v22/v24?
En las versiones anteriores, `hasattr(dev, 'DataFlow')` devolvía `False` en PyCAW, 
por lo que la consulta a la lista de micrófonos se ignoraba en silencio y Windows 
NUNCA llegaba a aplicar el muteo a los dispositivos de grabación.

SOLUCIÓN EN LA VERSIÓN V25:
1. Enumeración Directa con la API Nativa de Windows (IMMDeviceEnumerator.EnumAudioEndpoints):
   Llama directamente a `eCapture = 1` (Todos los micrófonos/entradas activas) a nivel de API de Windows COM.
2. Muteo Multicanal Estricto:
   - Aplica `SetMute(1)`
   - Ajusta `SetChannelVolumeLevelScalar(0.0)` en CADA canal individual (Canal 1, Canal 2, etc.)
   - Ajusta `SetMasterVolumeLevelScalar(0.0)` a cero absoluto.
3. Muteo Físico de Hardware Sony (Byte 7 = 0x00):
   Corta la ganancia del micrófono interno en el chip USB del mando DualSense.
4. Luz Naranja 🟠 Sincronizada Instantáneamente en el botón del mando.
"""

import sys
import os
import time
import ctypes
import threading
import tkinter as tk
from tkinter import ttk, messagebox

SONY_VID = 0x054C      # Vendor ID Sony
DUALSENSE_PID = 0x0CE6 # Product ID DualSense

class DualSenseHIDController:
    def __init__(self):
        self.device_handle = None
        self.hid = None
        self.last_button_state = False
        self._init_hid()

    def _init_hid(self):
        try:
            import hid
            self.hid = hid
        except ImportError:
            self.hid = None

    def connect(self):
        if not self.hid:
            return False, "Librería 'hid' no instalada."
        try:
            devices = self.hid.enumerate(SONY_VID, DUALSENSE_PID)
            if not devices:
                return False, "No se encontró el mando DualSense USB."

            path = None
            for d in devices:
                up = d.get('usage_page', 0)
                u = d.get('usage', 0)
                if up in (1, 65280) or u in (5, 1) or d.get('interface_number', -1) == 0:
                    path = d['path']
                    break

            if not path:
                path = devices[0]['path']

            self.device_handle = self.hid.device()
            self.device_handle.open_path(path)
            self.device_handle.set_nonblocking(True)
            return True, "Conectado a la Interfaz Principal USB HID."
        except Exception as e:
            return False, str(e)

    def read_mic_button_press_realtime(self):
        if not self.device_handle:
            return False

        latest_data = None
        try:
            while True:
                data = self.device_handle.read(64)
                if not data:
                    break
                latest_data = data
        except Exception:
            pass

        if not latest_data or len(latest_data) < 10:
            return False

        button_pressed = False
        if latest_data[0] == 0x01 and len(latest_data) >= 11:
            button_pressed = bool(latest_data[10] & 0x04)
        elif len(latest_data) >= 10:
            button_pressed = bool((latest_data[9] & 0x04) or (len(latest_data) >= 11 and (latest_data[10] & 0x04)))

        triggered = False
        if button_pressed and not self.last_button_state:
            triggered = True
            self.last_button_state = True
        elif not button_pressed:
            self.last_button_state = False

        return triggered

    def send_audio_activation_report(self, speaker_vol=100, headset_vol=100, mode="both", boost_mode=True, mic_muted=False):
        if not self.device_handle:
            return False

        if speaker_vol <= 0:
            spk_byte = 0x00
        else:
            max_hex = 0x8E if boost_mode else 0x66
            min_hex = 0x3C
            spk_byte = min_hex + int((speaker_vol / 100.0) * (max_hex - min_hex))

        if headset_vol <= 0:
            headset_byte = 0x00
        else:
            headset_byte = 0x1E + int((headset_vol / 100.0) * (0x9D - 0x1E))

        # Corte total de ganancia en el chip USB de Sony (Byte 7 = 0x00) + LED Naranja (Byte 9 = 0x01)
        mic_byte = 0x00 if mic_muted else 0x40
        led_byte = 0x01 if mic_muted else 0x00

        if mode == "speaker":
            mode_byte = 0x7C
        elif mode == "headset":
            mode_byte = 0x4C
        else:
            mode_byte = 0x6C

        report = [0] * 48
        report[0] = 0x02
        report[1] = 0xFF
        report[2] = 0xD7
        report[5] = headset_byte
        report[6] = spk_byte
        report[7] = mic_byte
        report[8] = mode_byte
        report[9] = led_byte

        report[38] = 0x05
        report[39] = 0x03
        report[42] = 0x02
        report[44] = 0x35
        report[47] = 0xE6

        try:
            self.device_handle.write(bytes(report))
            return True
        except Exception:
            return False

    def close(self):
        if self.device_handle:
            try:
                self.device_handle.close()
            except Exception:
                pass
            self.device_handle = None


class DualSenseApp:
    def __init__(self, root):
        self.root = root
        self.root.title("DualSense Native Control & Mic Mute Fix (v25)")
        self.root.geometry("620x490")
        self.root.resizable(False, False)

        self.is_running = False
        self.thread = None
        self.hid_ctrl = DualSenseHIDController()
        self.volume_obj = None
        self.mic_muted = False

        self.root.configure(bg="#1e1e2e")

        lbl_title = tk.Label(
            root, text="DualSense Audio, Lightbar & Real Mic Mute", font=("Segoe UI", 13, "bold"),
            fg="#cdd6f4", bg="#1e1e2e"
        )
        lbl_title.pack(pady=(12, 2))

        self.lbl_dev = tk.Label(
            root, text="USB HID: Desconectado | Direct MMDevice Enum: Listo", font=("Segoe UI", 9, "bold"),
            fg="#89b4fa", bg="#1e1e2e"
        )
        self.lbl_dev.pack(pady=2)

        self.lbl_mic_status = tk.Label(
            root, text="Micrófono Windows: ACTIVO ⚪ (Luz Naranja Apagada)", font=("Segoe UI", 10, "bold"),
            fg="#a6e3a1", bg="#1e1e2e"
        )
        self.lbl_mic_status.pack(pady=4)

        frame_opts = tk.Frame(root, bg="#1e1e2e")
        frame_opts.pack(pady=4)
        
        self.mode_var = tk.StringVar(value="both")
        rb1 = tk.Radiobutton(frame_opts, text="Altavoz + Headset", variable=self.mode_var, value="both", bg="#1e1e2e", fg="#a6e3a1", selectcolor="#181825", activebackground="#1e1e2e")
        rb2 = tk.Radiobutton(frame_opts, text="Solo Altavoz", variable=self.mode_var, value="speaker", bg="#1e1e2e", fg="#89b4fa", selectcolor="#181825", activebackground="#1e1e2e")
        rb1.pack(side="left", padx=5)
        rb2.pack(side="left", padx=5)

        frame_boost = tk.Frame(root, bg="#1e1e2e")
        frame_boost.pack(pady=4)
        self.boost_var = tk.BooleanVar(value=True)
        cb_boost = tk.Checkbutton(
            frame_boost, text="⚡ Potencia Amplificada 100% (Salida Máxima)",
            variable=self.boost_var, bg="#1e1e2e", fg="#f9e2af", selectcolor="#181825", activebackground="#1e1e2e",
            font=("Segoe UI", 9, "bold")
        )
        cb_boost.pack()

        self.lbl_vol = tk.Label(
            root, text="Volumen Windows: --%", font=("Segoe UI", 12, "bold"),
            fg="#a6e3a1", bg="#1e1e2e"
        )
        self.lbl_vol.pack(pady=2)

        frame_toggle = tk.Frame(root, bg="#1e1e2e")
        frame_toggle.pack(pady=6)
        self.btn_toggle_mute = tk.Button(
            frame_toggle, text="🔘 Alternar Mute Real de Micrófonos", font=("Segoe UI", 9, "bold"),
            bg="#fab387", fg="#11111b", activebackground="#f9e2af",
            width=36, height=1, relief="flat", command=self.toggle_mic_mute
        )
        self.btn_toggle_mute.pack()

        frame_buttons = tk.Frame(root, bg="#1e1e2e")
        frame_buttons.pack(pady=8)

        self.btn_start = tk.Button(
            frame_buttons, text="▶ Activar Servicio", font=("Segoe UI", 10, "bold"),
            bg="#a6e3a1", fg="#11111b", activebackground="#94e2d5",
            width=15, height=1, relief="flat", command=self.start_sync
        )
        self.btn_start.pack(side="left", padx=4)

        self.btn_test = tk.Button(
            frame_buttons, text="🔊 Probar Tono", font=("Segoe UI", 10, "bold"),
            bg="#89b4fa", fg="#11111b", activebackground="#b4befe",
            width=13, height=1, relief="flat", command=self.play_test_tone
        )
        self.btn_test.pack(side="left", padx=4)

        self.btn_hide = tk.Button(
            frame_buttons, text="🗕 Segundo Plano", font=("Segoe UI", 10, "bold"),
            bg="#b4befe", fg="#11111b", activebackground="#cba6f7",
            width=15, height=1, relief="flat", command=self.hide_to_background
        )
        self.btn_hide.pack(side="left", padx=4)

        self.btn_stop = tk.Button(
            frame_buttons, text="⏸ Detener", font=("Segoe UI", 10, "bold"),
            bg="#fab387", fg="#11111b", activebackground="#f9e2af",
            width=10, height=1, relief="flat", state="disabled", command=self.stop_sync
        )
        self.btn_stop.pack(side="left", padx=4)

        frame_exit = tk.Frame(root, bg="#1e1e2e")
        frame_exit.pack(pady=4)
        
        self.btn_exit = tk.Button(
            frame_exit, text="✖ Salir del Programa", font=("Segoe UI", 10, "bold"),
            bg="#f38ba8", fg="#11111b", activebackground="#eba0ac",
            width=18, height=1, relief="flat", command=self.exit_app
        )
        self.btn_exit.pack()

        self.root.protocol("WM_DELETE_WINDOW", self.hide_to_background)

        if "--minimized" in sys.argv or "--autostart" in sys.argv:
            self.root.after(500, self.auto_start_minimized)

    def auto_start_minimized(self):
        self.start_sync()
        self.hide_to_background()

    def hide_to_background(self):
        if not self.is_running:
            self.start_sync()
        self.root.withdraw()

    def play_test_tone(self):
        threading.Thread(target=self._generate_and_play_tone, daemon=True).start()

    def _generate_and_play_tone(self):
        try:
            import winsound
            winsound.Beep(880, 500)
        except Exception:
            pass

    def start_sync(self):
        if not self.is_running:
            ok, msg = self.hid_ctrl.connect()

            self.is_running = True
            self.btn_start.config(state="disabled", bg="#6c7086")
            self.btn_stop.config(state="normal", bg="#fab387")
            self.lbl_dev.config(text="USB HID DualSense: MUTEO TOTAL EN WINDOWS ACTIVO", fg="#a6e3a1")

            self.thread = threading.Thread(target=self.audio_loop, daemon=True)
            self.thread.start()

    def stop_sync(self):
        if self.is_running:
            self.is_running = False
            self.hid_ctrl.close()
            self.btn_start.config(state="normal", bg="#a6e3a1")
            self.btn_stop.config(state="disabled", bg="#6c7086")
            self.lbl_dev.config(text="USB HID: Desconectado", fg="#89b4fa")

    def _apply_windows_mic_mute_real_async(self, mute_state):
        """
        Llama directamente a IMMDeviceEnumerator::EnumAudioEndpoints(eCapture=1, DEVICE_STATE_ACTIVE=1)
        para forzar Mute = True/False y Volumen/Ganancia Canal = 0.0/1.0 en TODOS los micrófonos de Windows.
        """
        try:
            import comtypes
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

            comtypes.CoInitialize()

            # 1. Obtener el IMMDeviceEnumerator nativo de Windows
            device_enumerator = AudioUtilities.GetDeviceEnumerator()
            if device_enumerator:
                # EnumAudioEndpoints(eCapture=1, DEVICE_STATE_ACTIVE=1)
                collection = device_enumerator.EnumAudioEndpoints(1, 1)
                count = collection.GetCount()

                for i in range(count):
                    try:
                        imm_device = collection.Item(i)
                        interface = imm_device.Activate(IAudioEndpointVolume._iid_, comtypes.CLSCTX_ALL, None)
                        vol_obj = interface.QueryInterface(IAudioEndpointVolume)

                        if vol_obj:
                            # a) Mute maestro del dispositivo
                            vol_obj.SetMute(1 if mute_state else 0, None)

                            # b) Ganancia de cada canal individual (Ch 0, Ch 1, etc.)
                            ch_count = vol_obj.GetChannelCount()
                            for c in range(ch_count):
                                try:
                                    vol_obj.SetChannelVolumeLevelScalar(c, 0.0 if mute_state else 1.0, None)
                                except Exception:
                                    pass

                            # c) Ganancia maestra
                            try:
                                vol_obj.SetMasterVolumeLevelScalar(0.0 if mute_state else 1.0, None)
                            except Exception:
                                pass
                    except Exception:
                        pass

            comtypes.CoUninitialize()
        except Exception:
            pass

    def toggle_mic_mute(self):
        self.mic_muted = not self.mic_muted

        if self.mic_muted:
            self.update_mic_label("Micrófono Windows: SILENCIADO 🟠 (Ganancia 0% / Silencio Absoluto)", "#fab387")
        else:
            self.update_mic_label("Micrófono Windows: ACTIVO ⚪ (Ganancia 100% / Audio Restaurado)", "#a6e3a1")

        threading.Thread(target=self._apply_windows_mic_mute_real_async, args=(self.mic_muted,), daemon=True).start()

    def audio_loop(self):
        import comtypes
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

        comtypes.CoInitialize()

        try:
            speakers = AudioUtilities.GetSpeakers()
            if hasattr(speakers, 'EndpointVolume'):
                self.volume_obj = speakers.EndpointVolume
            elif hasattr(speakers, 'interface') and hasattr(speakers.interface, 'Activate'):
                interface = speakers.interface.Activate(IAudioEndpointVolume._iid_, comtypes.CLSCTX_ALL, None)
                self.volume_obj = interface.QueryInterface(IAudioEndpointVolume)
        except Exception:
            pass

        while self.is_running:
            try:
                if self.hid_ctrl.read_mic_button_press_realtime():
                    self.toggle_mic_mute()

                win_vol_pct = 100
                if self.volume_obj:
                    if self.volume_obj.GetMute():
                        self.volume_obj.SetMute(0, None)
                    vol_scalar = self.volume_obj.GetMasterVolumeLevelScalar()
                    win_vol_pct = int(vol_scalar * 100)
                    self.update_vol_label(win_vol_pct)

                mode = self.mode_var.get()
                boost = self.boost_var.get()

                self.hid_ctrl.send_audio_activation_report(
                    speaker_vol=win_vol_pct,
                    headset_vol=win_vol_pct,
                    mode=mode,
                    boost_mode=boost,
                    mic_muted=self.mic_muted
                )

            except Exception:
                pass

            time.sleep(0.02)

        comtypes.CoUninitialize()

    def update_vol_label(self, vol_pct):
        self.root.after(0, lambda: self.lbl_vol.config(text=f"Volumen Windows: {vol_pct}%"))

    def update_mic_label(self, text, color):
        self.root.after(0, lambda: self.lbl_mic_status.config(text=text, fg=color))

    def exit_app(self):
        self.is_running = False
        self.hid_ctrl.close()
        self.root.after(200, self.root.destroy)

if __name__ == "__main__":
    root = tk.Tk()
    app = DualSenseApp(root)
    root.mainloop()
