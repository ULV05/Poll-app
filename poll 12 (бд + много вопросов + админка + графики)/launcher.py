import tkinter as tk
import webbrowser
import threading
import subprocess
import os
from tkinter import PhotoImage

BG_COLOR = "#f0f8ff"
TITLE_COLOR = "#2c3e50"
STATUS_COLOR = "#7f8c8d"
HELP_COLOR = "#95a5a6"
BUTTON_BG = "#3498db"
BUTTON_FG = "white"

FONT_TITLE = ("Arial", 12, "bold")
FONT_NORMAL = ("Arial", 12)
FONT_SMALL = ("Arial", 10)

def start_server():
    def run_server():
        try:
            subprocess.run(["python", "app.py"], check=True)
        except subprocess.CalledProcessError as e:
            status_label.config(text=f"Ошибка запуска сервера: {e}")
            open_btn.config(state=tk.NORMAL)
    
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    status_label.config(text="Запуск сервера...")
    root.after(2000, open_browser)

def open_browser():
    try:
        webbrowser.open('http://localhost:5000')
        status_label.config(text="Браузер открыт! Сервер работает")
        open_btn.config(state=tk.DISABLED)
    except Exception as e:
        status_label.config(text=f"Ошибка открытия браузера: {e}")

root = tk.Tk()
root.title("Запуск платформы для опросов")
root.geometry("420x200")
root.configure(bg=BG_COLOR)

if os.path.exists('icon.ico'):
    try:
        root.iconbitmap('icon.ico')
    except Exception:
        pass  

title_label = tk.Label(
    root, 
    text="Платформа для создания и прохождения опросов",
    font=FONT_TITLE,
    bg=BG_COLOR,
    fg=TITLE_COLOR
)
title_label.pack(pady=20)

open_btn = tk.Button(
    root,
    text="Запустить платформу",
    command=start_server,
    font=FONT_NORMAL,
    bg=BUTTON_BG,
    fg=BUTTON_FG,
    padx=20,
    pady=10
)
open_btn.pack(pady=10)

status_label = tk.Label(
    root,
    text="Нажмите кнопку для запуска",
    font=FONT_NORMAL,
    bg=BG_COLOR,
    fg=STATUS_COLOR
)
status_label.pack(pady=10)

help_label = tk.Label(
    root,
    text="После запуска сервер будет работать в фоне.\nЗакройте это окно для остановки сервера.",
    font=FONT_SMALL,
    bg=BG_COLOR,
    fg=HELP_COLOR
)
help_label.pack(pady=10)

root.mainloop()