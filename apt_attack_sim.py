import socket
import time
import random

TARGET_IP = "100.120.229.46"

def simulate_normal():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.1)
        s.connect((TARGET_IP, 443))
        s.close()
    except: pass

def simulate_apt_beacon():
    print("🔴 [APT] Firing Stealth Beacon (Port 4444)...")
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.1)
        s.connect((TARGET_IP, 4444))
        s.close()
    except: pass

def simulate_apt_lateral():
    print("🔴 [APT] Firing Lateral Movement (Port 3389)...")
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.1)
        s.connect((TARGET_IP, 3389))
        s.close()
    except: pass

if __name__ == "__main__":
    print(f"🌐 INITIATING APT TRAFFIC MIX ON {TARGET_IP}")
    while True:
        if random.randint(1, 100) <= 70:
            simulate_normal()
        else:
            random.choice([simulate_apt_beacon, simulate_apt_lateral])()
        time.sleep(random.uniform(0.5, 2.0))