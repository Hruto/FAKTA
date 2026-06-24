"""
FAKTA - Data Collection Pipeline
Scrapes and normalizes Indonesian hoax/non-hoax datasets for LSTM training.

Sources:
- TurnBackHoax (MAFINDO)
- CekFakta (Tempo)
- ISHOX (Kaggle)
- Kominfo Hoax Bulletins
"""

import os
import re
import time
import json
import hashlib
import requests
from typing import List, Dict, Optional
from pathlib import Path
from datetime import datetime

import pandas as pd
from bs4 import BeautifulSoup


# ============================================================
# TurnBackHoax Scraper
# ============================================================

class TurnBackHoaxScraper:
    """
    Scrapes TurnBackHoax.id for hoax fact-check articles using their API.
    Much faster than HTML scraping.
    """

    API_URL = "https://turnbackhoax.id/api/articles"
    RATE_LIMIT = 0.5  # seconds between requests

    def __init__(self, output_dir: str = "data/raw/turnbackhoax"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._last_request = 0

    def _wait(self):
        """Enforce rate limiting."""
        elapsed = time.time() - self._last_request
        if elapsed < self.RATE_LIMIT:
            time.sleep(self.RATE_LIMIT - elapsed)
        self._last_request = time.time()

    def fetch_page(self, page: int = 1, limit: int = 100) -> List[Dict]:
        """Fetch a single page from the API."""
        self._wait()
        try:
            response = requests.get(
                self.API_URL,
                params={"page": page, "limit": limit},
                timeout=15,
                headers={"User-Agent": "FAKTA Academic Research Bot"},
                verify=False,
            )
            if response.status_code != 200:
                return []
            data = response.json()
            if not data.get("success"):
                return []
            return data.get("data", [])
        except Exception as e:
            print(f"[TurnBackHoax] Error fetching page {page}: {e}")
            return []

    def scrape(self, max_pages: int = 150, limit_per_page: int = 10) -> List[Dict]:
        """
        Scrape articles from the API.

        Args:
            max_pages: Maximum number of pages to fetch
            limit_per_page: Items per page (API default is 10)

        Returns:
            List of article dicts with title, description, content, conclusion
        """
        all_articles = []

        for page in range(1, max_pages + 1):
            print(f"Fetching page {page}/{max_pages}...", end=" ", flush=True)
            articles = self.fetch_page(page, limit_per_page)

            if not articles:
                print("No more articles.")
                break

            all_articles.extend(articles)
            print(f"Got {len(articles)} articles (total: {len(all_articles)})")

            # Stop if we got fewer than limit (last page)
            if len(articles) < limit_per_page:
                break

        # Save raw
        output_path = self.output_dir / "raw_articles.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(all_articles, f, ensure_ascii=False, indent=2)

        print(f"\nTotal articles collected: {len(all_articles)}")
        print(f"Saved to {output_path}")

        return all_articles


# ============================================================
# CekFakta Scraper
# ============================================================

class CekFaktaScraper:
    """
    Scrapes cekfakta.com (Tempo) for fact-check articles.
    """

    BASE_URL = "https://cekfakta.com"
    RATE_LIMIT = 2.0

    def __init__(self, output_dir: str = "data/raw/cekfakta"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._last_request = 0

    def _wait(self):
        elapsed = time.time() - self._last_request
        if elapsed < self.RATE_LIMIT:
            time.sleep(self.RATE_LIMIT - elapsed)
        self._last_request = time.time()

    def scrape(self, max_pages: int = 30) -> List[Dict]:
        """Scrape cekfakta articles."""
        # Placeholder implementation
        # cekfakta.com structure may vary
        print("[CekFakta] Scraper ready. Implement based on current site structure.")
        return []


# ============================================================
# Dataset Normalization
# ============================================================

import re

def strip_html(html: str) -> str:
    """Remove HTML tags from text."""
    if not html:
        return ""
    return re.sub(r"<[^>]+>", "", html).strip()


def normalize_turnbackhoax(raw_articles: List[Dict]) -> pd.DataFrame:
    """
    Normalize TurnBackHoax API data to training format.

    Output columns: text, claim, label, source, date, url
    """
    records = []

    for article in raw_articles:
        # Build full text from description + conclusion (debunk info)
        description = strip_html(article.get("description", ""))
        conclusion = strip_html(article.get("conclusion", ""))
        content = strip_html(article.get("content", ""))
        title = article.get("title", "")

        # Combine into training text
        text = f"{title}\n{description}\n{conclusion}".strip()

        # All TurnBackHoax articles are debunked hoaks
        label = "hoax"

        records.append({
            "text": text,
            "claim": title,
            "label": label,
            "source": "TurnBackHoax",
            "date": article.get("created_at", "")[:10] if article.get("created_at") else "",
            "url": f"https://turnbackhoax.id/articles/{article.get('slug', '')}",
            "category": article.get("category", ""),
        })

    df = pd.DataFrame(records)
    df = df.drop_duplicates(subset=["claim"])
    df = df.dropna(subset=["text"])
    df = df[df["text"].str.len() > 20]

    return df


def normalize_ishox(csv_path: str) -> pd.DataFrame:
    """
    Normalize ISHOX dataset from Kaggle.
    Expected format varies by version.
    """
    df = pd.read_csv(csv_path)

    # Map common column names
    if "text" not in df.columns:
        for col in ["tweet", "content", "article"]:
            if col in df.columns:
                df = df.rename(columns={col: "text"})
                break

    if "label" not in df.columns:
        for col in ["hoax", "class", "is_hoax"]:
            if col in df.columns:
                df = df.rename(columns={col: "label"})
                break

    if "text" in df.columns and "label" in df.columns:
        df["label"] = df["label"].astype(str).str.lower()
        df["label"] = df["label"].map({
            "hoax": "hoax", "true": "valid", "false": "hoax",
            "1": "hoax", "0": "valid", "hoaks": "hoax",
            "valid": "valid", "tidak hoax": "valid",
        }).fillna(df["label"])

        df["source"] = "ISHOX"
        return df[["text", "label", "source"]]

    return pd.DataFrame()


def combine_datasets(datasets: List[pd.DataFrame], output_path: str = "data/training/combined.csv"):
    """
    Combine multiple datasets and split into train/val/test.

    Args:
        datasets: List of normalized DataFrames
        output_path: Output path for combined CSV
    """
    from sklearn.model_selection import train_test_split

    combined = pd.concat(datasets, ignore_index=True)

    # Deduplicate
    combined = combined.drop_duplicates(subset=["text"])

    # Remove rows with empty text or unknown labels
    combined = combined.dropna(subset=["text", "label"])
    combined = combined[combined["label"].isin(["hoax", "valid", "uncertain"])]

    print(f"Combined dataset: {len(combined)} samples")
    print(f"Label distribution:\n{combined['label'].value_counts()}")

    # Save
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    combined.to_csv(output_path, index=False, encoding="utf-8")
    print(f"Saved to {output_path}")

    return combined


# ============================================================
# Main
# ============================================================

def main():
    """Run full data collection pipeline."""
    print("=" * 60)
    print("FAKTA Data Collection Pipeline")
    print("=" * 60)

    # Step 1: Scrape TurnBackHoax
    print("\n[1/3] Scraping TurnBackHoax...")
    tbh_scraper = TurnBackHoaxScraper()
    tbh_articles = tbh_scraper.scrape(max_pages=100)

    # Step 2: Normalize
    print("\n[2/3] Normalizing datasets...")
    tbh_df = normalize_turnbackhoax(tbh_articles)

    # Step 3: Combine
    print("\n[3/3] Combining datasets...")
    datasets = [tbh_df]
    combined = combine_datasets(datasets)

    print(f"\nDone! Total: {len(combined)} samples")


if __name__ == "__main__":
    main()
