"""
Fetch data using Playwright with real Chromium browser
"""

from playwright.sync_api import sync_playwright
import re
import json
import time
from typing import Optional, List

def fetch_series_with_playwright(series_id: int) -> Optional[List[List[int]]]:
    """
    Fetch a series using real browser automation
    """
    url = f"https://chileresultados.com/kino/sorteos/{series_id}"

    print(f"🔍 Fetching Series {series_id} with Playwright...")
    print(f"   URL: {url}")

    with sync_playwright() as p:
        # Launch browser (headless mode)
        print("   Launching Chromium browser...")
        browser = p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )

        # Create context with realistic settings
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )

        # Create page
        page = context.new_page()

        try:
            # Navigate to page
            print("   Navigating to page...")
            response = page.goto(url, wait_until='networkidle', timeout=30000)

            print(f"   Response status: {response.status}")

            if response.status != 200:
                print(f"   ❌ Failed: HTTP {response.status}")
                browser.close()
                return None

            # Wait for content to load
            print("   Waiting for content...")
            page.wait_for_timeout(3000)

            # Get page content
            content = page.content()

            # Save for debugging
            with open(f'playwright_page_{series_id}.html', 'w', encoding='utf-8') as f:
                f.write(content)

            print(f"   💾 Saved to playwright_page_{series_id}.html")

            # Get text content
            text = page.inner_text('body')

            # Extract numbers
            numbers = re.findall(r'\b(0[1-9]|1[0-9]|2[0-5])\b', text)

            if not numbers:
                print("   ❌ No numbers found")
                browser.close()
                return None

            print(f"   Found {len(numbers)} valid numbers (01-25)")

            # Convert to integers
            numbers = [int(n) for n in numbers]

            # Extract events (14 numbers each)
            events = []
            i = 0
            while i <= len(numbers) - 14:
                candidate = numbers[i:i+14]
                # Validate: 14 unique numbers between 1-25
                if len(set(candidate)) == 14 and all(1 <= n <= 25 for n in candidate):
                    events.append(sorted(candidate))
                    i += 14
                else:
                    i += 1

            browser.close()

            if len(events) >= 7:
                print(f"   ✅ Extracted {len(events)} events!")
                for i, event in enumerate(events[:7], 1):
                    print(f"      Event {i}: {' '.join(f'{n:02d}' for n in event)}")
                return events[:7]
            else:
                print(f"   ⚠️  Only found {len(events)} events (need 7)")
                return None

        except Exception as e:
            print(f"   ❌ Error: {e}")
            browser.close()
            return None

if __name__ == "__main__":
    print("="*70)
    print("PLAYWRIGHT BROWSER AUTOMATION TEST")
    print("="*70)
    print()

    # Test on Series 2800 (as user specified)
    events = fetch_series_with_playwright(2800)

    if events:
        print()
        print("="*70)
        print("✅ SUCCESS!")
        print("="*70)

        # Save result
        result = {
            "series_id": 2800,
            "events": events,
            "method": "playwright"
        }

        with open('test_2800_result.json', 'w') as f:
            json.dump(result, f, indent=2)

        print("💾 Saved to test_2800_result.json")
    else:
        print()
        print("="*70)
        print("❌ FAILED")
        print("="*70)
