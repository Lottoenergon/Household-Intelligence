import os
import sys
import re
import time
import subprocess
import webbrowser

CLOUDFLARED_EXE = r"C:\Program Files (x86)\cloudflared\cloudflared.exe"
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL_FILE = os.path.join(BASE_DIR, "data", "processed", "live_tunnel_url.txt")

if not os.path.exists(CLOUDFLARED_EXE):
    print(f"Error: {CLOUDFLARED_EXE} not found.")
    sys.exit(1)

print("[INFO] Launching Cloudflare Tunnel for Household Intelligence...")
cmd = [CLOUDFLARED_EXE, "tunnel", "--url", "http://127.0.0.1:8000"]
proc = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)

live_url = None
start_time = time.time()
while time.time() - start_time < 20:
    if proc.stderr is None:
        break
    line = proc.stderr.readline()
    if not line:
        continue
    match = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", line)
    if match:
        live_url = match.group(0)
        break

if not live_url:
    print("[ERROR] Failed to obtain live tunnel URL within 20s.")
    sys.exit(1)

print(f"[SUCCESS] Live Public URL: {live_url}")
with open(URL_FILE, "w", encoding="utf-8") as f:
    f.write(live_url.strip())

# Autorun/open in browser
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
