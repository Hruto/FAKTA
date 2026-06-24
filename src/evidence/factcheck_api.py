"""
FAKTA - Google Fact Check Tools API Integration
Free tier API for searching verified fact-checks.
"""

import os
import logging
import requests
from typing import List, Dict, Optional
from pathlib import Path

# Load .env file
try:
    from dotenv import load_dotenv
    _env_path = Path(__file__).parent.parent.parent / ".env"
    load_dotenv(dotenv_path=_env_path)
except ImportError:
    pass

logger = logging.getLogger(__name__)


class GoogleFactCheckAPI:
    """
    Google Fact Check Tools API client.
    Free tier available at https://developers.google.com/fact-check/tools/api
    """

    API_URL = "https://factchecktools.googleapis.com/v1alpha1/claims:search"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("GOOGLE_FACTCHECK_API_KEY")

    def search(self, query: str, language: str = "id", page_size: int = 5) -> List[Dict]:
        """
        Search for fact-checks matching the query.

        Args:
            query: Claim text or keywords
            language: Language code (id for Indonesian)
            page_size: Max results

        Returns:
            List of fact-check results
        """
        if not self.api_key:
            print("[FactCheckAPI] No API key set, skipping")
            return []

        params = {
            "query": query,
            "languageCode": language,
            "key": self.api_key,
            "pageSize": page_size,
        }

        try:
            response = requests.get(self.API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            results = []
            for claim in data.get("claims", [])[:page_size]:
                for review in claim.get("claimReview", []):
                    results.append({
                        "source": review.get("publisher", {}).get("name", "Unknown"),
                        "title": claim.get("text", "")[:200],
                        "text": review.get("textualRating", ""),
                        "url": review.get("url", ""),
                        "date": review.get("reviewDate", ""),
                        "rating": review.get("textualRating", ""),
                        "source_tier": 1,
                        "provider": "google_factcheck",
                        "relevance_score": 0.7,  # Google returns relevant results
                        "source_credibility": 1.0,
                        "recency_score": self._compute_recency(review.get("reviewDate", "")),
                    })

            return results

        except requests.exceptions.RequestException as e:
            print(f"[FactCheckAPI] Request error: {e}")
            return []
        except Exception as e:
            print(f"[FactCheckAPI] Error: {e}")
            return []

    def _compute_recency(self, date_str: str) -> float:
        """Compute recency score from ISO date string."""
        from datetime import datetime, timezone

        if not date_str:
            return 0.5

        try:
            # Normalize common date formats
            cleaned = date_str.strip()
            # Handle ISO 8601 with Z suffix
            if cleaned.endswith("Z"):
                cleaned = cleaned[:-1] + "+00:00"
            # Handle bare date like "2024-01-15"
            if len(cleaned) == 10 and cleaned[4] == "-" and cleaned[7] == "-":
                cleaned += "T00:00:00+00:00"

            date = datetime.fromisoformat(cleaned)
            # Ensure timezone-aware comparison
            if date.tzinfo is None:
                date = date.replace(tzinfo=timezone.utc)
            days_ago = (datetime.now(timezone.utc) - date).days

            if days_ago <= 30:
                return 1.0
            elif days_ago <= 365:
                return max(0.3, 1.0 - (days_ago / 365) * 0.7)
            else:
                return max(0.1, 0.3 - (days_ago - 365) / 1000)
        except (ValueError, TypeError, OSError):
            return 0.5


if __name__ == "__main__":
    api = GoogleFactCheckAPI()
    results = api.search("matcha gagal ginjal")
    print(f"Found {len(results)} fact-checks")
    for r in results:
        print(f"  [{r['source']}] {r['text'][:80]}...")
