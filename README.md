This engine utilizes three distinct Machine Learning models operating in parallel, acting as specialized lenses over the same AWS network feed:

1. Botnet Engine (Random Forest)
Target: High-frequency, low-payload automated attacks (Mirai, Okiru, DDoS).

Mechanism: Random Forest natively excels at finding rigid, repetitive, high-volume patterns. Paired with port heuristics to catch standard botnet propagation vectors.

2. Data Breach Triage (XGBoost Multi-Class)
Target: Data exfiltration and active network breaches.

Mechanism: A heavy-duty XGBoost classifier evaluates dozens of packet features (duration, flags, asymmetric byte ratios) to categorize the exact attack type (e.g., FTP Exfiltration, Web Attack) and assign a severity Priority (Low to Critical).

3. APT Stealth Radar (Isolation Forest)
Target: Stealthy human operators, Metasploit beacons, and Lateral Movement (RDP).

Mechanism: An unsupervised anomaly detection model. Instead of looking for known malware signatures in encrypted payloads, it isolates behavioral outliers (like perfectly timed 5-second check-ins over 72 hours) to flag Zero-Day intrusions.

🚀 Quick Start Guide
Prerequisites
Python 3.10+

Tailscale installed and authenticated to the shared project network.

Access to the central AWS Ubuntu server running Zeek and the FastAPI sensor_api.py.

Running a Module (Example: APT Radar)
Each module requires two terminals: one for the Streamlit GUI, and one to fire the simulated attack traffic.

Start the Dashboard:

PowerShell / VS Terminal / Command Prompt
cd majorprojectapt
python -m venv .venv
.\\.venv\\Scripts\\activate
pip install -r requirements.txt
python -m streamlit run apt_app.py
Launch the Attack Simulator:

PowerShell / VS Terminal / Command Prompt
cd majorprojectapt
python apt_sim.py
(Repeat the above steps for the majorprojectbotnet and majorprojectbreach directories).
