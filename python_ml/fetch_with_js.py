"""
Try fetching with JavaScript rendering using requests-html
This can bypass some Cloudflare protections
"""

from requests_html import HTMLSession
import time
import re
from typing import Optional, List

def fetch_with_js_rendering(series_id: int) -> Optional[List[List[int]]]:
    """
    Fetch and render JavaScript on the page
    """
    url = f"https://chileresultados.com/kino/sorteos/{series_id}"

    print(f"🔍 Fetching Series {series_id} with JavaScript rendering...")
    print(f"   URL: {url}")
    print()

    session = HTMLSession()

    try:
        # Fetch the page
        print("   Making request...")
        response = session.get(url, timeout=15)

        print(f"   Status: {response.status_code}")

        if response.status_code != 200:
            print(f"   ❌ Failed: {response.status_code}")
            return None

        # Render JavaScript
        print("   Rendering JavaScript...")
        try:
            response.html.render(timeout=20, sleep=2)
            print("   ✅ JavaScript rendered")
        except Exception as e:
            print(f"   ⚠️  JavaScript rendering failed: {e}")
            print("   Continuing with raw HTML...")

        # Save rendered content
        html_content = response.html.html
        with open(f'rendered_page_{series_id}.html', 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"   💾 Saved to rendered_page_{series_id}.html")
        print()

        # Extract numbers
        text = response.html.text
        numbers = re.findall(r'\b(0[1-9]|1[0-9]|2[0-5])\b', text)

        if numbers:
            print(f"   Found {len(numbers)} valid numbers (01-25)")

            # Convert to integers
            numbers = [int(n) for n in numbers]

            # Try to extract 7 events
            events = []
            i = 0
            while i <= len(numbers) - 14:
                candidate = numbers[i:i+14]
                if len(set(candidate)) == 14 and all(1 <= n <= 25 for n in candidate):
                    events.append(sorted(candidate))
                    i += 14
                else:
                    i += 1

            if len(events) >= 7:
                print(f"   ✅ Extracted {len(events)} events!")
                print()
                for i, event in enumerate(events[:7], 1):
                    print(f"   Event {i}: {' '.join(f'{n:02d}' for n in event)}")
                return events[:7]
            else:
                print(f"   ⚠️  Only found {len(events)} valid events (need 7)")
        else:
            print("   ❌ No valid numbers found")

        return None

    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("="*70)
    print("JAVASCRIPT RENDERING TEST")
    print("="*70)
    print()

    # Test on Series 3146
    events = fetch_with_js_rendering(3146)

    if events:
        print()
        print("="*70)
        print("✅ SUCCESS!")
        print("="*70)
    else:
        print()
        print("="*70)
        print("❌ FAILED - site protection too strong")
        print("="*70)
        print()
        print("Alternatives:")
        print("1. Database export from LuckyDb for earlier series")
        print("2. Manual data collection from browser")
        print("3. Selenium with real Chrome browser")
        print("="*70)
