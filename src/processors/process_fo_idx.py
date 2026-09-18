import os
import glob
import zipfile
import csv
from collections import defaultdict
from datetime import datetime

def process_all_foidx(output_filename="Consolidated_FO_Idx_Data.csv", data_dir="data"):
    # Find all zip files
    zip_files = glob.glob(os.path.join(data_dir, "FO_Market_Activity_Report_*.zip"))
    
    if not zip_files:
        print("No zip files found.")
        return
        
    print(f"Found {len(zip_files)} zip files. Processing...")
    
    # Store aggregated results: dict of (date, symbol) -> 
    # [fut_contracts, fut_qty, fut_val, opt_contracts, opt_qty, opt_val]
    aggregated_data = defaultdict(lambda: [0, 0, 0.0, 0, 0, 0.0])
    
    for zip_path in zip_files:
        try:
            with zipfile.ZipFile(zip_path, 'r') as z:
                # Find optidx file and futidx file
                optidx_files = [name for name in z.namelist() if name.lower().startswith('optidx') and name.lower().endswith('.csv')]
                futidx_files = [name for name in z.namelist() if name.lower().startswith('futidx') and name.lower().endswith('.csv')]
                
                # Extract date from zip filename
                basename = os.path.basename(zip_path)
                date_str = basename.split('_')[-1].split('.')[0] # gets YYYYMMDD
                try:
                    date_obj = datetime.strptime(date_str, "%Y%m%d")
                    formatted_date = date_obj.strftime("%Y-%m-%d")
                except ValueError:
                    formatted_date = date_str
                
                # Process Futures
                if futidx_files:
                    with z.open(futidx_files[0]) as f:
                        content = f.read().decode('utf-8-sig', errors='replace').splitlines()
                        if content:
                            header_idx = -1
                            for i, line in enumerate(content[:5]):
                                if "Symbol" in line and "Traded" in line:
                                    header_idx = i
                                    break
                            
                            if header_idx != -1:
                                content = content[header_idx:]
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

                # Process Options
                if optidx_files:
                    with z.open(optidx_files[0]) as f:
                        content = f.read().decode('utf-8-sig', errors='replace').splitlines()
                        if content:
                            header_idx = -1
                            for i, line in enumerate(content[:5]):
                                if "Symbol" in line and "Traded" in line:
                                    header_idx = i
                                    break
                            
                            if header_idx != -1:
                                content = content[header_idx:]
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
                                    aggregated_data[key][3] += contracts
                                    aggregated_data[key][4] += quantity
                                    aggregated_data[key][5] += value
                        
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
        writer.writerow(["Date", "Symbol", "Futures Contracts", "Futures Quantity", "Futures Value (Rs. In Crs.)", 
                         "Options Contracts", "Options Quantity", "Options Value (Rs. In Crs.)", 
                         "Total Overall Value (Rs. In Crs.)"])
        
        for date_val, symbol in sorted_keys:
            fut_c, fut_q, fut_v, opt_c, opt_q, opt_v = aggregated_data[(date_val, symbol)]
            total_v = fut_v + opt_v
            
            # Only write rows where at least some trading happened
            if total_v > 0 or fut_c > 0 or opt_c > 0:
                writer.writerow([
                    date_val, symbol, 
                    fut_c, fut_q, f"{fut_v:.2f}",
                    opt_c, opt_q, f"{opt_v:.2f}",
                    f"{total_v:.2f}"
                ])
            
    print(f"Done! Aggregated data saved to {output_filename}")

if __name__ == "__main__":
    process_all_foidx()
