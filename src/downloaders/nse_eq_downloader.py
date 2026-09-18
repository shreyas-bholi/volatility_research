import requests
import urllib.parse
from datetime import datetime, timedelta
import os
import argparse
import time

def download_eq_market_activity_report(date_obj, output_dir="."):
    # Setup session with headers
    session = requests.Session()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    session.headers.update(headers)
    
    # Format date for the API (e.g., 23-Jul-2026)
    date_str = date_obj.strftime("%d-%b-%Y")
    filename = f"EQ_Market_Activity_Report_{date_obj.strftime('%Y%m%d')}.csv"
    filepath = os.path.join(output_dir, filename)
    
    # Idempotency check
    if os.path.exists(filepath):
        print(f"Skipping {filename} - already exists.")
        return True
    
    # Initialize session by visiting main page to get cookies
    try:
        session.get("https://www.nseindia.com", timeout=10)
    except Exception as e:
        print(f"Warning: Failed to fetch cookies from main page: {e}")

    # Construct the API request parameters for Equity
    params = {
        'archives': '[{"name":"CM - Market Activity Report","type":"archives","category":"capital-market","section":"equities"}]',
        'date': date_str,
        'type': 'capital-market',
        'mode': 'single'
    }
    
    api_url = 'https://www.nseindia.com/api/reports?' + urllib.parse.urlencode(params)
    
    print(f"\n--- Fetching 'CM - Market Activity Report' for {date_str} ---")
    
    try:
        response = session.get(api_url, timeout=15)
        
        if response.status_code == 200:
            if 'application/json' in response.headers.get('content-type', ''):
                print("Error: Received JSON response instead of a file. The data might not be available for this date.")
                return False
                
            with open(filepath, 'wb') as f:
                f.write(response.content)
            print(f"Successfully downloaded: {filename}")
            return True
            
        elif response.status_code == 404:
            print(f"File not found (404). Data might not be available for this date (e.g., weekend/holiday).")
        elif response.status_code == 403:
            print(f"Access forbidden (403). NSE might be blocking the request. Ensure proper headers are used.")
        else:
            print(f"Failed with status code: {response.status_code}")
            
    except Exception as e:
        print(f"Error during download: {e}")
        
    return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download NSE Equity Market Activity Report from Archives")
    parser.add_argument("--date", help="Single date in YYYY-MM-DD format. Defaults to yesterday if no dates are provided.", default=None)
    parser.add_argument("--start-date", help="Start date in YYYY-MM-DD format for downloading a range.", default=None)
    parser.add_argument("--end-date", help="End date in YYYY-MM-DD format. Used with --start-date. Defaults to today.", default=None)
    parser.add_argument("--outdir", help="Output directory to save files.", default="equity data")
    
    args = parser.parse_args()
    
    # Ensure output directory exists
    if not os.path.exists(args.outdir):
        os.makedirs(args.outdir)
    
    dates_to_fetch = []
    
    if args.start_date:
        try:
            start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
            if args.end_date:
                end_date = datetime.strptime(args.end_date, "%Y-%m-%d")
            else:
                end_date = datetime.now()
                
            if start_date > end_date:
                print("Error: start-date cannot be after end-date.")
                exit(1)
                
            current_date = start_date
            while current_date <= end_date:
                # Skip weekends
                if current_date.weekday() < 5:
                    dates_to_fetch.append(current_date)
                current_date += timedelta(days=1)
        except ValueError:
            print("Invalid date format. Please use YYYY-MM-DD.")
            exit(1)
    elif args.date:
        try:
            dates_to_fetch.append(datetime.strptime(args.date, "%Y-%m-%d"))
        except ValueError:
            print("Invalid date format. Please use YYYY-MM-DD.")
            exit(1)
    else:
        # Default to previous day if no date is provided
        dates_to_fetch.append(datetime.now() - timedelta(days=1))
        
    print(f"Total dates to fetch: {len(dates_to_fetch)} (excluding weekends)")
    
    for i, target_date in enumerate(dates_to_fetch):
        download_eq_market_activity_report(target_date, args.outdir)
        
        # Add a delay between requests to avoid rate limiting
        if i < len(dates_to_fetch) - 1:
            time.sleep(2)
