#!/usr/bin/env python3
"""Scan the web for competitors related to a product idea.

Supports multiple search providers: Brave Search, Tavily, and DuckDuckGo.
Tries all available providers and merges results. Surfaces per-provider
errors (rate limits, missing keys) so the scorecard can note gaps.

Environment variables:
  BRAVE_API_KEY   - Optional. Brave Search API key (free tier: $5/month credit)
  TAVILY_API_KEY  - Optional. Tavily API key (free tier: 1000 searches/month)
  DuckDuckGo      - No API key required. Always available as fallback.
"""

import argparse
import json
import os
import sys
import gzip
import urllib.error
import urllib.parse
import urllib.request

MAX_RESULTS = 10

COMPETITOR_INDICATORS = [
    "pricing",
    "sign up",
    "get started",
    "features",
    "plans",
    "download",
    "install",
    "try free",
    "start trial",
]

DEAD_PROJECT_INDICATORS = [
    "page not found",
    "site no longer",
    "has been discontinued",
    "no longer available",
    "service retired",
    "shut down",
    "this project is no longer",
    "domain for sale",
]

DOMAIN_BLACKLIST = [
    "wikipedia.org",
    "youtube.com",
    "reddit.com",
    "twitter.com",
    "x.com",
    "linkedin.com",
    "medium.com",
    "substack.com",
]


def extract_competitor_signals(title, description, url):
    combined = f"{title} {description}".lower()

    pricing = "unknown"
    if any(p in combined for p in ["free tier", "free plan", "free forever"]):
        pricing = "free"
    elif any(
        p in combined for p in ["freemium", "free trial", "start free", "try free"]
    ):
        pricing = "freemium"
    elif any(
        p in combined
        for p in ["pricing", "paid", "subscription", "plans", "$", "per month"]
    ):
        pricing = "paid"

    audience = "general"
    if any(a in combined for a in ["enterprise", "b2b", "business", "team", "company"]):
        audience = "business"
    elif any(
        a in combined
        for a in ["freelancer", "solo", "personal", "individual", "consumer"]
    ):
        audience = "consumer"
    elif any(a in combined for a in ["developer", "api", "open source", "github"]):
        audience = "developer"

    maturity = "emerging"
    if any(
        m in combined
        for m in ["established", "trusted by", "thousands", "millions", "users"]
    ):
        maturity = "established"
    elif any(
        m in combined
        for m in ["mature", "industry standard", "leading", "most popular"]
    ):
        maturity = "mature"

    return {
        "pricing_inferred": pricing,
        "audience_inferred": audience,
        "maturity_inferred": maturity,
    }


def categorize_result(title, description, url):
    combined = f"{title} {description}".lower()

    if any(indicator in combined for indicator in DEAD_PROJECT_INDICATORS):
        return "dead_project"

    parsed = urllib.parse.urlparse(url)
    if any(domain in parsed.netloc for domain in DOMAIN_BLACKLIST):
        return "informational"

    has_product_signals = any(ind in combined for ind in COMPETITOR_INDICATORS)
    has_competitor_language = any(
        word in combined
        for word in [
            "platform",
            "tool",
            "app",
            "software",
            "service",
            "solution",
            "product",
            "saas",
            "automate",
            "manage",
        ]
    )

    if has_product_signals or has_competitor_language:
        return "direct_competitor"

    if "alternativ" in combined or "compare" in combined or "review" in combined:
        return "adjacent_tool"

    return "informational"


def classify_query_type(query):
    query_lower = query.lower()
    if any(
        w in query_lower
        for w in ["alternative", "instead of", "vs", "competitor", "similar to", "like"]
    ):
        return "comparison"
    if any(w in query_lower for w in ["best", "top", "recommend", "review"]):
        return "review"
    return "general"


def normalize_result(raw):
    return {
        "title": raw.get("title", ""),
        "url": raw.get("url", ""),
        "description": (raw.get("description", "") or "")[:200],
    }


def search_brave(query):
    api_key = os.environ.get("BRAVE_API_KEY")
    if not api_key:
        return {
            "provider": "brave",
            "status": "skipped",
            "error": "BRAVE_API_KEY not set",
            "results": [],
        }

    params = urllib.parse.urlencode(
        {"q": query, "count": MAX_RESULTS, "search_lang": "en"}
    )
    url = f"https://api.search.brave.com/res/v1/web/search?{params}"
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": api_key,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw_data = resp.read()
            if resp.headers.get("Content-Encoding") == "gzip":
                raw_data = gzip.decompress(raw_data)
            data = json.loads(raw_data.decode("utf-8"))
        web_results = data.get("web", {}).get("results", [])
        return {
            "provider": "brave",
            "status": "ok",
            "error": None,
            "results": [normalize_result(r) for r in web_results],
        }
    except urllib.error.HTTPError as e:
        return {
            "provider": "brave",
            "status": "error",
            "error": f"HTTP {e.code}: {e.reason}",
            "results": [],
        }
    except Exception as e:
        return {
            "provider": "brave",
            "status": "error",
            "error": str(e),
            "results": [],
        }


def search_tavily(query):
    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key:
        return {
            "provider": "tavily",
            "status": "skipped",
            "error": "TAVILY_API_KEY not set",
            "results": [],
        }

    payload = json.dumps({"query": query, "max_results": MAX_RESULTS}).encode("utf-8")
    req = urllib.request.Request(
        "https://api.tavily.com/search",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        raw_results = data.get("results", [])
        normalized = []
        for r in raw_results:
            normalized.append(
                {
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "description": (r.get("content", "") or "")[:200],
                }
            )
        return {
            "provider": "tavily",
            "status": "ok",
            "error": None,
            "results": normalized,
        }
    except urllib.error.HTTPError as e:
        return {
            "provider": "tavily",
            "status": "error",
            "error": f"HTTP {e.code}: {e.reason}",
            "results": [],
        }
    except Exception as e:
        return {
            "provider": "tavily",
            "status": "error",
            "error": str(e),
            "results": [],
        }


def search_duckduckgo(query):
    try:
        from ddgs import DDGS
    except ImportError:
        return {
            "provider": "duckduckgo",
            "status": "error",
            "error": "ddgs not installed. Run: uv add ddgs",
            "results": [],
        }

    try:
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=MAX_RESULTS):
                results.append(
                    {
                        "title": r.get("title", ""),
                        "url": r.get("href", ""),
                        "description": (r.get("body", "") or "")[:200],
                    }
                )
        return {
            "provider": "duckduckgo",
            "status": "ok",
            "error": None,
            "results": results,
        }
    except Exception as e:
        err_str = str(e).lower()
        if "ratelimit" in err_str or "429" in err_str:
            return {
                "provider": "duckduckgo",
                "status": "error",
                "error": f"Rate limited: {e}",
                "results": [],
            }
        return {
            "provider": "duckduckgo",
            "status": "error",
            "error": str(e),
            "results": [],
        }


def merge_results(provider_responses):
    seen_urls = set()
    merged = []
    for response in provider_responses:
        for r in response["results"]:
            if r["url"] and r["url"] not in seen_urls:
                seen_urls.add(r["url"])
                merged.append(r)
    return merged


def analyze(query):
    provider_responses = [
        search_brave(query),
        search_tavily(query),
        search_duckduckgo(query),
    ]

    successful_providers = [r for r in provider_responses if r["status"] == "ok"]
    failed_providers = [
        {"provider": r["provider"], "status": r["status"], "error": r["error"]}
        for r in provider_responses
        if r["status"] != "ok"
    ]

    if not successful_providers:
        return {
            "error": "All search providers failed",
            "provider_status": failed_providers,
            "results": None,
        }

    merged = merge_results(successful_providers)

    categorized = {
        "direct_competitor": [],
        "adjacent_tool": [],
        "informational": [],
        "dead_project": [],
    }

    for r in merged:
        category = categorize_result(r["title"], r["description"], r["url"])
        entry = {**r, "category": category}
        if category in ("direct_competitor", "adjacent_tool"):
            signals = extract_competitor_signals(r["title"], r["description"], r["url"])
            entry.update(signals)
        categorized[category].append(entry)

    return {
        "error": None,
        "provider_status": [
            {"provider": r["provider"], "status": r["status"], "error": r["error"]}
            for r in provider_responses
        ],
        "results": {
            "query": query,
            "query_type": classify_query_type(query),
            "total_results": len(merged),
            "categorized": categorized,
            "competitor_count": len(categorized["direct_competitor"]),
            "adjacent_count": len(categorized["adjacent_tool"]),
            "informational_count": len(categorized["informational"]),
            "dead_count": len(categorized["dead_project"]),
            "top_competitors": [
                {
                    "title": c["title"],
                    "url": c["url"],
                    "description": c.get("description", ""),
                    "pricing_inferred": c.get("pricing_inferred", "unknown"),
                    "audience_inferred": c.get("audience_inferred", "general"),
                    "maturity_inferred": c.get("maturity_inferred", "emerging"),
                }
                for c in categorized["direct_competitor"][:5]
            ],
        },
    }


def main():
    parser = argparse.ArgumentParser(description="Scan the web for competitors")
    parser.add_argument(
        "--query", required=True, help="Search query describing the product space"
    )
    args = parser.parse_args()

    result = analyze(args.query)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
