# DISCLAIMER:
# This software is designed for educational and administrative purposes only (Exam Monitoring).
# Usage for surveillance without user consent is strictly prohibited and may violate privacy laws.
# The developer assumes no liability for misuse.

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import json
import os
import sys
import threading
import time
import socket
import webbrowser
from datetime import datetime
import mss
import requests
import ftplib
import io
from PIL import Image
import psutil
from smb.SMBConnection import SMBConnection

# --- Настройка DPI ---
try:
    import ctypes
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

RUNNING = False

# ================= ПУТИ И ЛОГИ =================

def get_app_data_dir():
    app_data = os.getenv('APPDATA')
    config_dir = os.path.join(app_data, "ExamMonitor")
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
    return config_dir

SETTINGS_FILE = os.path.join(get_app_data_dir(), "settings.json")
LOG_FILE = os.path.join(get_app_data_dir(), "agent.log")

def log_message(message):
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {message}\n")
    except:
        pass

# ================= НАСТРОЙКИ =================

def load_settings():
    default_settings = {
        "mode": "SMB", # По умолчанию SMB
        "url_host": "192.168.1.5/Public",
        "ftp_user": "",
        "ftp_pass": "",
        "interval": 10,
        "start_hour": 9,
        "start_min": 0,
        "end_hour": 14,
        "end_min": 0
    }
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                data = json.load(f)
                if "start_min" not in data: data["start_min"] = 0
                if "end_min" not in data: data["end_min"] = 0
                return data
        except Exception as e:
            log_message(f"Err load settings: {e}")
            return default_settings
    return default_settings

def save_settings(data):
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(data, f)
    except Exception as e:
        log_message(f"Err save settings: {e}")
        messagebox.showerror("Ошибка", str(e))

# ================= ЯДРО =================

def take_screenshot_and_send(settings):
    pc_name = socket.gethostname()
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{pc_name}_{timestamp}.png"

    try:
        with mss.mss() as sct:
            sct_img = sct.grab(sct.monitors[1])
            img_bytes = mss.tools.to_png(sct_img.rgb, sct_img.size)

            # --- SMB ---
            if settings["mode"] == "SMB":
                # Формат: IP/ShareName
                raw_url = settings["url_host"].replace("\\", "/")
                parts = raw_url.split("/", 1)
                server_ip = parts[0]
                share_name = parts[1] if len(parts) > 1 else "public" 
                
                # Формат: DOMAIN\User
                user_full = settings["ftp_user"]
                if "\\" in user_full:
                    domain, username = user_full.split("\\", 1)
                else:
                    domain = pc_name 
                    username = user_full

                password = settings["ftp_pass"]
                
                conn = SMBConnection(username, password, pc_name, server_ip, domain=domain, use_ntlm_v2=True)
                connected = conn.connect(server_ip, 445)
                
                if connected:
                    bio = io.BytesIO(img_bytes)
                    conn.storeFile(share_name, f"/{filename}", bio)
                    conn.close()
                else:
                    log_message("SMB Connect failed")

            # --- FTP ---
            elif settings["mode"] == "FTP":
                bio = io.BytesIO(img_bytes)
                with ftplib.FTP(settings["url_host"]) as ftp:
                    ftp.login(user=settings["ftp_user"], passwd=settings["ftp_pass"])
                    ftp.set_pasv(True)
                    ftp.storbinary(f"STOR {filename}", bio)

            # --- HTTP ---
            elif settings["mode"] == "HTTP":
                files = {'file': (filename, img_bytes)}
                requests.post(settings["url_host"], files=files, timeout=10)

    except Exception as e:
        log_message(f"Ошибка отправки ({settings['mode']}): {e}")

def monitor_loop():
    global RUNNING
    RUNNING = True
    settings = load_settings()
    log_message(f"Мониторинг запущен. Режим: {settings.get('mode')}")
    
    while RUNNING:
        try:
            now = datetime.now()
            current_minutes = now.hour * 60 + now.minute
            
            start_total = int(settings.get("start_hour", 9)) * 60 + int(settings.get("start_min", 0))
            end_total = int(settings.get("end_hour", 14)) * 60 + int(settings.get("end_min", 0))

            if start_total <= current_minutes < end_total:
                take_screenshot_and_send(settings)
            
            time.sleep(int(settings.get("interval", 60)))
            
        except Exception as e:
            log_message(f"Loop error: {e}")
            time.sleep(60)

def start_monitor_thread():
    if not RUNNING:
        t = threading.Thread(target=monitor_loop, daemon=True)
        t.start()

def kill_other_instances():
    current_pid = os.getpid()
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            proc_name = proc.info['name'].lower()
            # ТЕПЕРЬ ИЩЕМ ExamMonAgent.exe
            if (proc_name == "exammonagent.exe") and proc.info['pid'] != current_pid:
                proc.kill()
        except:
            pass

# ================= GUI =================

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Disclaimer
        if not os.path.exists(SETTINGS_FILE):
            root = tk.Tk()
            root.withdraw()
            msg = ("ВНИМАНИЕ!\n\n"
                   "Эта программа предназначена для администрирования учебного процесса.\n"
                   "Использование программы для скрытого наблюдения без ведома пользователей "
                   "может нарушать законодательство.\n\n"
                   "Нажимая 'Да', вы подтверждаете легальность использования ПО.")
            answer = messagebox.askyesno("Легальное использование", msg, icon='warning')
            root.destroy()
            if not answer: sys.exit()

        self.title("Exam Monitor Agent")
        self.geometry("450x650")

        try:
            self.iconbitmap(resource_path("icon.ico"))
        except: pass

        self.settings = load_settings()

        self.lbl_title = ctk.CTkLabel(self, text="Настройка Агента", font=("Segoe UI", 24, "bold"))
        self.lbl_title.pack(pady=(15, 5))

        # Поля
        ctk.CTkLabel(self, text="Режим отправки:", font=("Segoe UI", 12)).pack(pady=(2, 0))
        self.mode_var = ctk.StringVar(value=self.settings.get("mode", "SMB"))
        # НОВЫЙ ПОРЯДОК: SMB, FTP, HTTP
        self.combo_mode = ctk.CTkComboBox(self, values=["SMB", "FTP", "HTTP"], variable=self.mode_var, width=300)
        self.combo_mode.pack(pady=2)

        ctk.CTkLabel(self, text="URL / IP (Для SMB: IP/Папка):", font=("Segoe UI", 12)).pack(pady=(2, 0))
        self.entry_url = ctk.CTkEntry(self, width=300)
        self.entry_url.insert(0, self.settings.get("url_host", ""))
        self.entry_url.pack(pady=2)

        ctk.CTkLabel(self, text="Логин (Для SMB: DOMAIN\\User):", font=("Segoe UI", 12)).pack(pady=(2, 0))
        self.entry_user = ctk.CTkEntry(self, width=300)
        self.entry_user.insert(0, self.settings.get("ftp_user", ""))
        self.entry_user.pack(pady=2)

        ctk.CTkLabel(self, text="Пароль:", font=("Segoe UI", 12)).pack(pady=(2, 0))
        self.entry_pass = ctk.CTkEntry(self, width=300, show="*")
        self.entry_pass.insert(0, self.settings.get("ftp_pass", ""))
        self.entry_pass.pack(pady=2)

        ctk.CTkLabel(self, text="Интервал (сек):", font=("Segoe UI", 12)).pack(pady=(2, 0))
        self.entry_interval = ctk.CTkEntry(self, width=100)
        self.entry_interval.insert(0, str(self.settings.get("interval", "10")))
        self.entry_interval.pack(pady=2)

        # Время
        ctk.CTkLabel(self, text="Время работы (ЧЧ:ММ):", font=("Segoe UI", 12)).pack(pady=(10, 0))
        frame_time = ctk.CTkFrame(self, fg_color="transparent")
        frame_time.pack(pady=5)
        
        self.entry_start_h = ctk.CTkEntry(frame_time, width=40)
        self.entry_start_h.insert(0, str(self.settings.get("start_hour", "9")))
        self.entry_start_h.pack(side="left", padx=2)
        ctk.CTkLabel(frame_time, text=":").pack(side="left")
        self.entry_start_m = ctk.CTkEntry(frame_time, width=40)
        self.entry_start_m.insert(0, str(self.settings.get("start_min", "0")))
        self.entry_start_m.pack(side="left", padx=2)

        ctk.CTkLabel(frame_time, text=" — ").pack(side="left", padx=10)

        self.entry_end_h = ctk.CTkEntry(frame_time, width=40)
        self.entry_end_h.insert(0, str(self.settings.get("end_hour", "14")))
        self.entry_end_h.pack(side="left", padx=2)
        ctk.CTkLabel(frame_time, text=":").pack(side="left")
        self.entry_end_m = ctk.CTkEntry(frame_time, width=40)
        self.entry_end_m.insert(0, str(self.settings.get("end_min", "0")))
        self.entry_end_m.pack(side="left", padx=2)

        # Кнопки
        self.btn_save = ctk.CTkButton(self, text="Сохранить и Запустить", 
                                      command=self.on_save_start,
                                      height=45, width=300, 
                                      font=("Segoe UI", 14, "bold"),
                                      fg_color="green", hover_color="darkgreen")
        self.btn_save.pack(pady=(20, 5)) 

        self.btn_info = ctk.CTkButton(self, text="О программе", 
                                      command=self.open_about_window,
                                      fg_color="transparent", 
                                      text_color="gray",
                                      hover_color=("gray90", "gray20"),
                                      font=("Segoe UI", 12),
                                      height=30)
        self.btn_info.pack(side="bottom", pady=10)

    def on_save_start(self):
        try:
            new_settings = {
                "mode": self.mode_var.get(),
                "url_host": self.entry_url.get(),
                "ftp_user": self.entry_user.get(),
                "ftp_pass": self.entry_pass.get(),
                "interval": int(self.entry_interval.get()),
                "start_hour": int(self.entry_start_h.get()),
                "start_min": int(self.entry_start_m.get()),
                "end_hour": int(self.entry_end_h.get()),
                "end_min": int(self.entry_end_m.get())
            }
            save_settings(new_settings)
            start_monitor_thread()
            self.withdraw()
        except ValueError:
            messagebox.showerror("Ошибка", "Проверьте числа в полях времени.")

    def open_about_window(self):
        about_window = ctk.CTkToplevel(self)
        about_window.title("О программе")
        about_window.geometry("320x350")
        about_window.attributes("-topmost", True)
        try:
            img_path = resource_path("logo.png")
            if os.path.exists(img_path):
                pil_image = Image.open(img_path)
                logo_img = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=(200, 80))
                lbl_logo = ctk.CTkLabel(about_window, text="", image=logo_img)
                lbl_logo.pack(pady=(30, 10))
        except: pass
        ctk.CTkLabel(about_window, text="Exam Monitor Agent", font=("Segoe UI", 18, "bold")).pack(pady=(5,0))
        ctk.CTkLabel(about_window, text="Разработчик", text_color="gray", font=("Segoe UI", 12)).pack(pady=(10,0))
        link = ctk.CTkLabel(about_window, text="APP-Develop.Ru", font=("Segoe UI", 14, "underline"), 
                            text_color=("#3B8ED0", "#1F6AA5"), cursor="hand2")
        link.pack(pady=5)
        link.bind("<Button-1>", lambda e: webbrowser.open("https://app-develop.ru"))
        ctk.CTkLabel(about_window, text="Версия 2.2", font=("Segoe UI", 10), text_color="gray").pack(side="bottom", pady=20)

# --- ЗАЩИТА: Timebomb ---
def check_license_date():
    LIMIT_DATE = datetime(2026, 1, 20)
    if datetime.now() > LIMIT_DATE:
        is_silent = (len(sys.argv) > 1 and sys.argv[1] == "--silent")
        if not is_silent:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Лицензия истекла", "Срок действия бета-версии истек (20.01.2026).")
            root.destroy()
        sys.exit()

if __name__ == "__main__":
    check_license_date()

    is_silent = (len(sys.argv) > 1 and sys.argv[1] == "--silent")
    if not is_silent: kill_other_instances()
    
    app = App()
    
    if is_silent:
        if os.path.exists(SETTINGS_FILE):
            start_monitor_thread()
            app.withdraw()
        else: sys.exit()
    app.mainloop()
