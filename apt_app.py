import streamlit as st
import pandas as pd
import requests
import time
import joblib

# Load APT Models
scaler = joblib.load("scaler.pkl")
unsup_model = joblib.load("apt_model_unsupervised.pkl")
feature_list = joblib.load("feature_list.pkl")

AWS_API_URL = "http://100.120.229.46:8000/botnet_traffic"

st.set_page_config(page_title="APT Detection Engine", layout="centered")
st.title("🛡️ APT Stealth Radar")
st.markdown("Listening to AWS Tailscale Tunnel for Anomalous Beacons and Lateral Movement...")

if 'apt_logs' not in st.session_state:
    st.session_state.apt_logs = []

alert_placeholder = st.empty()

# Helper function to safely convert Zeek text strings into AI-readable numbers
def safe_int(val):
    try: return int(val)
    except: return 0

while True:
    try:
        response = requests.get(AWS_API_URL, timeout=2)
        if response.status_code == 200:
            data = response.json()
            
            if "zeek_data" in data and "\t" in data["zeek_data"]:
                parts = data["zeek_data"].split('\t')
                if len(parts) > 10:
                    src_ip = parts[2]
                    target_port = str(parts[5])
                    
                    # Convert strings to integers for the AI!
                    df_row = pd.DataFrame([{
                        "src_port": safe_int(parts[4]), 
                        "dst_port": safe_int(target_port), 
                        "packet_length": safe_int(parts[8]), 
                        "protocol": 1 if parts[6]=='tcp' else 0
                    }])
                    
                    df_numeric = df_row.reindex(columns=feature_list, fill_value=0)
                    X_scaled = scaler.transform(df_numeric.values)
                    
                    unsup_score = unsup_model.decision_function(X_scaled)[0]
                    prediction = "⚠️ APT SUSPECTED (ANOMALY)" if unsup_score < 0 else "🟢 Normal Traffic"

                    if target_port == "4444": prediction = "🔴 APT DETECTED: Metasploit Beacon"
                    elif target_port == "3389": prediction = "🔴 APT DETECTED: RDP Lateral Movement"

                    # MINIMALIST LOG ENTRY
                    log_entry = {
                        "Source IP": src_ip,
                        "Port No": target_port,
                        "Message": prediction
                    }
                    
                    if len(st.session_state.apt_logs) == 0 or st.session_state.apt_logs[0] != log_entry:
                        st.session_state.apt_logs.insert(0, log_entry)
                        st.session_state.apt_logs = st.session_state.apt_logs[:15]

                    with alert_placeholder.container():
                        st.dataframe(pd.DataFrame(st.session_state.apt_logs), use_container_width=True, hide_index=True)
            else:
                with alert_placeholder.container():
                    st.info("System Idle. Waiting for Zeek traffic from AWS...")
                    
    except Exception as e:
        # Stop hiding the errors! Show them on the screen if it breaks.
        with alert_placeholder.container():
            st.error(f"Error processing packet: {e}")
            
    time.sleep(2)