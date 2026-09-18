import requests
import urllib.parse
from datetime import datetime

session = requests.Session()
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}
session.headers.update(headers)

session.get("https://www.nseindia.com", timeout=10)

date_str = "23-Jul-2024" # Let's use a known date
# Let's try to fetch capital-market archives list or just guess the params
# Actually, the report name is usually "Market Activity Report" under Capital Market.
params = {
    'archives': '[{"name":"CM - Market Activity Report","type":"archives","category":"capital-market","section":"equities"}]',
    'date': date_str,
    'type': 'capital-market',
    'mode': 'single'
}

api_url = 'https://www.nseindia.com/api/reports?' + urllib.parse.urlencode(params)
print("URL:", api_url)
resp = session.get(api_url, timeout=15)
print("Status:", resp.status_code)
print("Content-Type:", resp.headers.get('content-type'))
print("Headers:", resp.headers)
if 'application/json' not in resp.headers.get('content-type', ''):
    with open('test_eq_report.csv', 'wb') as f:
        f.write(resp.content)
    print("Saved to test_eq_report.csv")
else:
    print(resp.json())
