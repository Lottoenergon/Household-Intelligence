import os
import sys
import re
import time
import subprocess
import threading
import webbrowser

CLOUDFLARED_EXE = r"C:\Program Files (x86)\cloudflared\cloudflared.exe"
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
os.makedirs(PROCESSED_DIR, exist_ok=True)
URL_FILE = os.path.join(PROCESSED_DIR, "live_tunnel_url.txt")
LOG_FILE = os.path.join(PROCESSED_DIR, "tunnel.log")

if not os.path.exists(CLOUDFLARED_EXE):
    print(f"Error: {CLOUDFLARED_EXE} not found.")
    sys.exit(1)

print("[INFO] Launching Cloudflare Tunnel for Household Intelligence...")
cmd = [CLOUDFLARED_EXE, "tunnel", "--url", "http://127.0.0.1:8000"]
proc = subprocess.Popen(
    cmd,
    stderr=subprocess.PIPE,
    stdout=subprocess.DEVNULL,
    text=True,
    encoding="utf-8",
    errors="replace",
    bufsize=1
)

live_url = None
log_f = open(LOG_FILE, "w", encoding="utf-8")

def drain_and_log():
    global live_url
    try:
        if proc.stderr is not None:
            for line in iter(proc.stderr.readline, ''):
                log_f.write(line)
                log_f.flush()
                if not live_url:
                    match = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", line)
                    if match:
                        live_url = match.group(0)
    except Exception:
        pass

drain_thread = threading.Thread(target=drain_and_log, daemon=True)
drain_thread.start()

start_time = time.time()
while time.time() - start_time < 30:
    if live_url:
        break
    time.sleep(0.5)

if not live_url:
    print("[ERROR] Failed to obtain live tunnel URL within 30s. Check data/processed/tunnel.log")
    proc.terminate()
    sys.exit(1)

print(f"[SUCCESS] Live Public URL: {live_url}")
with open(URL_FILE, "w", encoding="utf-8") as f:
    f.write(live_url.strip())

# Autorun/open in browser
if "--no-browser" not in sys.argv:
    print(f"[INFO] Opening {live_url} in browser...")
    webbrowser.open(live_url)

# Keep the tunnel alive
try:
    while True:
        time.sleep(1)
        if proc.poll() is not None:
            break
except KeyboardInterrupt:
    proc.terminate()
finally:
    try:
        log_f.close()
    except Exception:
        pass
