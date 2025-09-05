# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import simpledialog, messagebox
import requests
import os
import sys

# ---------------------------
# إعدادات عامة
# ---------------------------
SYMBOLS = ["BTCUSDT", "DOGEUSDT"]
REFRESH_MS = 2000
PAD_X = 12
STARTUP_BAT_NAME = "CS_Binance_startup.bat"

# مسارات Startup
STARTUP_FOLDER = os.path.join(
    os.getenv("APPDATA", ""),
    "Microsoft", "Windows", "Start Menu", "Programs", "Startup"
)
STARTUP_BAT_PATH = os.path.join(STARTUP_FOLDER, STARTUP_BAT_NAME)

# ---------------------------
# إعداد الأيقونة
# ---------------------------
ICON_PATH = os.path.join(os.path.dirname(__file__), "icon.ico")

def set_window_icon(root):
    if os.path.exists(ICON_PATH):
        try:
            root.iconbitmap(ICON_PATH)
        except Exception as e:
            print("تحذير: لم يتم تحميل الأيقونة:", e)

# ---------------------------
# دوال Binance
# ---------------------------
def fetch_price(sym: str):
    try:
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={sym}"
        r = requests.get(url, timeout=6)
        data = r.json()
        if isinstance(data, dict) and "price" in data:
            return float(data["price"])
    except Exception:
        pass
    return None

def fetch_all_prices():
    out = {}
    for s in SYMBOLS:
        p = fetch_price(s)
        out[s] = p if p is not None else "N/A"
    return out

# ---------------------------
# startup helpers
# ---------------------------
def is_startup_enabled() -> bool:
    return os.path.exists(STARTUP_BAT_PATH)

def enable_startup():
    try:
        os.makedirs(STARTUP_FOLDER, exist_ok=True)
        with open(STARTUP_BAT_PATH, "w", encoding="utf-8") as f:
            py = sys.executable
            f.write(f'start "" "{py}" "{os.path.abspath(sys.argv[0])}"\r\n')
        start_var.set(True)
        messagebox.showinfo("Startup", "تم تفعيل التشغيل مع الويندوز.")
    except Exception as e:
        messagebox.showerror("Startup Error", f"خطأ أثناء تفعيل التشغيل مع الويندوز:\n{e}")

def disable_startup():
    try:
        if os.path.exists(STARTUP_BAT_PATH):
            os.remove(STARTUP_BAT_PATH)
        start_var.set(False)
        messagebox.showinfo("Startup", "تم تعطيل التشغيل مع الويندوز.")
    except Exception as e:
        messagebox.showerror("Startup Error", f"خطأ أثناء تعطيل التشغيل:\n{e}")

def toggle_startup():
    if start_var.get():
        enable_startup()
    else:
        disable_startup()

# ---------------------------
# التحكم في الواجهة
# ---------------------------
def normalize_symbol(inp: str) -> str:
    s = inp.strip().upper()
    if not s:
        return s
    if not s.endswith("USDT") and not s.endswith("BUSD") and not s.endswith("BTC") and not s.endswith("ETH"):
        s = s + "USDT"
    return s

def add_symbol_interactive():
    while True:
        ans = simpledialog.askstring("إضافة عملة", "أدخل رمز العملة (مثال: BTC أو BTCUSDT):")
        if ans is None:
            return
        sym = normalize_symbol(ans)
        if not sym:
            return
        p = fetch_price(sym)
        if p is None:
            retry = messagebox.askretrycancel("رمز غير صحيح", f"الرمز '{sym}' غير صالح أو غير متاح في Binance.\nهل تريد المحاولة مجددًا؟")
            if retry:
                continue
            else:
                return
        if sym not in SYMBOLS:
            SYMBOLS.append(sym)
            messagebox.showinfo("تم", f"تمت إضافة {sym}")
        else:
            messagebox.showinfo("معلومة", f"{sym} موجود مسبقًا.")
        refresh_now()
        return

def remove_symbol_interactive():
    ans = simpledialog.askstring("حذف عملة", "أدخل رمز العملة للحذف (مثال: BTC أو BTCUSDT):")
    if ans is None or not ans.strip():
        return
    sym = normalize_symbol(ans)
    if sym in SYMBOLS:
        SYMBOLS.remove(sym)
        messagebox.showinfo("تم", f"تم حذف {sym}")
        refresh_now()
    else:
        messagebox.showerror("خطأ", f"{sym} غير موجود في القائمة.")

# ---------------------------
# واجهة العرض / التحديث
# ---------------------------
def refresh_now():
    try:
        prices = fetch_all_prices()
    except Exception as e:
        prices = {}
    for w in content_frame.winfo_children():
        w.destroy()
    labels.clear()

    for s, p in prices.items():
        txt = f"{s}: {p if isinstance(p, str) else format_price(p)}"
        lbl = tk.Label(content_frame, text=txt, font=("Consolas", 10), bg="black", fg="lime", anchor="w", padx=PAD_X, pady=2)
        lbl.pack(fill="x")
        labels[s] = lbl

    root.update_idletasks()
    root.geometry("")

def format_price(value):
    try:
        if value >= 1000:
            return f"{value:,.0f}"
        if value >= 1:
            return f"{value:,.4f}"
        return f"{value:.8f}".rstrip("0").rstrip(".")
    except Exception:
        return str(value)

def periodic_update():
    try:
        prices = fetch_all_prices()
        for s, p in prices.items():
            txt = f"{s}: {p if isinstance(p, str) else format_price(p)}"
            if s in labels:
                labels[s].config(text=txt)
            else:
                lbl = tk.Label(content_frame, text=txt, font=("Consolas", 10), bg="black", fg="lime", anchor="w", padx=PAD_X, pady=2)
                lbl.pack(fill="x")
                labels[s] = lbl
    except Exception as e:
        if "Error" not in labels:
            lbl_err = tk.Label(content_frame, text=f"Error: {e}", font=("Consolas", 9), bg="black", fg="orange", anchor="w", padx=PAD_X, pady=2)
            lbl_err.pack(fill="x")
            labels["Error"] = lbl_err
    finally:
        root.update_idletasks()
        root.geometry("")
        root.after(REFRESH_MS, periodic_update)

# ---------------------------
# القوائم
# ---------------------------
def show_context_menu(event):
    start_var.set(is_startup_enabled())
    context_menu.tk_popup(event.x_root, event.y_root)

def hide_interface():
    root.iconify()

_drag_data = {"x": 0, "y": 0}
def start_move(event):
    _drag_data["x"] = event.x_root
    _drag_data["y"] = event.y_root

def do_move(event):
    dx = event.x_root - _drag_data["x"]
    dy = event.y_root - _drag_data["y"]
    _drag_data["x"] = event.x_root
    _drag_data["y"] = event.y_root
    x = root.winfo_x() + dx
    y = root.winfo_y() + dy
    root.geometry(f"+{x}+{y}")

# ---------------------------
# بناء واجهة المستخدم
# ---------------------------
root = tk.Tk()
root.title("CS | Binance")
root.configure(bg="black")
root.attributes("-topmost", True)
root.resizable(False, False)

# تعيين الأيقونة
set_window_icon(root)

try:
    root.attributes("-toolwindow", True)
except Exception:
    pass

btn_frame = tk.Frame(root, bg="black")
btn_frame.pack(fill="x")

btn_add = tk.Button(btn_frame, text="➕ إضافة", command=add_symbol_interactive, bg="blue", fg="white")
btn_add.pack(side="left", fill="x", expand=True)

btn_remove = tk.Button(btn_frame, text="❌ حذف", command=remove_symbol_interactive, bg="red", fg="white")
btn_remove.pack(side="left", fill="x", expand=True)

drag_area = tk.Frame(root, height=8, bg="black")
drag_area.pack(fill="x")
drag_area.bind("<Button-1>", start_move)
drag_area.bind("<B1-Motion>", do_move)

content_frame = tk.Frame(root, bg="black")
content_frame.pack(fill="both", expand=True)

labels = {}

start_var = tk.BooleanVar(value=is_startup_enabled())
context_menu = tk.Menu(root, tearoff=0)
context_menu.add_checkbutton(label="تشغيل مع الويندوز", variable=start_var, command=toggle_startup)
context_menu.add_command(label="إخفاء الواجهة (Minimize)", command=hide_interface)
context_menu.add_separator()
context_menu.add_command(label="خروج", command=root.destroy)

root.bind("<Button-3>", show_context_menu)
content_frame.bind("<Button-3>", show_context_menu)
btn_frame.bind("<Button-3>", show_context_menu)
drag_area.bind("<Button-3>", show_context_menu)

# ---------------------------
# تحديد مكان النافذة عند الإقلاع (أسفل يمين الشاشة فوق شريط المهام)
# ---------------------------
root.update_idletasks()
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
window_width = 220   # عرض النافذة
window_height = 120  # ارتفاع النافذة

x = screen_width - window_width
y = screen_height - window_height - 40  # 40px = تقدير ارتفاع شريط المهام
root.geometry(f"{window_width}x{window_height}+{x}+{y}")

periodic_update()
root.mainloop()
