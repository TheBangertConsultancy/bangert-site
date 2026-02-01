#!/usr/bin/env python3
"""
=============================================================================
THE BANGERT CONSULTANCY - Tourism News Feed Agent v2
=============================================================================

Scrapes tourism and travel industry news from RSS feeds, classifies articles
by geographic scope (Romania, European, Global), and outputs a balanced
JSON feed: roughly 1/3 Romania, 1/3 European, 1/3 Global.

HOW TO USE:
-----------
1. Install dependencies:
   pip install feedparser requests beautifulsoup4

2. Run manually:
   python news_agent.py

3. Automate with GitHub Actions (free) or cron job.
   See IMPLEMENTATION_GUIDE.md for full setup instructions.

OUTPUT:
-------
- news_feed.json : Array of news articles for the website

=============================================================================
"""

import json
import os
import sys
import re
import hashlib
from datetime import datetime, timedelta
from pathlib import Path

# ---- Dependencies ----
try:
    import feedparser
except ImportError:
    os.system(f"{sys.executable} -m pip install feedparser --quiet")
    import feedparser

try:
    import requests
except ImportError:
    os.system(f"{sys.executable} -m pip install requests --quiet")
    import requests

try:
    from bs4 import BeautifulSoup
except ImportError:
    os.system(f"{sys.executable} -m pip install beautifulsoup4 --quiet")
    from bs4 import BeautifulSoup


# =============================================================================
# CONFIGURATION
# =============================================================================

OUTPUT_FILE = Path("news_feed.json")
BACKUP_FILE = Path("news_feed_backup.json")

# Total articles in the final feed
TOTAL_ARTICLES = 9

# Geographic balance: how many from each bucket
SLOTS_ROMANIA = 3   # 1/3
SLOTS_EUROPE = 3    # 1/3
SLOTS_GLOBAL = 3    # 1/3

# If a bucket doesn't have enough articles, overflow goes to the others
# (e.g., if only 1 Romania article found, the extra 2 slots go to Europe/Global)

MAX_AGE_DAYS = 14
TIMEOUT = 15
USER_AGENT = "TheBangertConsultancy-NewsAgent/2.0"


# =============================================================================
# RSS FEEDS - organised by geographic focus
# =============================================================================

FEEDS_ROMANIA = [
    {
        "url": "https://www.romania-insider.com/feed",
        "source": "Romania Insider",
        "geo": "romania",
    },
    {
        "url": "https://www.romaniajournal.ro/feed/",
        "source": "Romania Journal",
        "geo": "romania",
    },
    {
        "url": "https://www.actmedia.eu/rss/rss.php",
        "source": "ACTMedia Romania",
        "geo": "romania",
    },
    {
        "url": "https://www.nineoclock.ro/feed/",
        "source": "Nine O'Clock",
        "geo": "romania",
    },
]

FEEDS_EUROPE = [
    {
        "url": "https://www.traveldailynews.com/feed/",
        "source": "Travel Daily News",
        "geo": "europe",
    },
    {
        "url": "https://www.eturbonews.com/feed/",
        "source": "eTurboNews",
        "geo": "global",  # mixed, will be reclassified by content
    },
    {
        "url": "https://www.hospitalitynet.org/rss/news.html",
        "source": "Hospitality Net",
        "geo": "europe",
    },
    {
        "url": "https://www.euronews.com/travel/feed",
        "source": "Euronews Travel",
        "geo": "europe",
    },
    {
        "url": "https://www.touristboard.net/feed/",
        "source": "Tourist Board News",
        "geo": "europe",
    },
    {
        "url": "https://etc-corporate.org/feed/",
        "source": "European Travel Commission",
        "geo": "europe",
    },
]

FEEDS_GLOBAL = [
    {
        "url": "https://skift.com/feed/",
        "source": "Skift",
        "geo": "global",
    },
    {
        "url": "https://www.phocuswire.com/rss",
        "source": "PhocusWire",
        "geo": "global",
    },
    {
        "url": "https://www.travelweekly.com/rss",
        "source": "Travel Weekly",
        "geo": "global",
    },
    {
        "url": "https://www.travelandtourworld.com/feed/",
        "source": "Travel & Tour World",
        "geo": "global",
    },
    {
        "url": "https://www.ttgmedia.com/rss",
        "source": "TTG Media",
        "geo": "global",
    },
    {
        "url": "https://www.travelmarketreport.com/rss",
        "source": "Travel Market Report",
        "geo": "global",
    },
    {
        "url": "https://www.breakingtravelnews.com/feed/",
        "source": "Breaking Travel News",
        "geo": "global",
    },
]

ALL_FEEDS = FEEDS_ROMANIA + FEEDS_EUROPE + FEEDS_GLOBAL


# =============================================================================
# GEOGRAPHIC CLASSIFICATION KEYWORDS
# =============================================================================

# Used to reclassify articles into the correct geographic bucket
# regardless of which feed they came from.

GEO_ROMANIA_KEYWORDS = [
    "romania", "romanian", "bucharest", "bucuresti",
    "transylvania", "moldova", "moldavia",
    "constanta", "mamaia", "brasov", "sibiu", "cluj",
    "timisoara", "iasi", "maramures", "banat", "dobrogea",
    "black sea coast", "danube delta", "tulcea", "prahova",
    "bran", "sinaia", "poiana brasov", "vama veche",
    "bucovina", "painted monasteries",
]

GEO_EUROPE_KEYWORDS = [
    "europe", "european", "eu ", " eu,", "eu's",
    "mediterranean", "balkans", "balkan",
    "spain", "spanish", "france", "french", "italy", "italian",
    "greece", "greek", "portugal", "portuguese",
    "germany", "german", "austria", "austrian", "switzerland", "swiss",
    "croatia", "croatian", "slovenia", "slovenia",
    "bulgaria", "bulgarian", "serbia", "serbian", "hungary", "hungarian",
    "turkey", "turkish", "czech", "prague", "poland", "polish",
    "netherlands", "dutch", "belgium", "belgian",
    "uk ", "britain", "british", "london", "scotland", "ireland",
    "scandinavia", "nordic", "norway", "sweden", "denmark", "finland",
    "barcelona", "paris", "rome", "lisbon", "berlin", "vienna",
    "amsterdam", "dubrovnik", "santorini", "alps",
    "schengen", "eurozone", "ryanair", "easyjet", "eurowings",
    # EU policy terms
    "european commission", "european parliament", "eu tourism",
    "eu fund", "erasmus", "horizon europe",
]

# If an article matches neither Romania nor Europe keywords, it's Global.


# =============================================================================
# RELEVANCE KEYWORDS (for scoring within each bucket)
# =============================================================================

KEYWORDS_HIGH_VALUE = [
    "destination marketing", "dmo", "destination management",
    "tourism strategy", "tourism board", "national tourism",
    "wine tourism", "sustainable tourism", "slow travel",
    "overtourism", "tourist tax", "tourism tax",
    "review management", "tripadvisor", "ota management",
    "travel tech", "digital campaign", "programmatic",
    "feeder market", "source market",
    "hotel marketing", "hospitality marketing",
    "mice tourism", "conference tourism",
    "cultural tourism", "heritage tourism", "rural tourism",
    "ai tourism", "artificial intelligence travel",
    "tourism investment", "tourism infrastructure",
    "eco tourism", "responsible tourism",
    "culinary tourism", "food tourism", "gastro tourism",
]

KEYWORDS_MEDIUM_VALUE = [
    "tourism", "travel industry", "hospitality",
    "hotel", "resort", "accommodation",
    "destination", "visitor economy", "inbound tourism",
    "outbound tourism", "travel trend", "booking",
    "airline", "cruise", "tour operator",
    "travel recovery", "tourism growth", "visitor numbers",
    "travel technology", "digital transformation",
    "influencer", "content marketing", "social media travel",
]


# =============================================================================
# CORE FUNCTIONS
# =============================================================================

def fetch_feed(feed_config):
    """Fetch and parse a single RSS feed."""
    articles = []
    try:
        headers = {"User-Agent": USER_AGENT}
        resp = requests.get(feed_config["url"], headers=headers, timeout=TIMEOUT)
        feed = feedparser.parse(resp.content)
        for entry in feed.entries[:25]:
            article = parse_entry(entry, feed_config)
            if article:
                articles.append(article)
    except Exception as e:
        print(f"  [WARN] {feed_config['source']}: {e}")
    return articles


def parse_entry(entry, feed_config):
    """Parse a single RSS feed entry into a structured article dict."""
    try:
        title = clean_text(entry.get("title", ""))
        if not title or len(title) < 15:
            return None

        url = entry.get("link", "")
        if not url:
            return None

        summary_raw = entry.get("summary", entry.get("description", ""))
        summary = clean_html(summary_raw)
        if len(summary) > 220:
            summary = summary[:217].rsplit(" ", 1)[0] + "..."
        if not summary:
            summary = title

        date_obj = None
        date_str = ""
        for field in ("published_parsed", "updated_parsed"):
            parsed = getattr(entry, field, None)
            if parsed:
                try:
                    date_obj = datetime(*parsed[:6])
                    date_str = date_obj.strftime("%B %d, %Y")
                    break
                except Exception:
                    pass

        # Skip old articles
        if date_obj and (datetime.now() - date_obj).days > MAX_AGE_DAYS:
            return None

        return {
            "id": hashlib.md5(url.encode()).hexdigest()[:12],
            "title": title,
            "summary": summary,
            "url": url,
            "source": feed_config["source"],
            "feed_geo": feed_config["geo"],  # Feed-level hint
            "geo": "",                        # Will be classified
            "date": date_str,
            "date_obj": date_obj.isoformat() if date_obj else "",
            "score": 0,
        }
    except Exception:
        return None


def clean_text(text):
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\[\.{3}\]$", "", text).strip()
    return text


def clean_html(html):
    try:
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "iframe"]):
            tag.decompose()
        text = soup.get_text(separator=" ")
        return re.sub(r"\s+", " ", text).strip()
    except Exception:
        return clean_text(html)


def classify_geography(article):
    """
    Classify each article as 'romania', 'europe', or 'global'
    based on its content, overriding the feed-level hint when needed.
    """
    text = (article["title"] + " " + article["summary"]).lower()

    # Check Romania first (most specific)
    romania_hits = sum(1 for kw in GEO_ROMANIA_KEYWORDS if kw in text)
    if romania_hits >= 1:
        article["geo"] = "romania"
        return article

    # Check Europe
    europe_hits = sum(1 for kw in GEO_EUROPE_KEYWORDS if kw in text)
    if europe_hits >= 1:
        article["geo"] = "europe"
        return article

    # Fall back to feed-level hint
    if article["feed_geo"] == "romania":
        article["geo"] = "romania"
    elif article["feed_geo"] == "europe":
        article["geo"] = "europe"
    else:
        article["geo"] = "global"

    return article


def score_article(article):
    """
    Score article by relevance to Bangert Consultancy's audience.
    This determines ranking WITHIN each geographic bucket.
    """
    score = 0
    text = (article["title"] + " " + article["summary"]).lower()

    for kw in KEYWORDS_HIGH_VALUE:
        if kw in text:
            score += 4

    for kw in KEYWORDS_MEDIUM_VALUE:
        if kw in text:
            score += 1

    # Recency bonus
    if article.get("date_obj"):
        try:
            age = (datetime.now() - datetime.fromisoformat(article["date_obj"])).days
            if age <= 1:
                score += 6
            elif age <= 3:
                score += 4
            elif age <= 7:
                score += 2
        except Exception:
            pass

    # Penalty for clickbait
    for cb in ["you won't believe", "shocking", "amazing trick", "top 10 hack"]:
        if cb in text:
            score -= 5

    article["score"] = max(score, 0)
    return article


def deduplicate(articles):
    """Remove articles with near-identical titles."""
    seen = set()
    unique = []
    for a in articles:
        key = re.sub(r"[^a-z0-9]", "", a["title"].lower())[:50]
        if key not in seen:
            seen.add(key)
            unique.append(a)
    return unique


def balanced_selection(articles):
    """
    Select articles with geographic balance:
    SLOTS_ROMANIA from Romania, SLOTS_EUROPE from Europe, SLOTS_GLOBAL from Global.
    
    If any bucket is short, overflow slots go to the other buckets
    (prioritising Europe first, then Global).
    """
    # Split into buckets
    romania = [a for a in articles if a["geo"] == "romania"]
    europe = [a for a in articles if a["geo"] == "europe"]
    global_ = [a for a in articles if a["geo"] == "global"]

    # Sort each bucket by score descending
    romania.sort(key=lambda x: x["score"], reverse=True)
    europe.sort(key=lambda x: x["score"], reverse=True)
    global_.sort(key=lambda x: x["score"], reverse=True)

    print(f"\n  Bucket sizes: Romania={len(romania)}, Europe={len(europe)}, Global={len(global_)}")

    # Pick from each bucket
    picked_ro = romania[:SLOTS_ROMANIA]
    picked_eu = europe[:SLOTS_EUROPE]
    picked_gl = global_[:SLOTS_GLOBAL]

    # Handle overflow: if a bucket is short, distribute extra slots
    total_picked = len(picked_ro) + len(picked_eu) + len(picked_gl)
    remaining_needed = TOTAL_ARTICLES - total_picked

    if remaining_needed > 0:
        # Collect unused articles from all buckets, sorted by score
        used_ids = {a["id"] for a in picked_ro + picked_eu + picked_gl}
        overflow_pool = [a for a in articles if a["id"] not in used_ids]
        overflow_pool.sort(key=lambda x: x["score"], reverse=True)

        # Fill remaining slots from overflow, trying to keep balance
        # Prefer Europe overflow first, then Global
        eu_overflow = [a for a in overflow_pool if a["geo"] == "europe"]
        gl_overflow = [a for a in overflow_pool if a["geo"] == "global"]
        ro_overflow = [a for a in overflow_pool if a["geo"] == "romania"]

        overflow_ordered = eu_overflow + gl_overflow + ro_overflow
        extra = overflow_ordered[:remaining_needed]
        picked_eu.extend([a for a in extra if a["geo"] == "europe"])
        picked_gl.extend([a for a in extra if a["geo"] == "global"])
        picked_ro.extend([a for a in extra if a["geo"] == "romania"])

    # Combine and interleave: Romania, Europe, Global, Romania, Europe, Global...
    # This makes the visual layout feel balanced rather than clustered by region.
    final = []
    max_len = max(len(picked_ro), len(picked_eu), len(picked_gl))
    for i in range(max_len):
        if i < len(picked_ro):
            final.append(picked_ro[i])
        if i < len(picked_eu):
            final.append(picked_eu[i])
        if i < len(picked_gl):
            final.append(picked_gl[i])

    return final[:TOTAL_ARTICLES]


def format_output(articles):
    """Clean up articles for JSON output."""
    output = []
    for a in articles:
        # Map geo label to a readable display category
        geo_labels = {
            "romania": "Romania",
            "europe": "European Tourism",
            "global": "Global Travel",
        }
        output.append({
            "title": a["title"],
            "summary": a["summary"],
            "url": a["url"],
            "source": a["source"],
            "category": geo_labels.get(a["geo"], "Travel News"),
            "date": a["date"],
        })
    return output


# =============================================================================
# MAIN
# =============================================================================

def generate_feed():
    print("=" * 60)
    print("THE BANGERT CONSULTANCY - News Feed Agent v2")
    print(f"Target mix: {SLOTS_ROMANIA} Romania / {SLOTS_EUROPE} Europe / {SLOTS_GLOBAL} Global")
    print(f"Run time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    all_articles = []

    for feed in ALL_FEEDS:
        print(f"  Fetching: {feed['source']}...")
        articles = fetch_feed(feed)
        all_articles.extend(articles)
        print(f"    -> {len(articles)} articles")

    print(f"\n  Total raw: {len(all_articles)}")

    # Classify geography
    all_articles = [classify_geography(a) for a in all_articles]

    # Score relevance
    all_articles = [score_article(a) for a in all_articles]

    # Deduplicate
    all_articles = deduplicate(all_articles)
    print(f"  After dedup: {len(all_articles)}")

    # Balanced selection
    selected = balanced_selection(all_articles)

    # Format for output
    output = format_output(selected)

    # Backup previous file
    if OUTPUT_FILE.exists():
        try:
            OUTPUT_FILE.rename(BACKUP_FILE)
        except Exception:
            pass

    # Write
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    # Report
    geo_counts = {}
    for a in selected:
        geo_counts[a["geo"]] = geo_counts.get(a["geo"], 0) + 1

    print(f"\n  Final feed: {len(output)} articles")
    print(f"  Balance: Romania={geo_counts.get('romania',0)}, "
          f"Europe={geo_counts.get('europe',0)}, "
          f"Global={geo_counts.get('global',0)}")
    print(f"\n  Articles:")
    for i, a in enumerate(output, 1):
        print(f"    {i}. [{a['category']}] [{a['source']}] {a['title'][:65]}...")

    print(f"\n  Written to: {OUTPUT_FILE}")
    print("  Done.")
    return output


if __name__ == "__main__":
    generate_feed()
