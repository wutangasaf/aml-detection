#!/usr/bin/env python3
"""
AML/CFT Regulatory Documents Bulk Downloader
Handles direct PDFs and attempts to extract PDF links from HTML pages.
"""

import requests
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

# --- Configuration ---
BASE_DIR = "/Users/asaferez/Projects/aml/documents/"
MAX_WORKERS = 5
TIMEOUT = 60

# Browser-like headers to avoid blocks
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,application/pdf,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Connection': 'keep-alive',
}

# --- Document List with WORKING Direct PDF URLs ---
# Priority: Direct PDF links that are confirmed to work
DOCUMENTS = [
    # ============ FATF - Using mirrors and direct links ============
    # FATF 40 Recommendations (FIU Trinidad mirror - WORKS)
    {"url": "https://fiu.gov.tt/wp-content/uploads/New-FATF-40-Recommendations.pdf",
     "folder": "fatf", "filename": "FATF-40-Recommendations.pdf", "direct": True},

    # FATF Financial Inclusion (World Bank mirror - WORKS)
    {"url": "https://documents1.worldbank.org/curated/en/099232208072496412/pdf/IDU-4d9b71e9-06f1-4fca-ab5a-8d63e43f85bd.pdf",
     "folder": "fatf", "filename": "FATF-Financial-Inclusion-Guidance.pdf", "direct": True},

    # FATF Methodology (Japan MOFA mirror)
    {"url": "https://www.mofa.go.jp/policy/i_crime/recommend.pdf",
     "folder": "fatf", "filename": "FATF-Original-40-Recommendations.pdf", "direct": True},

    # ============ BASEL / BIS - Direct PDFs (WORK) ============
    {"url": "https://www.bis.org/bcbs/publ/d353.pdf",
     "folder": "basel", "filename": "Basel-ML-TF-Risk-Management.pdf", "direct": True},

    {"url": "https://www.bis.org/bcbs/publ/d528.pdf",
     "folder": "basel", "filename": "Basel-CDD-Banks.pdf", "direct": True},

    # Basel AML Index 2024
    {"url": "https://index.baselgovernance.org/api/assets/0789b440-8537-45b4-8bfd-e44ac456c15d.pdf",
     "folder": "basel", "filename": "Basel-AML-Index-2024.pdf", "direct": True},

    # ============ EU LEGISLATION - EUR-Lex PDFs ============
    {"url": "https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=CELEX:32024R1624",
     "folder": "eu", "filename": "EU-AMLR-2024-1624-Single-Rulebook.pdf", "direct": True},

    {"url": "https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=CELEX:32024R1640",
     "folder": "eu", "filename": "EU-AMLD6-2024-1640.pdf", "direct": True},

    {"url": "https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=CELEX:32024R1620",
     "folder": "eu", "filename": "EU-AMLA-Regulation-2024-1620.pdf", "direct": True},

    {"url": "https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=CELEX:32023R1113",
     "folder": "eu", "filename": "EU-Transfer-Funds-2023-1113.pdf", "direct": True},

    {"url": "https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=CELEX:32018L0843",
     "folder": "eu", "filename": "EU-AMLD5-2018-843.pdf", "direct": True},

    {"url": "https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=CELEX:32024R0163",
     "folder": "eu", "filename": "EU-High-Risk-Countries-2024.pdf", "direct": True},

    # ============ EBA GUIDELINES ============
    {"url": "https://www.eba.europa.eu/sites/default/files/2025-10/0e56a26c-b379-4820-81ef-c02d9a5e37b5/Report%20on%20the%20functioning%20of%20AMLCFT%20colleges%20in%202024%20and%202025.pdf",
     "folder": "eba", "filename": "EBA-AMLCFT-Colleges-2024-2025.pdf", "direct": True},

    # ============ WOLFSBERG GROUP ============
    {"url": "https://iib.int/attachments/wolfsberg_cbddq_v1_4_0_apr_2024_1.pdf",
     "folder": "wolfsberg", "filename": "Wolfsberg-CBDDQ-2024.pdf", "direct": True},

    # ============ JMLSG (UK) ============
    {"url": "https://www.jmlsg.org.uk/wp-content/uploads/2025/09/JMLSG-Guidance-Part-I_June-2023-updated-Aug-2025.pdf",
     "folder": "jmlsg", "filename": "JMLSG-Part-I.pdf", "direct": True},

    {"url": "https://www.jmlsg.org.uk/wp-content/uploads/2025/09/JMLSG-Guidance-Part-II_June-2023_revised-Sept-2024-1.pdf",
     "folder": "jmlsg", "filename": "JMLSG-Part-II.pdf", "direct": True},

    {"url": "https://www.jmlsg.org.uk/wp-content/uploads/2025/09/JMLSG-Guidance_Part-III_Aug-2025-note.pdf",
     "folder": "jmlsg", "filename": "JMLSG-Part-III.pdf", "direct": True},

    # ============ FATF PAGES - Need PDF extraction ============
    # These are HTML pages - script will try to find PDF links
    {"url": "https://www.fatf-gafi.org/en/publications/Fatfrecommendations/Fatf-recommendations.html",
     "folder": "fatf", "filename": "FATF-Recommendations-Latest.pdf", "direct": False},

    {"url": "https://www.fatf-gafi.org/en/publications/Fatfrecommendations/Risk-based-approach-banking-sector.html",
     "folder": "fatf", "filename": "FATF-RBA-Banking.pdf", "direct": False},

    {"url": "https://www.fatf-gafi.org/en/publications/Fatfrecommendations/Guidance-rba-virtual-assets-2021.html",
     "folder": "fatf", "filename": "FATF-RBA-Virtual-Assets.pdf", "direct": False},

    {"url": "https://www.fatf-gafi.org/en/publications/Fatfrecommendations/Guidance-beneficial-ownership-legal-persons.html",
     "folder": "fatf", "filename": "FATF-Beneficial-Ownership.pdf", "direct": False},

    {"url": "https://www.fatf-gafi.org/en/publications/Fatfrecommendations/Correspondent-banking-services.html",
     "folder": "fatf", "filename": "FATF-Correspondent-Banking.pdf", "direct": False},

    {"url": "https://www.fatf-gafi.org/en/publications/Fatfrecommendations/Peps-r12-r22.html",
     "folder": "fatf", "filename": "FATF-PEPs-Guidance.pdf", "direct": False},

    # FATF TYPOLOGIES
    {"url": "https://www.fatf-gafi.org/en/publications/Methodsandtrends/Trade-basedmoneylaundering.html",
     "folder": "fatf/typologies", "filename": "FATF-TBML.pdf", "direct": False},

    {"url": "https://www.fatf-gafi.org/en/publications/Methodsandtrends/Professional-money-laundering.html",
     "folder": "fatf/typologies", "filename": "FATF-Professional-ML.pdf", "direct": False},

    {"url": "https://www.fatf-gafi.org/en/publications/Methodsandtrends/Virtual-assets-red-flag-indicators.html",
     "folder": "fatf/typologies", "filename": "FATF-VA-Red-Flags.pdf", "direct": False},

    {"url": "https://www.fatf-gafi.org/en/publications/Methodsandtrends/Concealment-beneficial-ownership.html",
     "folder": "fatf/typologies", "filename": "FATF-Concealment-BO.pdf", "direct": False},

    # ============ US SOURCES ============
    {"url": "https://www.occ.gov/news-issuances/news-releases/2024/nr-ia-2024-82b.pdf",
     "folder": "us", "filename": "OCC-AML-2024.pdf", "direct": True},
]


def extract_pdf_links_from_page(html_content, base_url):
    """Try to find PDF download links in an HTML page."""
    soup = BeautifulSoup(html_content, 'html.parser')
    pdf_links = []

    # Common patterns for PDF links
    patterns = [
        # Direct PDF links
        re.compile(r'href=["\']([^"\']*\.pdf)["\']', re.IGNORECASE),
        # FATF content dam pattern
        re.compile(r'href=["\']([^"\']*content/dam[^"\']*\.pdf)["\']', re.IGNORECASE),
        # Download buttons/links
        re.compile(r'href=["\']([^"\']*download[^"\']*\.pdf)["\']', re.IGNORECASE),
    ]

    # Find all links
    for link in soup.find_all('a', href=True):
        href = link['href']
        if '.pdf' in href.lower():
            full_url = urljoin(base_url, href)
            pdf_links.append(full_url)

    # Also search in raw HTML for hidden links
    for pattern in patterns:
        matches = pattern.findall(html_content)
        for match in matches:
            full_url = urljoin(base_url, match)
            if full_url not in pdf_links:
                pdf_links.append(full_url)

    return list(set(pdf_links))


def download_document(doc_info):
    """Download a single document."""
    url = doc_info["url"]
    folder = doc_info["folder"]
    filename = doc_info["filename"]
    is_direct = doc_info.get("direct", True)

    full_path = os.path.join(BASE_DIR, folder, filename)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)

    # Skip if already exists and is a valid PDF
    if os.path.exists(full_path):
        size = os.path.getsize(full_path)
        if size > 10000:  # More than 10KB, likely valid
            return f"SKIP: {filename} already exists ({size:,} bytes)"

    session = requests.Session()
    session.headers.update(HEADERS)

    try:
        response = session.get(url, timeout=TIMEOUT, allow_redirects=True)
        response.raise_for_status()

        content_type = response.headers.get('Content-Type', '').lower()

        # Direct PDF download
        if 'application/pdf' in content_type or response.content[:4] == b'%PDF':
            with open(full_path, 'wb') as f:
                f.write(response.content)
            size = len(response.content)
            return f"OK: {filename} ({size:,} bytes)"

        # HTML page - try to extract PDF link
        elif 'text/html' in content_type:
            if is_direct:
                # Expected PDF but got HTML - blocked
                return f"BLOCKED: {filename} - got HTML instead of PDF"

            # Try to find PDF link in the page
            pdf_links = extract_pdf_links_from_page(response.text, url)

            if pdf_links:
                # Try first PDF link found
                for pdf_url in pdf_links[:3]:  # Try up to 3 links
                    try:
                        pdf_response = session.get(pdf_url, timeout=TIMEOUT)
                        if pdf_response.content[:4] == b'%PDF':
                            with open(full_path, 'wb') as f:
                                f.write(pdf_response.content)
                            size = len(pdf_response.content)
                            return f"OK: {filename} (extracted from page, {size:,} bytes)"
                    except:
                        continue

                # Save found links for manual download
                links_file = full_path.replace('.pdf', '_links.txt')
                with open(links_file, 'w') as f:
                    f.write(f"Source: {url}\n\nPDF links found:\n")
                    for link in pdf_links:
                        f.write(f"  {link}\n")
                return f"MANUAL: {filename} - found {len(pdf_links)} PDF links, saved to {os.path.basename(links_file)}"
            else:
                return f"NO_PDF: {filename} - no PDF links found on page"

        else:
            return f"UNKNOWN: {filename} - content type: {content_type}"

    except requests.exceptions.Timeout:
        return f"TIMEOUT: {filename}"
    except requests.exceptions.RequestException as e:
        return f"ERROR: {filename} - {str(e)[:50]}"


def main():
    """Run bulk download."""
    print("=" * 70)
    print("AML/CFT REGULATORY DOCUMENTS BULK DOWNLOADER")
    print("=" * 70)
    print(f"Base directory: {BASE_DIR}")
    print(f"Documents to process: {len(DOCUMENTS)}")
    print(f"Parallel workers: {MAX_WORKERS}")
    print("=" * 70)
    print()

    # Categorize results
    results = {"OK": [], "SKIP": [], "BLOCKED": [], "MANUAL": [], "ERROR": []}

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(download_document, doc): doc for doc in DOCUMENTS}

        for future in as_completed(futures):
            result = future.result()
            print(result)

            # Categorize
            for key in results.keys():
                if result.startswith(key):
                    results[key].append(result)
                    break

            time.sleep(0.5)  # Be nice to servers

    # Summary
    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"  Downloaded:     {len(results['OK'])}")
    print(f"  Already exists: {len(results['SKIP'])}")
    print(f"  Blocked/HTML:   {len(results['BLOCKED'])}")
    print(f"  Manual needed:  {len(results['MANUAL'])}")
    print(f"  Errors:         {len(results['ERROR'])}")
    print("=" * 70)

    # List documents needing manual download
    if results['BLOCKED'] or results['MANUAL'] or results['ERROR']:
        print()
        print("DOCUMENTS REQUIRING MANUAL DOWNLOAD:")
        print("-" * 70)
        for r in results['BLOCKED'] + results['MANUAL'] + results['ERROR']:
            print(f"  {r}")


if __name__ == "__main__":
    # Check for required library
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        print("Installing BeautifulSoup...")
        os.system("pip install beautifulsoup4")
        from bs4 import BeautifulSoup

    main()
