"""
AFK Bot GUI with Professional Silent Auto-Updater
Author: Killed9 / ChatGPT

Features:
- License checking
- GUI with Tkinter
- Auto-update via Gofile (version.txt + script swap & restart)
- Full title in red (no black AFK)
"""

import tkinter as tk
from tkinter import scrolledtext
from PIL import Image, ImageTk
import threading
import time
import os
import random
import unicodedata
import re
from datetime import datetime
import cv2
import numpy as np
import subprocess
import webbrowser
import hashlib
import json
import requests
import pyautogui
import keyboard
import sys
import shutil

# ====== CONFIGURABLE CONSTANTS ======
APP_NAME = "KILLERAFK"
OWNER_ID = "oAiDnmxnGr"
APP_VERSION = "1.3"  # <-- Bump with each release
LICENSE_FILE = "license.json"
DISCORD_INVITE_URL = "https://discord.gg/vmUP8CzZSe"

GOFILE_VERSION_URL = "https://raw.githubusercontent.com/Killed9/AFKkiller/main/version.txt"
GOFILE_SCRIPT_URL  = "https://raw.githubusercontent.com/Killed9/AFKkiller/main/afk_bot_gui.py"
UPDATE_SCRIPT_NAME = "afk_bot_gui_update.py"
UPDATER_HELPER_NAME = "update_helper.py"
MAIN_SCRIPT_NAME = os.path.basename(__file__)

COLOR_BG = "#141214"
COLOR_BG_OVERLAY = "#1c181b"
COLOR_BTN = "#c01626"
COLOR_BTN_HOVER = "#fa2e49"
COLOR_BTN_STOP = "#18181b"
COLOR_BTN_STOP_HOVER = "#33333b"
COLOR_TEXT = "#f5f5f5"
COLOR_STATUS_GO = "#1de986"
COLOR_STATUS_STOP = "#e60d26"
WINDOW_W, WINDOW_H = 570, 350
BG_IMAGE_PATH = "reaper_bg.png"

window_title = "Call of Duty®"
TEMPLATE_FOLDER = r"C:\Users\andre\Downloads\Velo Booster v1.1.5\UI"
class_order = [
    "menu_x4",
    "black_ops_button",
    "black_ops_button_hovered",
    "multiplayer_button",
    "multiplayer_button_hovered",
    "find_a_match_button",
    "find_a_match_button_hovered",
    "party_games",
    "party_games_hovered",
    "prop_hunt_button",
    "prop_hunt_button_hovered"
]
THRESHOLD = 0.80
AUMID = "38985CA0.COREBase_5bkah9njm3e9g!codShip"

# ====== AUTO-UPDATER FUNCTIONS ======

def log_update_status(msg):
    """Default log for updater before GUI is available."""
    print("[UPDATE]", msg)

def check_for_update(current_version, log_func=log_update_status):
    """Check Gofile for a new version. Returns (needs_update, latest_version)."""
    try:
        resp = requests.get(GOFILE_VERSION_URL, timeout=6)
        resp.raise_for_status()
        latest_version = resp.text.strip()
        if latest_version != current_version:
            log_func(f"New version available: {latest_version}")
            return True, latest_version
        return False, latest_version
    except Exception as e:
        log_func(f"Update check failed: {e}")
        return False, None

def download_latest_script(log_func=log_update_status):
    """Download the latest script from Gofile."""
    try:
        resp = requests.get(GOFILE_SCRIPT_URL, timeout=12)
        resp.raise_for_status()
        with open(UPDATE_SCRIPT_NAME, "wb") as f:
            f.write(resp.content)
        log_func("Downloaded latest script successfully.")
        return True
    except Exception as e:
        log_func(f"Failed to download update: {e}")
        return False

def run_update_helper():
    """Create and run a temporary script to swap in the new file and relaunch."""
    with open(UPDATER_HELPER_NAME, "w") as f:
        f.write(f"""
import os
import sys
import time
import shutil
import subprocess

time.sleep(1.5)
tries = 0
while True:
    try:
        os.remove("{MAIN_SCRIPT_NAME}")
        break
    except Exception:
        tries += 1
        if tries > 12:
            print("Failed to delete old main script after multiple tries.")
            sys.exit(1)
        time.sleep(1)
try:
    shutil.move("{UPDATE_SCRIPT_NAME}", "{MAIN_SCRIPT_NAME}")
except Exception as e:
    print("Failed to move update:", e)
    sys.exit(1)
try:
    subprocess.Popen([sys.executable, "{MAIN_SCRIPT_NAME}"])
except Exception as e:
    print("Failed to restart new version:", e)
sys.exit(0)
""")
    subprocess.Popen([sys.executable, UPDATER_HELPER_NAME])
    sys.exit(0)

def auto_update_if_needed(log_func=log_update_status):
    """Check, download, and install update if needed."""
    needs_update, latest_version = check_for_update(APP_VERSION, log_func=log_func)
    if needs_update:
        ok = download_latest_script(log_func=log_func)
        if ok:
            log_func(f"Updating to version {latest_version} and restarting...")
            run_update_helper()
        else:
            log_func("Update download failed. Running current version.")
    else:
        log_func("No update needed.")

# ====== LICENSE & UTILS ======

def save_license_key(key):
    try:
        with open(LICENSE_FILE, "w") as f:
            json.dump({"license": key.strip()}, f)
    except Exception as e:
        print(f"Error saving license key: {e}")

def load_license_key():
    if os.path.exists(LICENSE_FILE):
        try:
            with open(LICENSE_FILE, "r") as f:
                data = json.load(f)
                return data.get("license", "").strip()
        except Exception as e:
            print(f"Error loading license key: {e}")
    return ""

def format_expiry(expiry_ts):
    try:
        if not expiry_ts or int(expiry_ts) == 0:
            return "Lifetime"
        secs = int(expiry_ts) - int(time.time())
        if secs < 0:
            return "Expired"
        days = secs // 86400
        hours = (secs % 86400) // 3600
        minutes = (secs % 3600) // 60
        return f"{days}d {hours}h {minutes}m remaining"
    except Exception:
        return "Unknown"

def check_license_key(license_key):
    url = "https://keyauth.win/api/1.2/"
    try:
        resp = requests.post(url, data={
            "type": "init",
            "ver": APP_VERSION,
            "name": APP_NAME,
            "ownerid": OWNER_ID
        })
        data = resp.json()
        if not data.get("success", False):
            return False, f"App initialization failed: {data.get('message','Unknown error')}"
        sessionid = data["sessionid"]
        resp2 = requests.post(url, data={
            "type": "license",
            "key": license_key,
            "sessionid": sessionid,
            "name": APP_NAME,
            "ownerid": OWNER_ID
        })
        data2 = resp2.json()
        if data2.get("success", False):
            expiry = data2.get("expiry")
            return True, expiry
        else:
            return False, data2.get("message", "License invalid or expired.")
    except Exception as e:
        return False, f"Network/Error: {e}"

# ====== GUI & BOT ======

def get_all_png_templates(folder):
    try:
        return [f for f in os.listdir(folder) if f.lower().endswith('.png')]
    except Exception:
        return []

def normalize_title(title):
    normalized = ''.join(
        c for c in unicodedata.normalize('NFKC', title)
        if unicodedata.category(c)[0] != 'C'
        and not unicodedata.combining(c)
    )
    normalized = re.sub(r'\s+', ' ', normalized).strip().lower()
    return normalized

def find_game_window(window_title):
    target_norm = normalize_title(window_title)
    for w in pyautogui.getAllWindows():
        win_norm = normalize_title(w.title)
        if target_norm in win_norm:
            return w
    return None

def launch_game_by_aumid(aumid, log):
    try:
        log(f"Launching game using AUMID: {aumid}")
        subprocess.Popen(["explorer.exe", f"shell:appsFolder\\{aumid}"], shell=True)
    except Exception as e:
        log(f"Failed to launch game by AUMID: {e}")

def match_template_gray(screen_img, template_path, threshold=THRESHOLD):
    if not os.path.isfile(template_path):
        return None, 0
    img_gray = cv2.cvtColor(screen_img, cv2.COLOR_BGR2GRAY)
    template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
    if template is None:
        return None, 0
    res = cv2.matchTemplate(img_gray, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(res)
    if max_val >= threshold:
        h, w = template.shape[:2]
        center = (max_loc[0] + w // 2, max_loc[1] + h // 2)
        return center, max_val
    return None, max_val

def smart_movement_script(stop_event, template_folder, log, threshold=THRESHOLD):
    keys = ['w', 'a', 's', 'd']
    log("Dynamic SMART movement script started!")
    skip_template_path = os.path.join(template_folder, "skip_dismiss.PNG")
    while not stop_event.is_set():
        screen = pyautogui.screenshot()
        img = cv2.cvtColor(np.array(screen), cv2.COLOR_RGB2BGR)
        center_skip, conf_skip = match_template_gray(img, skip_template_path, threshold)
        if center_skip:
            log(f"skip_dismiss detected at {center_skip} (conf={conf_skip:.2f}). Stopping movement script.")
            stop_event.set()
            break

        mode = random.choices(['single', 'combo', 'jump', 'idle'], weights=[45, 30, 10, 15])[0]
        dur = random.uniform(0.13, 0.65)
        if mode == 'single':
            k = random.choice(keys)
            keyboard.press(k)
            log(f"Holding '{k.upper()}' for {dur:.2f}s")
            time.sleep(dur)
            keyboard.release(k)
        elif mode == 'combo':
            k1, k2 = random.sample(keys, 2)
            keyboard.press(k1)
            keyboard.press(k2)
            log(f"Holding '{k1.upper()}'+'{k2.upper()}' for {dur:.2f}s")
            time.sleep(dur)
            keyboard.release(k1)
            keyboard.release(k2)
        elif mode == 'jump':
            n_jumps = random.randint(1, 2)
            for _ in range(n_jumps):
                keyboard.press('space')
                log("Jump!")
                time.sleep(0.09 + random.uniform(0, 0.06))
                keyboard.release('space')
                time.sleep(random.uniform(0.11, 0.23))
        else:
            idle = random.uniform(0.7, 1.6)
            log(f"Idle/pausing for {idle:.2f}s")
            time.sleep(idle)
        time.sleep(random.uniform(0.03, 0.09))
    log("Dynamic SMART movement script stopped.")

def cv_ui_sequence_bot(window_title, template_folder, class_order, log, threshold=THRESHOLD, should_run_event=None, movement_stop_event=None, movement_thread_holder=None):
    movement_started = False
    try:
        while (should_run_event is None or should_run_event.is_set()):
            game_window = find_game_window(window_title)
            if not game_window:
                log("Game window lost! Stopping movement (if running).")
                if movement_stop_event is not None:
                    movement_stop_event.set()
                if movement_thread_holder is not None and movement_thread_holder[0]:
                    if movement_thread_holder[0].is_alive():
                        movement_thread_holder[0].join(timeout=2)
                        log("Movement thread stopped by game close.")
                    movement_thread_holder[0] = None
                movement_started = False

                log("Waiting 20s, then relaunching game.")
                for _ in range(20):
                    if should_run_event is not None and not should_run_event.is_set():
                        log("Bot stopped during relaunch wait.")
                        return
                    time.sleep(1)
                launch_game_by_aumid(AUMID, log)
                log("Waiting for game window to appear after relaunch...")
                while find_game_window(window_title) is None:
                    if should_run_event is not None and not should_run_event.is_set():
                        log("Bot stopped during window reacquire.")
                        return
                    time.sleep(1)
                log("Game window detected after relaunch.")

            screen = pyautogui.screenshot()
            img = cv2.cvtColor(np.array(screen), cv2.COLOR_RGB2BGR)
            found_any = False

            # Crash dialog handling
            for crash_name in ["skip_dismiss", "directx_button", "directx_hovered"]:
                crash_path = os.path.join(template_folder, crash_name + ".PNG")
                center, conf = match_template_gray(img, crash_path, threshold=0.80)
                if center:
                    pyautogui.moveTo(center[0], center[1], duration=0.13)
                    pyautogui.click(center[0], center[1])
                    log(f"Clicked crash dialog '{crash_name}' at {center} (conf={conf:.2f})")
                    found_any = True
                    time.sleep(0.7)

            # Main menu navigation and bot logic
            ordered_templates = [f"{name}.PNG" for name in class_order]
            template_files = get_all_png_templates(template_folder)

            for png_name in ordered_templates:
                template_path = os.path.join(template_folder, png_name)
                if not os.path.isfile(template_path):
                    continue
                name = png_name.rsplit('.', 1)[0].lower()
                if name == "ammo_ui":
                    continue
                center, conf = match_template_gray(img, template_path, threshold)
                if center:
                    log(f"Detected '{name}' at {center} (conf={conf:.2f})")
                    found_any = True
                    pyautogui.moveTo(center[0], center[1], duration=0.13)
                    pyautogui.click(center[0], center[1])
                    log(f"Clicked '{name}' at {center}")
                    time.sleep(1.5)

            # Now check for ammo_UI to start movement
            ammo_ui_path = os.path.join(template_folder, "ammo_UI.png")
            center_ammo, conf_ammo = match_template_gray(img, ammo_ui_path, threshold=0.80)
            log(f"[DEBUG] ammo_UI confidence: {conf_ammo:.2f} (found: {bool(center_ammo)} at {center_ammo})")
            if center_ammo and not movement_started and (movement_thread_holder is not None):
                log(f"ammo_UI detected at {center_ammo} (conf={conf_ammo:.2f}). Starting dynamic movement.")
                movement_stop_event.clear()
                movement_thread_holder[0] = threading.Thread(target=smart_movement_script, args=(movement_stop_event, template_folder, log), daemon=True)
                movement_thread_holder[0].start()
                movement_started = True

            # Stop movement if ammo_UI is lost
            if not center_ammo and movement_started:
                log("ammo_UI no longer detected. Stopping movement.")
                if movement_stop_event is not None:
                    movement_stop_event.set()
                if movement_thread_holder is not None and movement_thread_holder[0]:
                    if movement_thread_holder[0].is_alive():
                        movement_thread_holder[0].join(timeout=2)
                        log("Movement thread stopped by ammo_UI loss.")
                    movement_thread_holder[0] = None
                movement_started = False

            time.sleep(0.5)
    except Exception as e:
        import traceback
        log("Fatal exception:\n" + traceback.format_exc())
        if movement_stop_event is not None:
            movement_stop_event.set()
        if movement_thread_holder is not None and movement_thread_holder[0]:
            movement_thread_holder[0].join(timeout=2)
            movement_thread_holder[0] = None

class AFKBot:
    def __init__(self, log_func):
        self._should_run = threading.Event()
        self.log = log_func
        self._bot_thread = None
        self.movement_stop_event = threading.Event()
        self.movement_thread_holder = [None]

    def start(self):
        if self._bot_thread and self._bot_thread.is_alive():
            self.log("Bot is already running.")
            return
        self._should_run.set()
        self.movement_stop_event.clear()
        self._bot_thread = threading.Thread(target=self.run, daemon=True)
        self._bot_thread.start()

    def stop(self):
        self.log("Stopping bot...")
        self._should_run.clear()
        self.movement_stop_event.set()
        if self.movement_thread_holder[0] is not None and self.movement_thread_holder[0].is_alive():
            self.movement_thread_holder[0].join(timeout=2)
            self.log("Movement thread stopped.")

    def run(self):
        self.log("[BOT] Bot loop started.")
        cv_ui_sequence_bot(
            window_title,
            TEMPLATE_FOLDER,
            class_order,
            self.log,
            threshold=THRESHOLD,
            should_run_event=self._should_run,
            movement_stop_event=self.movement_stop_event,
            movement_thread_holder=self.movement_thread_holder
        )
        self.log("[BOT] Bot loop stopped.")

class AFKReaperGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PROJECT AFK KILLER")
        self.geometry(f"{WINDOW_W}x{WINDOW_H}")
        self.resizable(False, False)
        self.configure(bg=COLOR_BG)
        self.is_running = False

        self.bg_img = Image.open(BG_IMAGE_PATH).resize((WINDOW_W, WINDOW_H), Image.LANCZOS).convert("RGBA")
        overlay = Image.new('RGBA', self.bg_img.size, (25, 0, 0, 150))
        self.bg_with_overlay = Image.alpha_composite(self.bg_img, overlay)
        self.bg_photo = ImageTk.PhotoImage(self.bg_with_overlay)
        self.bg_label = tk.Label(self, image=self.bg_photo, border=0)
        self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        # BOTH shadow and visible title in accent red
        self.title_shadow = tk.Label(self, text="PROJECT AFK KILLER", fg="#000", bg=COLOR_BG, font=("Segoe UI Black", 20), anchor="center")
        self.title_shadow.place(relx=0.5, y=23, anchor="center")
        self.title_label = tk.Label(self, text="PROJECT AFK KILLER", fg=COLOR_BTN, bg=COLOR_BG, font=("Segoe UI Black", 20), anchor="center")
        self.title_label.place(relx=0.5, y=20, anchor="center")

        self.license_active = False
        self.license_expiry = ""

        self.license_frame = tk.Frame(self, bg=COLOR_BG)
        self.license_frame.place(relx=0.5, y=100, anchor="center")
        tk.Label(self.license_frame, text="Enter License Key:", fg=COLOR_TEXT, bg=COLOR_BG, font=("Segoe UI", 12)).grid(row=0, column=0, padx=5, pady=2)
        self.license_entry = tk.Entry(self.license_frame, font=("Consolas", 12), width=32)
        self.license_entry.grid(row=0, column=1, padx=3)
        self.license_activate_btn = tk.Button(
            self.license_frame, text="Activate", font=("Segoe UI", 11),
            bg=COLOR_BTN, fg=COLOR_TEXT, activebackground=COLOR_BTN_HOVER,
            activeforeground="#fff", bd=0, relief="flat", padx=10, pady=2,
            command=self.activate_license, cursor="hand2"
        )
        self.license_activate_btn.grid(row=0, column=2, padx=5)
        self.license_status = tk.Label(self.license_frame, text="", fg="red", bg=COLOR_BG, font=("Segoe UI", 10))
        self.license_status.grid(row=1, column=0, columnspan=3, pady=2)

        self.ui_widgets = []

        self.status_dot = tk.Canvas(self, width=16, height=16, bg=COLOR_BG, highlightthickness=0)
        self.status_id = self.status_dot.create_oval(2, 2, 14, 14, fill=COLOR_STATUS_STOP, outline="#222")
        self.status_dot.place(relx=0.15, y=60, anchor="w")
        self.status_label = tk.Label(self, text="Stopped", fg=COLOR_STATUS_STOP, bg=COLOR_BG, font=("Segoe UI", 12, "bold"))
        self.status_label.place(relx=0.18, y=60, anchor="w")
        self.ui_widgets += [self.status_dot, self.status_label]

        self.start_btn = tk.Button(self, text="Start", font=("Segoe UI Bold", 13),
                                   bg=COLOR_BTN, fg=COLOR_TEXT, activebackground=COLOR_BTN_HOVER,
                                   activeforeground="#fff", bd=0, relief="flat",
                                   padx=18, pady=2, command=self.toggle_start,
                                   cursor="hand2", state="disabled")
        self.start_btn.place(relx=0.41, y=57, anchor="e")
        self.ui_widgets.append(self.start_btn)

        self.stop_btn = tk.Button(self, text="Stop", font=("Segoe UI Bold", 13),
                                  bg=COLOR_BTN_STOP, fg="#f1e2e8", activebackground=COLOR_BTN_STOP_HOVER,
                                  activeforeground="#fff", bd=0, relief="flat",
                                  padx=18, pady=2, command=self.toggle_stop,
                                  cursor="hand2", state="disabled")
        self.stop_btn.place(relx=0.59, y=57, anchor="w")
        self.ui_widgets.append(self.stop_btn)

        self.start_btn.bind("<Enter>", lambda e: self.start_btn.config(bg=COLOR_BTN_HOVER))
        self.start_btn.bind("<Leave>", lambda e: self.start_btn.config(bg=COLOR_BTN))
        self.stop_btn.bind("<Enter>", lambda e: self.stop_btn.config(bg=COLOR_BTN_STOP_HOVER))
        self.stop_btn.bind("<Leave>", lambda e: self.stop_btn.config(bg=COLOR_BTN_STOP))

        self.log_box = scrolledtext.ScrolledText(self, wrap="word", bg=COLOR_BG_OVERLAY, fg=COLOR_TEXT,
                                                 font=("Consolas", 10), width=64, height=11,
                                                 border=0, highlightthickness=0, insertbackground=COLOR_BTN, state="disabled")
        self.log_box.place(x=22, y=135)
        self.ui_widgets.append(self.log_box)

        self.support_btn = tk.Button(
            self, text="Support / Discord", font=("Segoe UI Bold", 11),
            bg=COLOR_BTN, fg=COLOR_TEXT, activebackground=COLOR_BTN_HOVER,
            activeforeground="#fff", bd=0, relief="flat", padx=12, pady=1,
            command=self.open_support_link, cursor="hand2", state="disabled"
        )
        self.support_btn.place(relx=0.5, rely=1.0, anchor="s", y=-14)
        self.support_btn.bind("<Enter>", lambda e: self.support_btn.config(bg=COLOR_BTN_HOVER))
        self.support_btn.bind("<Leave>", lambda e: self.support_btn.config(bg=COLOR_BTN))
        self.ui_widgets.append(self.support_btn)

        self.license_label = tk.Label(
            self, text=f"License: (Not Activated)", fg=COLOR_TEXT,
            bg=COLOR_BG, font=("Segoe UI", 9, "italic")
        )
        self.license_label.place(relx=1.0, rely=1.0, anchor="se", x=-8, y=-8)

        self.bot = AFKBot(self.log_msg)
        self.update_idletasks()
        self.center_window()
        self.set_ui_active(False)

        self.try_load_license_on_start()

    def set_ui_active(self, enabled):
        for w in self.ui_widgets:
            try:
                w.config(state="normal" if enabled else "disabled")
            except Exception:
                pass

    def try_load_license_on_start(self):
        loaded_key = load_license_key()
        if loaded_key:
            self.license_entry.insert(0, loaded_key)
            self.license_status.config(text="Checking license, please wait...")
            self.update()
            ok, result = check_license_key(loaded_key)
            if ok:
                expiry_str = format_expiry(result)
                self.license_expiry = expiry_str
                self.license_label.config(text=f"License: {expiry_str}")
                self.license_frame.place_forget()
                self.set_ui_active(True)
                self.start_btn.config(state="normal")
                self.support_btn.config(state="normal")
                self.log_msg("[KEYAUTH] License auto-activated successfully.")
                self.license_active = True
            else:
                self.license_status.config(text=f"License in file invalid: {result}")
                self.license_active = False

    def activate_license(self):
        license_key = self.license_entry.get().strip()
        if not license_key:
            self.license_status.config(text="Please enter a license key.")
            return
        self.license_status.config(text="Checking license, please wait...")
        self.update()
        ok, result = check_license_key(license_key)
        if ok:
            save_license_key(license_key)
            expiry_str = format_expiry(result)
            self.license_label.config(text=f"License: {expiry_str}")
            self.license_frame.place_forget()
            self.set_ui_active(True)
            self.start_btn.config(state="normal")
            self.support_btn.config(state="normal")
            self.log_msg("[KEYAUTH] License activated successfully.")
            self.license_active = True
        else:
            self.license_status.config(text=f"Activation Error: {result}")
            self.license_active = False

    def open_support_link(self):
        webbrowser.open_new(DISCORD_INVITE_URL)

    def center_window(self):
        w, h = self.winfo_width(), self.winfo_height()
        ws = self.winfo_screenwidth()
        hs = self.winfo_screenheight()
        x = (ws // 2) - (w // 2)
        y = (hs // 2) - (h // 2)
        self.geometry(f'{w}x{h}+{x}+{y}')

    def toggle_start(self):
        if not self.license_active:
            self.log_msg("License not activated.")
            return
        self.is_running = True
        self.status_dot.itemconfig(self.status_id, fill=COLOR_STATUS_GO)
        self.status_label.config(text="Running", fg=COLOR_STATUS_GO)
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.bot.start()

    def toggle_stop(self):
        self.is_running = False
        self.status_dot.itemconfig(self.status_id, fill=COLOR_STATUS_STOP)
        self.status_label.config(text="Stopped", fg=COLOR_STATUS_STOP)
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.bot.stop()

    def log_msg(self, text):
        self.log_box.config(state="normal")
        now = datetime.now().strftime("[%H:%M:%S] ")
        self.log_box.insert("end", f"{now}{text}\n")
        self.log_box.see("end")
        self.log_box.config(state="disabled")

# ====== MAIN STARTUP ======
if __name__ == "__main__":
    def gui_log_wrapper(msg):
        print("[UPDATE]", msg)
    auto_update_if_needed(log_func=gui_log_wrapper)

    if not os.path.isfile(BG_IMAGE_PATH):
        print(f"Missing background image: {BG_IMAGE_PATH}")
        input("Press Enter to exit...")
        exit(1)
    try:
        app = AFKReaperGUI()
        # Now patch the updater log to use GUI after GUI starts
        log_update_status = app.log_msg
        app.mainloop()
    except Exception as e:
        import traceback
        print("Fatal error in GUI:")
        print(traceback.format_exc())
        input("Press Enter to exit...")
