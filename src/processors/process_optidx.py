import os
import glob
import zipfile
import csv
from collections import defaultdict
from datetime import datetime

def process_all_optidx(output_filename="Consolidated_OptIdx_Data.csv", data_dir="."):
    # Find all zip files
    zip_files = glob.glob(os.path.join(data_dir, "FO_Market_Activity_Report_*.zip"))
    
    if not zip_files:
        print("No zip files found.")
        return
        
    print(f"Found {len(zip_files)} zip files. Processing...")
    
    # Store aggregated results: dict of (date, symbol) -> [contracts, quantity, value]
    aggregated_data = defaultdict(lambda: [0, 0, 0.0])
    
    for zip_path in zip_files:
        try:
            with zipfile.ZipFile(zip_path, 'r') as z:
                # Find optidx file
                optidx_files = [name for name in z.namelist() if name.lower().startswith('optidx') and name.lower().endswith('.csv')]
                
                if not optidx_files:
                    continue
                    
                optidx_filename = optidx_files[0]
                
                # Extract date from zip filename
                basename = os.path.basename(zip_path)
                date_str = basename.split('_')[-1].split('.')[0] # gets YYYYMMDD
                try:
                    date_obj = datetime.strptime(date_str, "%Y%m%d")
                    formatted_date = date_obj.strftime("%Y-%m-%d")
                except ValueError:
                    formatted_date = date_str
                
                with z.open(optidx_filename) as f:
                    content = f.read().decode('utf-8-sig', errors='replace').splitlines()
                    
                    if not content:
                        continue
                        
                    # Find the header row (sometimes there's a title row above it)
                    header_idx = 0
                    for i, line in enumerate(content[:5]):
                        if "Symbol" in line and "Traded" in line:
                            header_idx = i
                            break
                            
                    content = content[header_idx:]
                    if not content:
                        continue
                        
                    reader = csv.reader(content)
                    headers = next(reader)
                    
                    for row in reader:
                        if len(row) < 4:
                            continue
                            
                        symbol = row[0].strip()
                        if not symbol:
                            continue
                            
                        try:
                            contracts = int(row[1].strip())
                            quantity = int(row[2].strip())
                            value = float(row[3].strip())
                        except ValueError:
                            continue
                            
                        key = (formatted_date, symbol)
                        aggregated_data[key][0] += contracts
                        aggregated_data[key][1] += quantity
                        aggregated_data[key][2] += value
                        
        except zipfile.BadZipFile:
            print(f"Skipping {basename} (Not a valid zip file)")
        except Exception as e:
            print(f"Error processing {zip_path}: {e}")
            
    print(f"Writing {len(aggregated_data)} aggregated rows to CSV...")
    
    # Sort by Date then Symbol
    sorted_keys = sorted(aggregated_data.keys(), key=lambda x: (x[0], x[1]))
    
    with open(output_filename, 'w', newline='', encoding='utf-8') as out_f:
        writer = csv.writer(out_f)
        # Write header
        writer.writerow(["Date", "Symbol", "No of Contracts Traded", "Traded Quantity", "Total Traded Value (Rs. In Crs.)"])
        
        for date_val, symbol in sorted_keys:
            contracts, quantity, value = aggregated_data[(date_val, symbol)]
            writer.writerow([date_val, symbol, contracts, quantity, f"{value:.2f}"])
            
    print(f"Done! Aggregated data saved to {output_filename}")

if __name__ == "__main__":
    process_all_optidx()
