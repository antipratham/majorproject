import streamlit as st
import pandas as pd
import requests
import time
import joblib

# --- Load Models & Config ---
multi_scaler = joblib.load("multi_scaler.pkl")
multi_model = joblib.load("multi_model.pkl")
anomaly_scaler = joblib.load("anomaly_scaler.pkl")
anomaly_model = joblib.load("anomaly_model.pkl")
FEATURES = joblib.load("features.pkl")

AWS_API_URL = "http://100.120.229.46:8000/botnet_traffic"

INV_LABEL_MAP = {0: 'Benign', 1: 'DDoS', 2: 'PortScan', 3: 'Bot', 4: 'Infiltration', 5: 'Web Attack', 6: 'Brute Force', 7: 'DoS', 8: 'Heartbleed'}
PRIORITY_MAP = {'Benign': 'LOW', 'DDoS': 'HIGH', 'PortScan': 'MEDIUM', 'Bot': 'MEDIUM', 'Infiltration': 'HIGH', 'Web Attack': 'HIGH', 'Brute Force': 'HIGH', 'DoS': 'HIGH', 'Heartbleed': 'CRITICAL', 'Zero-Day Anomaly': 'CRITICAL', 'FTP Exfiltration': 'CRITICAL', 'DNS Tunneling': 'CRITICAL'}

# --- UI Setup ---
st.set_page_config(page_title="Breach Detection Engine", layout="wide")
st.title("🚨 Data Breach & Exfiltration Dashboard")

if 'breach_logs' not in st.session_state:
    st.session_state.breach_logs = []

# Botnet-style Checkbox! No more sidebars.
connect_aws = st.checkbox("Connect to AWS & Start Live Feed", value=True)

metrics_placeholder = st.empty()
table_placeholder = st.empty()

# Helper to safely convert Zeek strings into XGBoost Math Numbers
def safe_float(val):
    try: return float(val)
    except: return 0.0

if connect_aws:
    with table_placeholder.container():
        st.success("Connected to AWS API via Tailscale tunnel. Listening for packets...")
    
    while connect_aws:
        try:
            response = requests.get(AWS_API_URL, timeout=2)
            if response.status_code == 200:
                data = response.json()
                if "zeek_data" in data and "\t" in data["zeek_data"]:
                    parts = data["zeek_data"].split('\t')
                    if len(parts) > 10:
                        src_ip = parts[2]
                        dest_ip = parts[3]
                        target_port_str = parts[5]
                        
                        # 1. Map Zeek metadata to CICIDS features with SAFE MATH CONVERSION
                        df_row = pd.DataFrame([{
                            " Destination Port": safe_float(target_port_str), 
                            " Total Length of Fwd Packets": safe_float(parts[8]), 
                            " Flow Duration": safe_float(parts[7])
                        }])
                        df_numeric = df_row.reindex(columns=FEATURES, fill_value=0)
                        
                        # Added .values to suppress the yellow warnings
                        X_multi = multi_scaler.transform(df_numeric.values)
                        X_anom = anomaly_scaler.transform(df_numeric.values)
                        
                        multi_label_num = multi_model.predict(X_multi)[0]
                        anomaly_score = anomaly_model.predict(X_anom)[0]

                        # 2. Priority Logic
                        if multi_label_num != 0:
                            prediction = INV_LABEL_MAP.get(multi_label_num, "Unknown Attack")
                        else:
                            prediction = "Zero-Day Anomaly" if anomaly_score == -1 else "Benign"

                        # 3. Heuristic Exfiltration Catch
                        if target_port_str == "21": prediction = "FTP Exfiltration"
                        elif target_port_str == "53": prediction = "DNS Tunneling"

                        priority = PRIORITY_MAP.get(prediction, "LOW")

                        log_entry = {
                            "Time": time.strftime('%H:%M:%S'),
                            "Source": src_ip,
                            "Dest": dest_ip,
                            "Port": target_port_str,
                            "Type": prediction,
                            "Priority": priority
                        }
                        
                        if len(st.session_state.breach_logs) == 0 or st.session_state.breach_logs[0] != log_entry:
                            st.session_state.breach_logs.insert(0, log_entry)
                            st.session_state.breach_logs = st.session_state.breach_logs[:20]
                            
        except Exception as e:
            with table_placeholder.container():
                st.error(f"Error processing packet: {e}")
            
        # --- Update UI ---
        total_packets = len(st.session_state.breach_logs)
        critical_threats = sum(1 for p in st.session_state.breach_logs if p['Priority'] == "CRITICAL")
        high_threats = sum(1 for p in st.session_state.breach_logs if p['Priority'] == "HIGH")
        anomalies = sum(1 for p in st.session_state.breach_logs if p['Type'] != "Benign")

        with metrics_placeholder.container():
            cols = st.columns(4)
            cols[0].metric("Total Packets", total_packets)
            cols[1].metric("Critical Threats", critical_threats)
            cols[2].metric("High Threats", high_threats)
            cols[3].metric("Anomalies", anomalies)

        with table_placeholder.container():
            if st.session_state.breach_logs:
                df = pd.DataFrame(st.session_state.breach_logs)
                
                # Apply the custom row colors
                def style_priority(row):
                    colors = {
                        'CRITICAL': 'background-color: #8B0000; color: white; font-weight: bold',
                        'HIGH': 'background-color: #FF4B4B; color: white',
                        'MEDIUM': 'background-color: #FFA500; color: black',
                        'LOW': 'background-color: #28a745; color: white',
                    }
                    return [colors.get(row['Priority'], '')] * len(row)

                st.dataframe(df.style.apply(style_priority, axis=1), width="stretch", hide_index=True, height=500)
                
        time.sleep(2)