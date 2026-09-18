import os
import csv
from datetime import datetime

def parse_equity_summary(filepath):
    summary = {
        'eq_traded_value': '0.0',
        'eq_traded_qty': '0.0',
        'eq_trades': '0',
        'eq_market_cap': '0.0'
    }
    
    if not os.path.exists(filepath):
        return summary
        
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for _ in range(15):  # Check first 15 lines
                line = f.readline()
                if not line:
                    break
                parts = line.split(',')
                if len(parts) >= 3:
                    key = parts[1].strip()
                    val = parts[2].strip()
                    
                    if key == 'Traded Value (Rs. In Crores)':
                        summary['eq_traded_value'] = val
                    elif key == 'Traded Quantity (in Lakhs)':
                        summary['eq_traded_qty'] = val
                    elif key == 'Number of Trades':
                        summary['eq_trades'] = val
                    elif key == 'Total Market Capitalisation (Rs. Crores)':
                        summary['eq_market_cap'] = val
    except Exception as e:
        print(f"Error parsing {filepath}: {e}")
        
    return summary

def process_combined_data(fo_filename="Consolidated_FO_Idx_Data.csv", eq_dir="equity data", out_filename="Consolidated_All_Market_Data.csv"):
    if not os.path.exists(fo_filename):
        print(f"Error: {fo_filename} not found.")
        return
        
    print(f"Reading {fo_filename} and augmenting with equity data...")
    
    eq_cache = {} # date_str -> summary dict
    
    with open(fo_filename, 'r', encoding='utf-8') as f_in, \
         open(out_filename, 'w', newline='', encoding='utf-8') as f_out:
         
        reader = csv.reader(f_in)
        writer = csv.writer(f_out)
        
        headers = next(reader)
        new_headers = headers + [
            "Equity Traded Value (Rs. In Crs.)",
            "Equity Traded Quantity (in Lakhs)",
            "Equity Number of Trades",
            "Equity Total Market Cap (Rs. Crs.)"
        ]
        writer.writerow(new_headers)
        
        rows_processed = 0
        
        for row in reader:
            if not row: continue
            
            date_val = row[0]
            
            if date_val not in eq_cache:
                # convert YYYY-MM-DD to YYYYMMDD
                try:
                    dt = datetime.strptime(date_val, "%Y-%m-%d")
                    eq_filename = f"EQ_Market_Activity_Report_{dt.strftime('%Y%m%d')}.csv"
                    eq_filepath = os.path.join(eq_dir, eq_filename)
                    eq_cache[date_val] = parse_equity_summary(eq_filepath)
                except ValueError:
                    eq_cache[date_val] = {
                        'eq_traded_value': '0.0', 'eq_traded_qty': '0.0', 
                        'eq_trades': '0', 'eq_market_cap': '0.0'
                    }
                    
            summary = eq_cache[date_val]
            
            new_row = row + [
                summary['eq_traded_value'],
                summary['eq_traded_qty'],
                summary['eq_trades'],
                summary['eq_market_cap']
            ]
            writer.writerow(new_row)
            rows_processed += 1
            
    print(f"Done! Saved {rows_processed} rows to {out_filename}")

if __name__ == "__main__":
    process_combined_data()
