import requests
import csv
import time
import os
import json

# --- 1. Configuration ---

# This MUST match the /predict endpoint of your API
# If running on GCP, replace with your GCP Cloud Run URL
API_URL = "https://botnet-api-service-596428028742.asia-south1.run.app/predict"# For local testing (if you run api_server.py on your host):
# API_URL = "http://10.0.2.2:8000/predict" # 10.0.2.2 is the host's IP in VirtualBox

# This MUST match the output file from your cicflowmeter command
CSV_FILE_PATH = "/home/pratham/flows.csv"

# These are the 9 features your MODEL was trained on.
# We will select *only* these from the CSV.
MODEL_FEATURES = [
    'dur', 'proto', 'dir', 'state', 'stos', 'dtos', 
    'tot_pkts', 'tot_bytes', 'src_bytes'
]

# --- !! CRITICAL MAPPING !! ---
# This maps the REAL cicflowmeter headers (left) to the
# feature names your model expects (right).
# This is the "translation" step.
COLUMN_MAP = {
    'flow_duration': 'dur',
    'protocol': 'proto',
    'tot_fwd_pkts': 'tot_pkts',    # Approximating 'tot_pkts'
    'totlen_fwd_pkts': 'src_bytes', # Approximating 'src_bytes'
    'tot_fwd_pkts': 'tot_pkts',
    'totlen_fwd_pkts': 'tot_bytes',  # Approximating 'tot_bytes'
    # ---
    # The features below are NOT produced by cicflowmeter
    # and will be sent as 'None'. Your API (with my fix) will handle this.
    # ---
    'dir': 'dir',
    'state': 'state',
    'stos': 'stos',
    'dtos': 'dtos'
}


def follow_file(filepath):
    """
    "Tails" a file and yields new lines as they are written.
    """
    print(f"Starting to monitor '{filepath}' for new flows...")
    filepath = os.path.abspath(filepath)
    
    # Ensure the file exists before we start
    while not os.path.exists(filepath):
        print(f"Waiting for '{filepath}' to be created by cicflowmeter...")
        time.sleep(5)

    with open(filepath, 'r') as f:
        # Go to the end of the file
        f.seek(0, 2) 
        
        while True:
            line = f.readline()
            if not line:
                # No new line, wait a bit
                time.sleep(0.5)
                continue
            
            # New line found
            yield line

def process_flow_line(line, headers):
    """
    Converts a single CSV line into the JSON payload for the API.
    """
    try:
        reader = csv.reader([line])
        values = next(reader)
        row_dict = dict(zip(headers, values))

        # 1. Create the base payload
        payload = {}
        
        # 2. Translate from cicflowmeter names to model names
        for csv_header, model_feature in COLUMN_MAP.items():
            if csv_header in row_dict:
                payload[model_feature] = row_dict[csv_header]
            else:
                # Add placeholders for features cicflowmeter doesn't make
                payload[model_feature] = None 
        
        # 3. Ensure all model features are present, even if None
        for feature in MODEL_FEATURES:
            if feature not in payload:
                payload[feature] = None
        
        # 4. Correct data types for the API
        for key in ['dur', 'stos', 'dtos']:
            payload[key] = float(payload[key]) if payload[key] is not None else 0.0
        
        for key in ['tot_pkts', 'tot_bytes', 'src_bytes']:
            payload[key] = int(payload[key]) if payload[key] is not None else 0
            
        return payload

    except Exception as e:
        print(f"Error processing line: {e}. Line: {line.strip()}")
        return None

def main():
    headers = []
    first_line = True
    
    for line in follow_file(CSV_FILE_PATH):
        if first_line:
            # The first line we read is the CSV Header
            headers = [h.strip() for h in line.split(',')]
            print(f"Captured headers: {headers}")
            first_line = False
            continue # Skip processing the header line

        # Process the new flow
        payload = process_flow_line(line, headers)
        
        if payload:
            try:
                # Send to the API
                response = requests.post(API_URL, json=payload)
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"Flow Predicted: {result.get('predicted_family')} (Confidence: {result.get('confidence', 0):.2f})")
                else:
                    print(f"API Error (Code {response.status_code}): {response.text}")

            except requests.exceptions.ConnectionError:
                print(f"Error: Cannot connect to API at {API_URL}. Is it running?")
                time.sleep(10) # Wait 10s before retrying
            except Exception as e:
                print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()