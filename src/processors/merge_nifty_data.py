import os
import pandas as pd
import numpy as np

def merge_nifty_with_expiries(
    data_path="data/processed/data.csv",
    expiries_path="data/processed/nifty_actual_expiries.csv",
    output_path="data/processed/nifty_data_with_expiries.csv"
):
    """
    Loads daily NIFTY market data, cleans column headers, sorts chronologically,
    and accurately merges with actual verified expiry dates.
    """
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Market data file not found: {data_path}")
    if not os.path.exists(expiries_path):
        raise FileNotFoundError(f"Expiries file not found: {expiries_path}")

    # 1. Load data
    df = pd.read_csv(data_path)
    exp = pd.read_csv(expiries_path)

    # Clean whitespace in column names (e.g. 'low ')
    df.columns = df.columns.str.strip()
    exp.columns = exp.columns.str.strip()

    # Parse and validate dates
    df['Date'] = pd.to_datetime(df['Date'])
    exp['ExpiryDate'] = pd.to_datetime(exp['ExpiryDate'])

    # Sort strictly chronologically
    df = df.sort_values('Date').reset_index(drop=True)

    # 2. Match with actual verified expiries
    actual_expiries = set(exp['ExpiryDate'])
    df['is_expiry'] = df['Date'].isin(actual_expiries)

    # 3. Add calendar metadata
    df['day_name'] = df['Date'].dt.day_name()
    df['day_of_week'] = df['Date'].dt.dayofweek
    df['year'] = df['Date'].dt.year
    df['month'] = df['Date'].dt.month

    # 4. Classify Expiry Type: Monthly vs Weekly vs Non-Expiry
    # The last expiry of each month represents the monthly contract settlement.
    df['expiry_type'] = np.where(df['is_expiry'], 'Weekly', 'Non-Expiry')
    
    # Identify last expiry in each month as 'Monthly'
    df_exp = df[df['is_expiry']].copy()
    df_exp['year_month'] = df_exp['Date'].dt.to_period('M')
    monthly_expiry_dates = set(df_exp.groupby('year_month')['Date'].max())
    df.loc[df['Date'].isin(monthly_expiry_dates), 'expiry_type'] = 'Monthly'

    # Save to output file
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df.to_csv(output_path, index=False)
        print(f"Successfully saved merged dataset ({len(df)} rows) to: {output_path}")

    return df

if __name__ == "__main__":
    df_merged = merge_nifty_with_expiries()
    
    # Print validation summary
    print("\n" + "="*50)
    print("VERIFICATION & VALIDATION SUMMARY")
    print("="*50)
    print(f"Total trading days: {len(df_merged)}")
    print(f"Date range: {df_merged['Date'].min().strftime('%Y-%m-%d')} to {df_merged['Date'].max().strftime('%Y-%m-%d')}")
    print(f"Total expiry days mapped: {df_merged['is_expiry'].sum()}")
    print(f"Expiry types breakdown:\n{df_merged['expiry_type'].value_counts().to_string()}")

    # 2023 - 2025 Deep Dive
    subset_mask = (df_merged['year'] >= 2023) & (df_merged['year'] <= 2025)
    df_sub = df_merged[subset_mask]
    print("\n" + "-"*50)
    print("2023 - 2025 FOCUS PERIOD BREAKDOWN")
    print("-"*50)
    print(f"Trading days in 2023-2025: {len(df_sub)}")
    print(f"Expiry days in 2023-2025: {df_sub['is_expiry'].sum()}")
    print("\nBreakdown by Year & Day of Week for Expiry Days:")
    exp_summary = df_sub[df_sub['is_expiry']].groupby(['year', 'day_name', 'expiry_type']).size().unstack(fill_value=0)
    print(exp_summary)
