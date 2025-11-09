"""
Test scraper on a known series to verify HTML parsing
"""

import requests
from bs4 import BeautifulSoup
import re

def test_scrape(series_id: int = 3146):
    """Test scraping a known series"""
    url = f"https://chileresultados.com/kino/sorteos/{series_id}"

    print(f"Testing scraper on Series {series_id}")
    print(f"URL: {url}")
    print()

    try:
        # Use browser-like headers to avoid 403 Forbidden
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-CL,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        print(f"✅ Response: {response.status_code}")
        print(f"✅ Content length: {len(response.content)} bytes")
        print()

        soup = BeautifulSoup(response.content, 'html.parser')

        # Save HTML for inspection
        with open('sample_page.html', 'w', encoding='utf-8') as f:
            f.write(soup.prettify())

        print("✅ Saved HTML to sample_page.html")
        print()

        # Try to find numbers
        print("Looking for numbers in the page...")
        print()

        # Method 1: Look for common number class names
        number_elements = soup.find_all(class_=re.compile('ball|bola|number|numero', re.I))
        print(f"Method 1 (class names): Found {len(number_elements)} elements")
        if number_elements:
            print("Sample elements:")
            for elem in number_elements[:5]:
                print(f"  {elem.get('class')}: {elem.get_text().strip()}")
        print()

        # Method 2: Extract all 2-digit numbers from text
        all_text = soup.get_text()
        numbers = re.findall(r'\b(0[1-9]|1[0-9]|2[0-5])\b', all_text)
        print(f"Method 2 (regex): Found {len(numbers)} valid numbers (01-25)")
        if numbers:
            numbers_int = [int(n) for n in numbers]
            print(f"First 50 numbers: {numbers_int[:50]}")
            print()

            # Try to group into events
            if len(numbers_int) >= 98:
                print("Attempting to group into 7 events of 14 numbers:")
                for i in range(7):
                    event = sorted(numbers_int[i*14:(i+1)*14])
                    print(f"  Event {i+1}: {' '.join(f'{n:02d}' for n in event)}")
                print()

        # Method 3: Look for specific table/div structure
        tables = soup.find_all('table')
        print(f"Method 3 (tables): Found {len(tables)} tables")

        divs = soup.find_all('div', class_=re.compile('result|evento|event', re.I))
        print(f"Method 3 (result divs): Found {len(divs)} divs")
        print()

        # Show page title for verification
        title = soup.find('title')
        if title:
            print(f"Page title: {title.get_text().strip()}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_scrape(3146)
