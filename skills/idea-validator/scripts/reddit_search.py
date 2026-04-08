#!/usr/bin/env python3
"""Search Reddit for pain-point evidence related to a product idea.

Uses Reddit's public JSON endpoints (no API key required).
Returns structured JSON with post counts, engagement metrics, and frustration signals.

Matching strategy: frustration phrases are tiered by specificity. High-specificity
phrases (explicit tool-seeking) qualify on their own. Low-specificity phrases (generic
questions) require a domain keyword to co-occur in the same post. Posts where the
frustration phrase appears in the title get a reduced upvote threshold (2x weight).
"""

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

FRUSTRATION_HIGH = [
    "wish there was",
    "looking for a tool",
    "why is there no",
    "there has to be a better way",
    "sick of",
    "hate having to",
    "so frustrated",
    "tired of",
]

FRUSTRATION_MEDIUM = [
    "any alternatives",
    "can someone recommend",
    "recommendations for",
    "i need a tool",
    "is it just me",
    "am i the only one",
    "looking for a way to",
    "help me find",
]

FRUSTRATION_LOW = [
    "does anyone know",
    "how do you",
    "what do you use for",
    "is there anything",
    "looking for",
]

ALL_FRUSTRATION = FRUSTRATION_HIGH + FRUSTRATION_MEDIUM + FRUSTRATION_LOW

MIN_UPVOTES = 20
TITLE_UPVOTE_MULTIPLIER = 0.5
MAX_AGE_MONTHS = 24
USER_AGENT = "IdeaValidator/0.2 (research; no app)"
REQUEST_DELAY = 2


def search_subreddit(subreddit, keyword, limit=25):
    params = urllib.parse.urlencode(
        {
            "q": keyword,
            "sort": "relevance",
            "restrict_sr": "on",
            "limit": limit,
            "t": "year",
        }
    )
    url = f"https://www.reddit.com/r/{subreddit}/search.json?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 429:
            time.sleep(REQUEST_DELAY * 3)
            try:
                with urllib.request.urlopen(req, timeout=15) as resp:
                    return json.loads(resp.read().decode("utf-8"))
            except Exception:
                return {"data": {"children": []}}
        return {"data": {"children": []}}
    except Exception:
        return {"data": {"children": []}}


def post_age_months(created_utc):
    now = time.time()
    return (now - created_utc) / (86400 * 30)


def find_frustration_signals(title, selftext, domain_keywords):
    title_lower = title.lower()
    body_lower = f"{title} {selftext}".lower()
    domain_match = any(kw in body_lower for kw in domain_keywords)

    best_tier = None
    phrase_found = None
    in_title = False

    for phrase in FRUSTRATION_HIGH:
        if phrase in body_lower:
            best_tier = "high"
            phrase_found = phrase
            in_title = phrase in title_lower
            break

    if best_tier is None:
        for phrase in FRUSTRATION_MEDIUM:
            if phrase in body_lower:
                best_tier = "medium"
                phrase_found = phrase
                in_title = phrase in title_lower
                break

    if best_tier is None:
        for phrase in FRUSTRATION_LOW:
            if phrase in body_lower:
                best_tier = "low"
                phrase_found = phrase
                in_title = phrase in title_lower
                break

    if best_tier is None:
        return None

    if best_tier == "high":
        qualifies = True
    elif best_tier == "medium":
        qualifies = True
    elif best_tier == "low":
        qualifies = domain_match

    if not qualifies:
        return None

    return {
        "tier": best_tier,
        "phrase": phrase_found,
        "in_title": in_title,
        "domain_keyword_present": domain_match,
    }


def effective_upvote_threshold(signal):
    if signal and signal["in_title"]:
        return MIN_UPVOTES * TITLE_UPVOTE_MULTIPLIER
    return MIN_UPVOTES


def process_posts(raw_children, domain_keywords):
    qualifying = []
    total_seen = 0
    for child in raw_children:
        data = child.get("data", {})
        if data.get("stickied"):
            continue
        total_seen += 1
        title = data.get("title", "")
        selftext = data.get("selftext", "") or ""
        ups = data.get("ups", 0) or data.get("score", 0)
        created = data.get("created_utc", 0)
        url = f"https://reddit.com{data.get('permalink', '')}"
        age = post_age_months(created)

        signal = find_frustration_signals(title, selftext, domain_keywords)
        if signal is None:
            continue

        threshold = effective_upvote_threshold(signal)
        if ups >= threshold and age <= MAX_AGE_MONTHS:
            qualifying.append(
                {
                    "title": title,
                    "upvotes": ups,
                    "url": url,
                    "age_months": round(age, 1),
                    "subreddit": data.get("subreddit", ""),
                    "snippet": selftext[:200] if selftext else title,
                    "match_tier": signal["tier"],
                    "matched_phrase": signal["phrase"],
                    "in_title": signal["in_title"],
                    "domain_keyword_present": signal["domain_keyword_present"],
                }
            )
    return qualifying, total_seen


def search_all(keywords, subreddits):
    domain_keywords = [kw.strip().lower() for kw in keywords if len(kw.strip()) > 2]
    all_qualifying = []
    subreddit_stats = {}
    total_posts_scanned = 0

    for subreddit in subreddits:
        subreddit = subreddit.strip()
        if not subreddit:
            continue
        sub_qualifying = []
        sub_scanned = 0
        for keyword in keywords:
            keyword = keyword.strip()
            if not keyword:
                continue
            time.sleep(REQUEST_DELAY)
            result = search_subreddit(subreddit, keyword)
            children = result.get("data", {}).get("children", [])
            qualifying, scanned = process_posts(children, domain_keywords)
            sub_qualifying.extend(qualifying)
            sub_scanned += scanned

        if sub_qualifying:
            subreddit_stats[subreddit] = {
                "qualifying_posts": len(sub_qualifying),
                "posts_scanned": sub_scanned,
                "avg_upvotes": round(
                    sum(p["upvotes"] for p in sub_qualifying) / len(sub_qualifying), 1
                ),
            }
            all_qualifying.extend(sub_qualifying)
        total_posts_scanned += sub_scanned

    all_qualifying.sort(key=lambda p: p["upvotes"], reverse=True)
    seen_urls = set()
    deduped = []
    for post in all_qualifying:
        if post["url"] not in seen_urls:
            seen_urls.add(post["url"])
            deduped.append(post)

    tier_counts = {"high": 0, "medium": 0, "low": 0}
    for post in deduped:
        tier_counts[post["match_tier"]] += 1

    recency_buckets = {"0-3": 0, "3-6": 0, "6-12": 0, "12-24": 0}
    for post in deduped:
        m = post["age_months"]
        if m <= 3:
            recency_buckets["0-3"] += 1
        elif m <= 6:
            recency_buckets["3-6"] += 1
        elif m <= 12:
            recency_buckets["6-12"] += 1
        else:
            recency_buckets["12-24"] += 1

    return {
        "total_qualifying_posts": len(deduped),
        "total_posts_scanned": total_posts_scanned,
        "subreddits_searched": len([s for s in subreddits if s.strip()]),
        "subreddits_with_results": list(subreddit_stats.keys()),
        "subreddit_breakdown": subreddit_stats,
        "match_tier_distribution": tier_counts,
        "recency_distribution": recency_buckets,
        "avg_upvotes": round(sum(p["upvotes"] for p in deduped) / len(deduped), 1)
        if deduped
        else 0,
        "top_posts": deduped[:10],
        "methodology": {
            "frustration_phrases_high": FRUSTRATION_HIGH,
            "frustration_phrases_medium": FRUSTRATION_MEDIUM,
            "frustration_phrases_low": FRUSTRATION_LOW,
            "min_upvotes_threshold": MIN_UPVOTES,
            "title_upvote_discount": f"{TITLE_UPVOTE_MULTIPLIER}x threshold when phrase in title",
            "low_tier_requires_domain_keyword": True,
            "domain_keywords_used": domain_keywords,
            "max_age_months": MAX_AGE_MONTHS,
        },
    }


def main():
    parser = argparse.ArgumentParser(description="Search Reddit for pain-point signals")
    parser.add_argument(
        "--keywords", required=True, help="Comma-separated keywords to search"
    )
    parser.add_argument(
        "--subreddits", required=True, help="Comma-separated subreddits to search"
    )
    args = parser.parse_args()

    keywords = [k.strip() for k in args.keywords.split(",")]
    subreddits = [s.strip() for s in args.subreddits.split(",")]

    if not keywords or not subreddits:
        print(
            json.dumps(
                {
                    "error": "Both --keywords and --subreddits are required",
                    "results": None,
                }
            )
        )
        sys.exit(1)

    print(
        json.dumps(
            {"error": None, "results": search_all(keywords, subreddits)}, indent=2
        )
    )


if __name__ == "__main__":
    main()
