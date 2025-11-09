"""
Scrape historical lottery data from chileresultados.com

Current dataset gaps:
- 2800-2897 (~98 draws)
- 2908-2979 (~72 draws)

Total potential: ~170 additional series!
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import re
from typing import List, Dict, Optional

def scrape_series(series_id: int) -> Optional[List[List[int]]]:
    """
    Scrape a single series from chileresultados.com

    Returns: List of 7 events, each with 14 numbers, or None if failed
    """
    url = f"https://chileresultados.com/kino/sorteos/{series_id}"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # Find all number elements
        # The site shows 7 events, each with 14 numbers
        # We need to parse the HTML structure to extract them

        events = []

        # Look for number containers - adjust selectors based on actual HTML structure
        # This is a generic approach - may need adjustment based on actual page structure
        number_containers = soup.find_all(class_=re.compile('number|numero|ball|bola', re.I))

        if not number_containers:
            # Try alternative: find all elements with numbers
            all_text = soup.get_text()
            # Extract all 2-digit numbers between 01-25
            numbers = re.findall(r'\b(0[1-9]|1[0-9]|2[0-5])\b', all_text)
            numbers = [int(n) for n in numbers]

            if len(numbers) >= 98:  # 7 events * 14 numbers = 98
                # Group into events of 14
                for i in range(0, min(98, len(numbers)), 14):
                    event = sorted(numbers[i:i+14])
                    if len(event) == 14:
                        events.append(event)

                if len(events) >= 7:
                    return events[:7]

        else:
            # Extract numbers from containers
            all_numbers = []
            for container in number_containers:
                text = container.get_text().strip()
                # Try to extract number
                match = re.search(r'\b(0[1-9]|1[0-9]|2[0-5])\b', text)
                if match:
                    all_numbers.append(int(match.group(1)))

            # Group into events
            if len(all_numbers) >= 98:
                for i in range(0, min(98, len(all_numbers)), 14):
                    event = sorted(all_numbers[i:i+14])
                    if len(event) == 14:
                        events.append(event)

                if len(events) >= 7:
                    return events[:7]

        print(f"  ⚠️ Series {series_id}: Could not parse 7 complete events")
        return None

    except requests.exceptions.RequestException as e:
        print(f"  ❌ Series {series_id}: Network error - {e}")
        return None
    except Exception as e:
        print(f"  ❌ Series {series_id}: Parse error - {e}")
        return None

def scrape_range(start: int, end: int, delay: float = 1.0) -> Dict[int, List[List[int]]]:
    """
    Scrape a range of series

    Args:
        start: First series ID
        end: Last series ID (inclusive)
        delay: Delay between requests in seconds (be nice to the server!)

    Returns: Dict of {series_id: [7 events]}
    """
    scraped_data = {}
    total = end - start + 1

    print(f"\nScraping series {start} to {end} ({total} total)...")
    print(f"Delay between requests: {delay}s")
    print()

    for series_id in range(start, end + 1):
        print(f"[{series_id - start + 1}/{total}] Scraping series {series_id}...", end=" ")

        events = scrape_series(series_id)

        if events:
            scraped_data[series_id] = events
            print(f"✅ Got 7 events")
        else:
            print(f"❌ Failed")

        # Be nice to the server
        if series_id < end:
            time.sleep(delay)

    return scraped_data

def main():
    """
    Scrape all missing historical data
    """
    print("="*70)
    print("HISTORICAL DATA SCRAPER")
    print("="*70)
    print()

    # Load current expanded data to know what we have
    print("Loading current dataset...")
    with open('full_series_data_expanded.json') as f:
        current_data = json.load(f)

    current_ids = set(int(k) for k in current_data.keys())
    print(f"✅ Current dataset: {len(current_ids)} series")
    print(f"   Range: {min(current_ids)} to {max(current_ids)}")
    print()

    # Identify gaps
    print("Identifying missing series...")
    missing_ranges = []

    # Gap 1: 2800-2897
    gap1_start = 2800
    gap1_end = 2897
    gap1_missing = [i for i in range(gap1_start, gap1_end + 1) if i not in current_ids]
    if gap1_missing:
        missing_ranges.append((min(gap1_missing), max(gap1_missing)))
        print(f"  Gap 1: {min(gap1_missing)}-{max(gap1_missing)} ({len(gap1_missing)} series)")

    # Gap 2: 2908-2979
    gap2_start = 2908
    gap2_end = 2979
    gap2_missing = [i for i in range(gap2_start, gap2_end + 1) if i not in current_ids]
    if gap2_missing:
        missing_ranges.append((min(gap2_missing), max(gap2_missing)))
        print(f"  Gap 2: {min(gap2_missing)}-{max(gap2_missing)} ({len(gap2_missing)} series)")

    total_missing = len(gap1_missing) + len(gap2_missing)
    print()
    print(f"📊 Total missing: {total_missing} series")
    print()

    # Ask for confirmation
    print("⚠️  WARNING: This will make ~170 HTTP requests to chileresultados.com")
    print("   With 1s delay, this will take ~3 minutes")
    print()

    # Start scraping
    all_scraped = {}

    for start, end in missing_ranges:
        scraped = scrape_range(start, end, delay=1.0)
        all_scraped.update(scraped)
        print()
        print(f"✅ Scraped {len(scraped)} series from range {start}-{end}")
        print()

    # Merge with current data
    print("="*70)
    print("MERGING DATA")
    print("="*70)
    print()

    # Convert current data to int keys
    merged_data = {int(k): v for k, v in current_data.items()}

    # Add scraped data
    for series_id, events in all_scraped.items():
        merged_data[series_id] = events

    print(f"Previous: {len(current_data)} series")
    print(f"Scraped: {len(all_scraped)} series")
    print(f"Total: {len(merged_data)} series")
    print(f"Growth: +{len(all_scraped)} series (+{len(all_scraped)/len(current_data)*100:.1f}%)")
    print()

    # Show final range
    all_ids = sorted(merged_data.keys())
    print(f"Final range: {all_ids[0]} to {all_ids[-1]}")
    print(f"Total events: {len(all_ids) * 7}")
    print()

    # Save
    output_file = 'full_series_data_scraped.json'
    with open(output_file, 'w') as f:
        json_data = {str(k): v for k, v in merged_data.items()}
        json.dump(json_data, f, indent=2)

    print(f"💾 Saved to: {output_file}")
    print()

    # Summary
    print("="*70)
    print("SCRAPING SUMMARY")
    print("="*70)
    print(f"✅ Successfully scraped: {len(all_scraped)} series")
    print(f"✅ Final dataset: {len(merged_data)} series")
    print(f"✅ Dataset growth: +{len(all_scraped)/len(current_data)*100:.1f}%")
    print()

    if len(all_scraped) < total_missing:
        failed = total_missing - len(all_scraped)
        print(f"⚠️  Failed to scrape: {failed} series ({failed/total_missing*100:.1f}%)")
        print(f"   Some draws may not exist or have incomplete data")

    print("="*70)

if __name__ == "__main__":
    main()
