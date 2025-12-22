#!/usr/bin/env python3
"""
Download German and EU Legal Documents

Sources:
- German Federal Laws: gesetze-im-internet.de (Official - German Federal Ministry of Justice)
- EU Regulations: EUR-Lex (Official EU Law Portal)

Run this script to download all available legal documents for the Legal Assistant chatbot.
"""

import os
import sys
import time
import requests
import xml.etree.ElementTree as ET
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# Target directory for legal documents
LEGAL_DOCS_DIR = Path(__file__).parent.parent / "app" / "data" / "rag" / "legal"
BUNDESGESETZE_DIR = LEGAL_DOCS_DIR / "bundesgesetze"
EU_GESETZE_DIR = LEGAL_DOCS_DIR / "eu_recht"

# User agent for requests
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/pdf,application/octet-stream,*/*',
    'Accept-Language': 'de-DE,de;q=0.9,en;q=0.8',
}

# EU Laws to download (important regulations) - using alternative PDF sources
EU_LAWS = [
    # DSGVO / GDPR - from official DE source
    {
        "filename": "DSGVO_2016_679.pdf",
        "urls": [
            "https://dsgvo-gesetz.de/dsgvo-volltext.pdf",
            "https://www.datenschutz-grundverordnung.eu/wp-content/uploads/2016/04/CELEX_32016R0679_DE_TXT.pdf",
        ],
        "name": "Datenschutz-Grundverordnung (DSGVO/GDPR)",
        "category": "datenschutz"
    },
    # BDSG - Bundesdatenschutzgesetz (already on gesetze-im-internet.de, but adding here too)
    {
        "filename": "BDSG.pdf",
        "urls": [
            "https://www.gesetze-im-internet.de/bdsg_2018/BDSG.pdf",
        ],
        "name": "Bundesdatenschutzgesetz (BDSG)",
        "category": "datenschutz"
    },
]

# Priority German laws (download these first, always)
PRIORITY_LAWS = [
    "gg", "bgb", "hgb", "stgb", "stpo", "zpo", "arbgg", "kschg", "betrvg",
    "arbzg", "muschg_2018", "beeg", "sgb_1", "sgb_2", "sgb_3", "sgb_4",
    "sgb_5", "sgb_6", "sgb_7", "sgb_8", "sgb_9", "sgb_10", "sgb_11", "sgb_12",
    "vwgo", "vwvfg", "ao_1977", "estg", "ustg_1980", "gmbhg", "aktg", "inso",
    "bdsg_2018", "uwg_2004", "gwb", "urhg", "markeng", "bbaug", "stvg",
    "stvo_2013", "bimschg", "agg", "tmg", "btmg", "tkg", "famfg",
    "gvg", "gbo", "patg", "gebrg", "ifsg", "amg",
    "arbschg", "owig", "vvg", "wphg", "kagb",
]


def download_file(url: str, filepath: Path, name: str = None, timeout: int = 120) -> bool:
    """Download a file from URL to filepath."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=timeout, stream=True, allow_redirects=True)
        response.raise_for_status()

        # Check content type - should be PDF or octet-stream
        content_type = response.headers.get('content-type', '').lower()

        # Skip if it's HTML (error page)
        if 'text/html' in content_type:
            # Check if it starts with PDF magic bytes anyway
            first_bytes = response.content[:10]
            if not first_bytes.startswith(b'%PDF'):
                return False

        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        # Verify it's a valid PDF (check magic bytes)
        with open(filepath, 'rb') as f:
            magic = f.read(5)
            if magic != b'%PDF-':
                filepath.unlink()
                return False

        # Verify file size (PDFs should be at least 1KB)
        if filepath.stat().st_size < 1000:
            filepath.unlink()
            return False

        return True

    except Exception as e:
        if filepath.exists():
            filepath.unlink()
        return False


def get_all_bundesgesetze():
    """
    Fetch list of all German federal laws from gesetze-im-internet.de XML.
    Returns list of (abbreviation, title) tuples.
    """
    print("Fetching list of all Bundesgesetze from gesetze-im-internet.de...")

    try:
        response = requests.get(
            "https://www.gesetze-im-internet.de/gii-toc.xml",
            headers=HEADERS,
            timeout=60
        )
        response.raise_for_status()

        # Parse XML
        root = ET.fromstring(response.content)

        laws = []
        for item in root.findall('.//item'):
            link = item.find('link')
            title = item.find('title')

            if link is not None and title is not None:
                url = link.text
                if url and '/xml.zip' in url:
                    # Extract abbreviation from URL
                    # e.g., "http://www.gesetze-im-internet.de/bgb/xml.zip" -> "bgb"
                    parts = url.rstrip('/').replace('/xml.zip', '').split('/')
                    if len(parts) >= 1:
                        abbrev = parts[-1]
                        # Filter out obviously bad entries
                        if abbrev and len(abbrev) < 50 and not abbrev.startswith('.'):
                            laws.append((abbrev, title.text))

        print(f"Found {len(laws)} Bundesgesetze")
        return laws

    except Exception as e:
        print(f"Error fetching law list: {e}")
        return []


def get_pdf_filename(abbrev: str) -> str:
    """
    Get the correct PDF filename for a law abbreviation.
    Most laws use uppercase abbreviation, some use mixed case.
    """
    # Special cases with known naming
    special_cases = {
        "bgb": "BGB",
        "hgb": "HGB",
        "stgb": "StGB",
        "stpo": "StPO",
        "zpo": "ZPO",
        "gg": "GG",
        "gvg": "GVG",
        "gbo": "GBO",
        "gwb": "GWB",
        "vwgo": "VwGO",
        "vwvfg": "VwVfG",
        "agg": "AGG",
        "tmg": "TMG",
        "tkg": "TKG",
        "owig": "OWiG",
        "vvg": "VVG",
        "aktg": "AktG",
        "gmbhg": "GmbHG",
        "patg": "PatG",
        "gebrg": "GebrG",
        "arbgg": "ArbGG",
        "arbzg": "ArbZG",
        "arbschg": "ArbSchG",
        "betrvg": "BetrVG",
        "kschg": "KSchG",
        "muschg_2018": "MuSchG",
        "beeg": "BEEG",
        "bimschg": "BImSchG",
        "btmg": "BtMG",
        "amg": "AMG",
        "ifsg": "IfSG",
        "inso": "InsO",
        "urhg": "UrhG",
        "markeng": "MarkenG",
        "uwg_2004": "UWG",
        "wphg": "WpHG",
        "kagb": "KAGB",
        "ao_1977": "AO",
        "estg": "EStG",
        "ustg_1980": "UStG",
        "stvg": "StVG",
        "stvo_2013": "StVO",
        "famfg": "FamFG",
        "bdsg_2018": "BDSG",
    }

    if abbrev.lower() in special_cases:
        return special_cases[abbrev.lower()]

    # For SGB books
    if abbrev.lower().startswith("sgb_"):
        return abbrev.upper()

    # Default: uppercase
    return abbrev.upper()


def download_bundesgesetz(abbrev: str, title: str, target_dir: Path) -> tuple:
    """Download a single Bundesgesetz PDF."""
    pdf_name = get_pdf_filename(abbrev)
    filename = f"{pdf_name}.pdf"
    filepath = target_dir / filename

    # Skip if already exists
    if filepath.exists() and filepath.stat().st_size > 1000:
        return (abbrev, "skipped", title)

    # Try different URL patterns
    url_patterns = [
        f"https://www.gesetze-im-internet.de/{abbrev}/{pdf_name}.pdf",
        f"https://www.gesetze-im-internet.de/{abbrev}/{abbrev.upper()}.pdf",
        f"https://www.gesetze-im-internet.de/{abbrev}/{abbrev}.pdf",
    ]

    for url in url_patterns:
        if download_file(url, filepath, title):
            size_kb = filepath.stat().st_size / 1024
            return (abbrev, "downloaded", f"{title} ({size_kb:.0f} KB)")

    return (abbrev, "failed", title)


def download_eu_law(law: dict, target_dir: Path) -> tuple:
    """Download a single EU law PDF."""
    filepath = target_dir / law["filename"]

    # Skip if already exists
    if filepath.exists() and filepath.stat().st_size > 1000:
        return (law["name"], "skipped", "")

    # Try all URLs
    for url in law.get("urls", []):
        if download_file(url, filepath, law["name"]):
            size_kb = filepath.stat().st_size / 1024
            return (law["name"], "downloaded", f"({size_kb:.0f} KB)")

    return (law["name"], "failed", "")


def main():
    print("=" * 70)
    print("LLARS Legal Documents Downloader")
    print("=" * 70)
    print()
    print("Sources:")
    print("  - Bundesgesetze: gesetze-im-internet.de (German Federal Ministry of Justice)")
    print("  - EU-Recht: Various official sources")
    print()

    # Create directories
    BUNDESGESETZE_DIR.mkdir(parents=True, exist_ok=True)
    EU_GESETZE_DIR.mkdir(parents=True, exist_ok=True)

    # Stats
    stats = {
        "downloaded": 0,
        "skipped": 0,
        "failed": 0
    }

    # ==================== EU LAWS ====================
    print("-" * 70)
    print(f"Downloading {len(EU_LAWS)} EU Laws...")
    print("-" * 70)

    for law in EU_LAWS:
        name, status, extra = download_eu_law(law, EU_GESETZE_DIR)
        stats[status] += 1
        symbol = {"downloaded": "✓", "skipped": "○", "failed": "✗"}[status]
        print(f"  {symbol} {name} {extra}")
        time.sleep(0.3)

    # ==================== BUNDESGESETZE ====================
    print()
    print("-" * 70)
    print("Downloading Bundesgesetze...")
    print("-" * 70)

    # Get all laws
    all_laws = get_all_bundesgesetze()

    if not all_laws:
        print("Could not fetch law list. Using priority laws only.")
        all_laws = [(abbr, abbr.upper()) for abbr in PRIORITY_LAWS]

    # Sort: priority laws first, then alphabetically
    priority_set = set(PRIORITY_LAWS)
    all_laws_sorted = sorted(
        all_laws,
        key=lambda x: (0 if x[0].lower() in [p.lower() for p in priority_set] else 1, x[0])
    )

    print(f"Processing {len(all_laws_sorted)} laws...")
    print()

    # Download with progress
    downloaded_count = 0
    failed_priority = []

    for i, (abbrev, title) in enumerate(all_laws_sorted):
        abbr, status, extra = download_bundesgesetz(abbrev, title, BUNDESGESETZE_DIR)
        stats[status] += 1

        symbol = {"downloaded": "✓", "skipped": "○", "failed": "·"}[status]

        # Progress display
        if status == "downloaded":
            downloaded_count += 1
            print(f"  {symbol} [{i+1}/{len(all_laws_sorted)}] {extra}")
        elif status == "failed" and abbrev.lower() in [p.lower() for p in priority_set]:
            failed_priority.append(abbrev)

        # Rate limiting
        if status == "downloaded":
            time.sleep(0.15)

        # Progress indicator every 100 laws
        if (i + 1) % 500 == 0:
            print(f"  ... processed {i+1}/{len(all_laws_sorted)} laws ...")

    # Report failed priority laws
    if failed_priority:
        print()
        print(f"  ⚠ {len(failed_priority)} priority laws failed: {', '.join(failed_priority[:10])}")

    # ==================== SUMMARY ====================
    print()
    print("=" * 70)
    print("Summary")
    print("=" * 70)
    print(f"  Downloaded: {stats['downloaded']}")
    print(f"  Skipped:    {stats['skipped']} (already exist)")
    print(f"  Failed:     {stats['failed']}")
    print()

    # Count files
    bundesgesetze_count = len(list(BUNDESGESETZE_DIR.glob("*.pdf")))
    eu_count = len(list(EU_GESETZE_DIR.glob("*.pdf")))
    total_size_mb = sum(f.stat().st_size for f in LEGAL_DOCS_DIR.rglob("*.pdf")) / (1024 * 1024)

    print(f"Total PDFs: {bundesgesetze_count + eu_count}")
    print(f"  - Bundesgesetze: {bundesgesetze_count}")
    print(f"  - EU-Recht: {eu_count}")
    print(f"Total Size: {total_size_mb:.1f} MB")
    print()
    print("Documents saved to:")
    print(f"  {LEGAL_DOCS_DIR}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
