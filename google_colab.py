!git clone https://github.com/rarabzad/CaSR-v3.1-downloader.git
%cd CaSR-v3.1-downloader
!pip install -r requirements.txt
!wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
!dpkg -i cloudflared-linux-amd64.deb

import threading, os, time, requests
import subprocess, re
from IPython.display import display, HTML

def run_streamlit():
    os.system("streamlit run app.py --server.port 8501 --server.headless true")

def wait_for_streamlit(port=8501, timeout=60):
    """Wait for Streamlit to be ready"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"http://localhost:{port}", timeout=2)
            if response.status_code == 200:
                print("✅ Streamlit is ready!")
                return True
        except:
            pass
        time.sleep(2)
    return False

# Start Streamlit in background
print("🚀 Starting Streamlit...")
threading.Thread(target=run_streamlit, daemon=True).start()

# Wait for Streamlit to be ready
if not wait_for_streamlit():
    print("❌ Streamlit failed to start properly")
    exit()

# Now start the tunnel
print("🌐 Creating tunnel...")
proc = subprocess.Popen(
    ["cloudflared", "tunnel", "--url", "http://localhost:8501", "--no-autoupdate"],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True
)

tunnel_url = None
max_attempts = 10
attempt = 0

for line in proc.stdout:
    print(f"Cloudflare: {line.strip()}")  # Debug output
    if "trycloudflare.com" in line:
        match = re.search(r"https://[a-zA-Z0-9.-]+\.trycloudflare\.com", line)
        if match:
            tunnel_url = match.group(0)
            break
    attempt += 1
    if attempt > max_attempts:
        break

if tunnel_url:
    print(f"\n🎉 Success! Your app is available at:")
    display(HTML(f"""
        <div style="padding: 20px; background-color: #f0f8ff; border: 2px solid #4CAF50; border-radius: 10px; margin: 10px 0;">
            <h3 style="color: #2E7D32;">Your Streamlit App is Ready!</h3>
            <a href="{tunnel_url}" target="_blank" style="font-size:18px; color: #1976D2; text-decoration: none;">
                🚀 {tunnel_url}
            </a>
        </div>
    """))
else:
    print("⚠️ Could not detect the tunnel URL. Checking if Streamlit is accessible...")
    # Try to access Streamlit directly
    try:
        response = requests.get("http://localhost:8501")
        if response.status_code == 200:
            print("✅ Streamlit is running on localhost:8501")
            print("❌ But tunnel creation failed. Try running the cloudflared command manually.")
        else:
            print("❌ Streamlit is not responding properly")
    except Exception as e:
        print(f"❌ Error checking Streamlit: {e}")
