#!/usr/bin/env python3
"""Fetch merged pull requests by the author and group them by company.

Standard library only. Reads GITHUB_TOKEN from the environment (optional
but strongly recommended: the unauthenticated search API is heavily rate
limited). Writes scripts/merged.json next to this file.

    GITHUB_TOKEN="$(gh auth token)" python3 scripts/fetch_merged.py

Only repositories whose OWNER is in the explicit allowlist below are kept.
Everything else (personal repos, class repos, friends' hackathon repos) is
dropped, so the skyline only ever shows company open source work.
"""
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

AUTHOR = "Om-singhaI"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "merged.json")

# owner (GitHub org) -> company. Matching is case-insensitive.
COMPANIES = {
    "microsoft": "Microsoft", "Azure": "Microsoft", "MicrosoftDocs": "Microsoft",
    "facebook": "Meta", "pytorch": "Meta", "meta-llama": "Meta",
    "apple": "Apple",
    "cloudflare": "Cloudflare",
    "aws": "AWS", "awslabs": "AWS", "aws-samples": "AWS",
    "google": "Google", "googleapis": "Google", "GoogleCloudPlatform": "Google",
    "firebase": "Google", "google-gemini": "Google",
    "NVIDIA": "NVIDIA",
    "huggingface": "Hugging Face",
    "vercel": "Vercel",
    "teslamotors": "Tesla",
    "NASA-AMMOS": "NASA", "nasa": "NASA",
    "openai": "OpenAI",
    "anthropics": "Anthropic",
}
OWNER_TO_COMPANY = {k.lower(): v for k, v in COMPANIES.items()}

API = "https://api.github.com/search/issues"
PER_PAGE = 100


def get(url, token):
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": f"{AUTHOR}-skyline",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    for attempt in range(4):
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            # secondary rate limit or transient server error: back off and retry
            if e.code in (403, 429, 500, 502, 503) and attempt < 3:
                time.sleep(5 * (attempt + 1))
                continue
            raise
        except urllib.error.URLError:
            if attempt < 3:
                time.sleep(5 * (attempt + 1))
                continue
            raise


def fetch_all(token):
    q = f"is:pr is:merged author:{AUTHOR}"
    items, page = [], 1
    while True:
        url = API + "?" + urllib.parse.urlencode(
            {"q": q, "per_page": PER_PAGE, "page": page,
             "sort": "created", "order": "asc"})
        data = get(url, token)
        batch = data.get("items", [])
        items.extend(batch)
        if data.get("incomplete_results"):
            print("warning: GitHub reported incomplete search results", file=sys.stderr)
        # the search API stops at 1000 results
        if len(batch) < PER_PAGE or len(items) >= min(data.get("total_count", 0), 1000):
            break
        page += 1
    return items


def main():
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    items = fetch_all(token)

    counts = {}      # (company, owner/repo) -> count
    first = None
    dropped = {}
    seen = set()
    for it in items:
        if it.get("html_url") in seen:
            continue
        seen.add(it.get("html_url"))
        # repository_url: https://api.github.com/repos/OWNER/REPO
        owner, repo = it["repository_url"].rstrip("/").split("/")[-2:]
        company = OWNER_TO_COMPANY.get(owner.lower())
        if company is None:
            dropped[f"{owner}/{repo}"] = dropped.get(f"{owner}/{repo}", 0) + 1
            continue
        key = (company, f"{owner}/{repo}")
        counts[key] = counts.get(key, 0) + 1
        merged_at = (it.get("pull_request") or {}).get("merged_at") or it.get("closed_at")
        if merged_at and (first is None or merged_at < first):
            first = merged_at

    companies = {}
    for (company, full), n in counts.items():
        companies.setdefault(company, []).append(
            {"repo": full, "name": full.split("/", 1)[1], "count": n})
    out = []
    for company, repos in companies.items():
        repos.sort(key=lambda r: (-r["count"], r["name"].lower()))
        out.append({"company": company,
                    "total": sum(r["count"] for r in repos),
                    "repos": repos})
    out.sort(key=lambda c: (-c["total"], c["company"].lower()))

    doc = {
        "author": AUTHOR,
        # date of the earliest merged PR that counts; stable unless history changes
        "since": first[:10] if first else None,
        "companies": out,
    }
    text = json.dumps(doc, indent=2, ensure_ascii=False) + "\n"
    old = None
    if os.path.exists(OUT):
        with open(OUT, encoding="utf-8") as f:
            old = f.read()
    if text != old:
        with open(OUT, "w", encoding="utf-8") as f:
            f.write(text)
    for c in out:
        print(f"{c['company']:<14}{c['total']:>4}  "
              + ", ".join(f"{r['name']} {r['count']}" for r in c["repos"]))
    if dropped:
        print(f"dropped (owner not in allowlist): {len(dropped)} repos, "
              f"{sum(dropped.values())} PRs")
    print("wrote" if text != old else "unchanged", OUT)


if __name__ == "__main__":
    main()
