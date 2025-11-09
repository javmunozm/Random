"""
Advanced web scraper with multiple bypass techniques
"""

import requests
from bs4 import BeautifulSoup
import time
import json
import re
from typing import Optional, List

def fetch_with_session(series_id: int) -> Optional[requests.Response]:
    """
    Fetch using a persistent session with full browser headers
    """
    session = requests.Session()

    # Full browser headers
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'es-CL,es;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0',
        'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"'
    }

    url = f"https://chileresultados.com/kino/sorteos/{series_id}"

    try:
        # First, visit the main page to get cookies
        session.get('https://chileresultados.com/', headers=headers, timeout=10)
        time.sleep(1)

        # Then fetch the specific series page
        response = session.get(url, headers=headers, timeout=10)
        return response
    except Exception as e:
        print(f"Session method failed: {e}")
        return None

def fetch_simple(series_id: int) -> Optional[requests.Response]:
    """
    Simple fetch with minimal headers
    """
    url = f"https://chileresultados.com/kino/sorteos/{series_id}"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0'
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        return response
    except Exception as e:
        print(f"Simple method failed: {e}")
        return None

def fetch_with_referer(series_id: int) -> Optional[requests.Response]:
    """
    Fetch with referer (as if navigating from main site)
    """
    url = f"https://chileresultados.com/kino/sorteos/{series_id}"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://chileresultados.com/kino',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'es-CL,es;q=0.9'
    }

    try:
        response = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
        return response
    except Exception as e:
        print(f"Referer method failed: {e}")
        return None

def parse_kino_page(html_content: str, series_id: int) -> Optional[List[List[int]]]:
    """
    Parse the Kino results page to extract 7 events with 14 numbers each
    """
    soup = BeautifulSoup(html_content, 'html.parser')

    # Save for debugging
    with open(f'debug_page_{series_id}.html', 'w', encoding='utf-8') as f:
        f.write(soup.prettify())

    print(f"\n📄 Parsing Series {series_id}...")
    print(f"   Page title: {soup.find('title').get_text() if soup.find('title') else 'N/A'}")

    # Strategy 1: Look for specific Kino number containers
    # Common patterns: class="ball", class="number", data-number, etc.

    # Try to find all number elements
    number_patterns = [
        {'class': re.compile(r'ball', re.I)},
        {'class': re.compile(r'numero', re.I)},
        {'class': re.compile(r'number', re.I)},
        {'class': re.compile(r'bola', re.I)},
        {'data-number': True},
    ]

    all_numbers = []

    for pattern in number_patterns:
        elements = soup.find_all(attrs=pattern)
        if elements:
            print(f"   Found {len(elements)} elements matching {pattern}")
            for elem in elements[:5]:
                print(f"      Sample: {elem.get('class')} = {elem.get_text().strip()}")
            break

    # Strategy 2: Extract all 2-digit numbers from page text
    text_content = soup.get_text()

    # Find all numbers 01-25
    raw_numbers = re.findall(r'\b(0[1-9]|1[0-9]|2[0-5])\b', text_content)

    if raw_numbers:
        numbers = [int(n) for n in raw_numbers]
        print(f"   Found {len(numbers)} valid numbers (01-25) in text")

        # Look for sequences of 14 numbers
        events = []
        i = 0
        while i <= len(numbers) - 14:
            # Check if next 14 numbers could be an event
            candidate = numbers[i:i+14]

            # Basic validation: should have 14 unique numbers between 1-25
            if len(set(candidate)) == 14 and all(1 <= n <= 25 for n in candidate):
                events.append(sorted(candidate))
                print(f"   Event {len(events)}: {' '.join(f'{n:02d}' for n in sorted(candidate))}")
                i += 14
            else:
                i += 1

        if len(events) >= 7:
            print(f"   ✅ Successfully extracted {len(events)} events")
            return events[:7]
        else:
            print(f"   ⚠️  Only found {len(events)} valid events (need 7)")

    # Strategy 3: Look for table structure
    tables = soup.find_all('table')
    if tables:
        print(f"   Found {len(tables)} tables - analyzing...")
        for table in tables:
            cells = table.find_all(['td', 'th'])
            table_numbers = []
            for cell in cells:
                text = cell.get_text().strip()
                match = re.search(r'\b(0[1-9]|1[0-9]|2[0-5])\b', text)
                if match:
                    table_numbers.append(int(match.group(1)))

            if len(table_numbers) >= 98:
                print(f"      Table has {len(table_numbers)} numbers - extracting events...")
                # Extract events similar to Strategy 2

    return None

def test_all_methods(series_id: int = 3146):
    """
    Test all fetching methods
    """
    print("="*70)
    print(f"TESTING MULTIPLE FETCH METHODS FOR SERIES {series_id}")
    print("="*70)
    print()

    methods = [
        ("Session with cookies", fetch_with_session),
        ("Simple with Firefox UA", fetch_simple),
        ("With Referer header", fetch_with_referer),
    ]

    for name, method in methods:
        print(f"\n🔍 Method: {name}")
        print("-" * 50)

        response = method(series_id)

        if response is None:
            print("❌ Failed to fetch (exception)")
            continue

        print(f"Status: {response.status_code}")
        print(f"Content-Length: {len(response.content)}")
        print(f"Content-Type: {response.headers.get('Content-Type', 'N/A')}")

        if response.status_code == 200:
            print("✅ SUCCESS!")

            # Try to parse
            events = parse_kino_page(response.text, series_id)

            if events and len(events) == 7:
                print("\n" + "="*70)
                print("✅ SUCCESSFULLY EXTRACTED DATA!")
                print("="*70)
                for i, event in enumerate(events, 1):
                    print(f"Event {i}: {' '.join(f'{n:02d}' for n in event)}")

                return events
            else:
                print("⚠️  Could not parse 7 events from page")
                print("   Check debug_page_{series_id}.html for manual inspection")

        elif response.status_code == 403:
            print("❌ 403 Forbidden - blocked")
        elif response.status_code == 404:
            print("❌ 404 Not Found - URL may be wrong or series doesn't exist")
        else:
            print(f"❌ Unexpected status code")

        time.sleep(2)  # Wait between methods

    print("\n" + "="*70)
    print("ALL METHODS FAILED")
    print("="*70)
    return None

if __name__ == "__main__":
    # Test on a known recent series
    test_all_methods(3146)

    # Also test an older series
    print("\n\n")
    test_all_methods(2900)
