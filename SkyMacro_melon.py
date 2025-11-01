import win32gui
import win32con
import win32api
import time
import threading
import random
from pycaw.pycaw import AudioUtilities, IAudioMeterInformation
from discord_webhook import DiscordWebhook

# Virtual Key Codes
VK_A = 0x41
VK_D = 0x44
VK_W = 0x57
VK_T = 0x54
VK_UP = 0x26
VK_ENTER = 0x0D

# Scan Codes (based on US QWERTY layout)
SC_A = 0x1E
SC_D = 0x20
SC_W = 0x11
SC_T = 0x14
SC_UP = 0x48
SC_ENTER = 0x1c
# Get the window handle for Minecraft
hwnd = win32gui.FindWindow(None, "Minecraft 1.8.9")

def make_lparam(repeat_count, scan_code, extended, context_code, previous_state, transition_state):
    return (repeat_count |
            (scan_code << 16) |
            (extended << 24) |
            (context_code << 29) |
            (previous_state << 30) |
            (transition_state << 31))

def press_key(hwnd, key_code, scan_code):
    lparam = make_lparam(1, scan_code, 0, 0, 0, 0)
    win32gui.SendMessage(hwnd, win32con.WM_KEYDOWN, key_code, lparam)

def release_key(hwnd, key_code, scan_code):
    lparam = make_lparam(1, scan_code, 0, 0, 1, 1)
    win32gui.SendMessage(hwnd, win32con.WM_KEYUP, key_code, lparam)

def hold_key(hwnd, key_code, scan_code, duration, stop_event):
    print(f"Pressing {chr(key_code)}")
    press_key(hwnd, key_code, scan_code)

    start_time = time.time()
    while time.time() - start_time < duration:
        if stop_event.is_set():
            print(f"Stop event detected, releasing {chr(key_code)} early")
            break
        time.sleep(0.1)

    release_key(hwnd, key_code, scan_code)
    print(f"Released {chr(key_code)}")

def hold_left_click(hwnd):
    win32api.PostMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, 0)

def release_left_click():
    win32api.PostMessage(hwnd, win32con.WM_LBUTTONUP, 0, 0)

def find_minecraft_audio_meter():
    sessions = AudioUtilities.GetAllSessions()
    for session in sessions:
        if session.Process and "javaw.exe" in session.Process.name().lower():
            print("[DEBUG] Found Minecraft session")
            return session._ctl.QueryInterface(IAudioMeterInformation)
    print("[DEBUG] Minecraft audio session NOT found")
    return None

def monitor_audio(stop_event):
    silence_start = None
    meter = find_minecraft_audio_meter()
    if not meter:
        print("[ERROR] Could not find Minecraft audio meter, exiting audio monitor.")
        stop_event.set()
        return

    while not stop_event.is_set():
        peak = meter.GetPeakValue()  # Real-time volume level (0.0 to 1.0)
        print(f"[DEBUG] Peak volume: {peak:.3f}")
        if peak <= 0.01:
            if silence_start is None:
                silence_start = time.time()
                print("[DEBUG] Silence started")
            elif time.time() - silence_start >= 10:
                print("❗ No sound detected for 10 seconds!")
                stop_event.set()
                break
            else:
                print(f"[DEBUG] Silent for {time.time() - silence_start:.2f} seconds...")
        else:
            if silence_start is not None:
                print("[DEBUG] Sound resumed")
            silence_start = None

        time.sleep(0.5)

def macro_loop(stop_event):
    A_counter = 0
    while not stop_event.is_set():
        ad_random = random.uniform(29, 31)
        print(f"Holding A for ~{ad_random:.2f} seconds...")
        hold_key(hwnd, VK_A, SC_A, ad_random, stop_event)
        if stop_event.is_set():
            break

        A_counter += 1
        if A_counter == 15:
            print("Pausing after 3 A loops...")
            A_counter = 0
            random_time = random.uniform(0.1,0.5)
            release_left_click()
            hold_key(hwnd, VK_T, SC_T, 0, stop_event)
            time.sleep(random_time)
            hold_key(hwnd, VK_UP, SC_UP, 0, stop_event)
            time.sleep(random_time)
            hold_key(hwnd, VK_ENTER, SC_ENTER, 0, stop_event)
            time.sleep(1)

            hold_left_click(hwnd)
            continue

        w_random = random.uniform(1, 1.3)
        print(f"Holding W for ~{w_random:.2f} seconds...")
        hold_key(hwnd, VK_W, SC_W, w_random, stop_event)
        if stop_event.is_set():
            break

        print(f"Holding D for ~{ad_random:.2f} seconds...")
        hold_key(hwnd, VK_D, SC_D, ad_random, stop_event)
        if stop_event.is_set():
            break

        print(f"Holding W for ~{w_random:.2f} seconds...")
        hold_key(hwnd, VK_W, SC_W, w_random, stop_event)

def send_discord_notification():
    webhook = DiscordWebhook(
        url="Redacted",
        content="<@844653327567945779> ❗YOU'RE BEING CHECKED"
    )
    webhook.execute()
    print("[INFO] Discord notification sent.")

if __name__ == "__main__":
    stop_event = threading.Event()

    # Start holding left-click in a background thread
    click_thread = threading.Thread(target=hold_left_click, args=(hwnd,))
    click_thread.start()

    # Start monitoring audio in a background thread
    monitor_thread = threading.Thread(target=monitor_audio, args=(stop_event,))
    monitor_thread.start()

    # Start macro loop in main thread (or you can also run it in another thread)
    try:
        macro_loop(stop_event)
    except KeyboardInterrupt:
        print("Keyboard interrupt received, stopping.")
        stop_event.set()
    finally:
        print("[INFO] Cleaning up...")

        # Release mouse click and keys
        release_left_click()
        release_key(hwnd, VK_A, SC_A)
        release_key(hwnd, VK_D, SC_D)
        release_key(hwnd, VK_W, SC_W)

        # Wait for threads to finish nicely
        click_thread.join()
        monitor_thread.join()

        # Send Discord notification after all stopped
        for _ in range(100):
            send_discord_notification()
            time.sleep(1.5)

        print("[INFO] Script stopped cleanly.")
