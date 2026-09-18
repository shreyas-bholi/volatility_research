import os
import glob
import zipfile
import csv
import pandas as pd
import numpy as np

def get_actual_expiries(data_dir="data"):
    zip_files = glob.glob(os.path.join(data_dir, "FO_Market_Activity_Report_*.zip"))
    actual_expiries = set()
    
    for zip_path in zip_files:
        try:
            with zipfile.ZipFile(zip_path, 'r') as z:
                # Find op* file
                op_files = [name for name in z.namelist() if name.lower().startswith('op') and name.lower().endswith('.csv') and 'optidx' not in name and 'optstk' not in name]
                
                # If op01012016.csv style not found, try any op file
                if not op_files:
                    op_files = [name for name in z.namelist() if name.lower().startswith('op') and name.lower().endswith('.csv')]
                
                if not op_files:
                    continue
                    
                for op_filename in op_files:
                    with z.open(op_filename) as f:
                        # reading as lines
                        content = f.read().decode('utf-8-sig', errors='replace').splitlines()
                        if not content:
                            continue
                            
                        reader = csv.reader(content)
                        try:
                            headers = next(reader)
                        except StopIteration:
                            continue
                        
                        # Find indices
                        headers = [h.strip() for h in headers]
                        try:
                            sym_idx = headers.index('SYMBOL')
                            exp_idx = headers.index('EXP_DATE')
                            inst_idx = headers.index('INSTRUMENT')
                        except ValueError:
                            continue
                            
                        for row in reader:
                            if len(row) <= exp_idx:
                                continue
                            if row[inst_idx].strip() == 'OPTIDX' and row[sym_idx].strip() == 'NIFTY':
                                actual_expiries.add(row[exp_idx].strip())
        except Exception as e:
            pass
            
    # Convert to standard format
    formatted_expiries = set()
    for exp in actual_expiries:
        try:
            formatted_expiries.add(pd.to_datetime(exp, format='%d/%m/%Y').strftime('%Y-%m-%d'))
        except:
            pass
    return formatted_expiries

def get_predicted_expiries(start_date, end_date):
    df = pd.DataFrame({'Date': pd.date_range(start=start_date, end=end_date)})
    df['day_of_week'] = df['Date'].dt.dayofweek
    is_last_week = df['Date'].dt.month != (df['Date'] + pd.Timedelta(days=7)).dt.month
    is_thursday = df['day_of_week'] == 3
    is_tuesday = df['day_of_week'] == 1
    
    cond_pre_weekly = (df['Date'] < '2019-02-11') & is_thursday & is_last_week
    cond_weekly_thursday = (df['Date'] >= '2019-02-11') & (df['Date'] < '2025-09-02') & is_thursday
    cond_weekly_tuesday = (df['Date'] >= '2025-09-02') & is_tuesday
    
    df['is_expiry'] = cond_pre_weekly | cond_weekly_thursday | cond_weekly_tuesday
    
    return set(df[df['is_expiry']]['Date'].dt.strftime('%Y-%m-%d'))

print("Extracting actual expiries from zip files...")
actual_exp = get_actual_expiries()
print(f"Found {len(actual_exp)} unique actual expiries.")

if not actual_exp:
    print("No actual expiries found.")
    exit()

start = min(actual_exp)
end = max(actual_exp)
print(f"Date range: {start} to {end}")

print("Generating predicted expiries...")
pred_exp = get_predicted_expiries(start, end)
print(f"Generated {len(pred_exp)} predicted expiries.")

actual_but_not_pred = sorted(list(actual_exp - pred_exp))
pred_but_not_actual = sorted(list(pred_exp - actual_exp))

print(f"\nExpiries in Data but NOT Predicted ({len(actual_but_not_pred)}): (likely holiday shifts)")
print(actual_but_not_pred[:20])
if len(actual_but_not_pred) > 20: print("...")

print(f"\nPredicted but NOT in Data ({len(pred_but_not_actual)}): (likely holiday skips or logic mismatch)")
print(pred_but_not_actual[:20])
if len(pred_but_not_actual) > 20: print("...")

df_diff1 = pd.DataFrame({'Date': actual_but_not_pred, 'Type': 'Actual but not predicted'})
df_diff2 = pd.DataFrame({'Date': pred_but_not_actual, 'Type': 'Predicted but not actual'})
df_diff = pd.concat([df_diff1, df_diff2])
df_diff['Date'] = pd.to_datetime(df_diff['Date'])
df_diff.sort_values('Date', inplace=True)
df_diff.to_csv('expiry_differences.csv', index=False)
print("\nSaved differences to expiry_differences.csv")
