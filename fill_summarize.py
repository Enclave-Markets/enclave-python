import json
import sys
from datetime import datetime
from collections import defaultdict

def summarize_theoretical_pnl(file_path):
    pnl_by_hour = defaultdict(float)

    with open(file_path, 'r') as file:
        for line in file:
            try:
                parts = line.split(' ', 3)  # Splitting by the first three spaces
                if len(parts) < 4:
                    continue  # Skip lines that don't have the expected format

                # Extract timestamp from the first part and JSON from the fourth part
                timestamp_str = parts[0] + ' ' + parts[1]
                timestamp = datetime.fromisoformat(timestamp_str.split('.')[0])
                data = json.loads(''.join(parts[3:]))  # JSON data is in the fourth part

                hour_key = timestamp.strftime('%Y-%m-%d %H:00')
                pnl_by_hour[hour_key] += data["theoretical_pnl"]
            except (json.JSONDecodeError, KeyError, ValueError, IndexError):
                print("Error processing line:", line)

    return pnl_by_hour

if len(sys.argv) < 2:
    print("Usage: python script_name.py <file_path>")
    sys.exit(1)

file_path = sys.argv[1]
pnl_summary = summarize_theoretical_pnl(file_path)

for hour, pnl in pnl_summary.items():
    print(f"{hour}: {pnl:.2f}")