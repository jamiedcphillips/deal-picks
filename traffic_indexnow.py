#!/usr/bin/env python3
"""
Tokenless organic-traffic driver for the deal-picks affiliate site.
- Submits all sitemap URLs to IndexNow (Bing + Yandex) -> gets pages crawled/indexed fast, no account.
- Pings search-engine sitemap endpoints.
Run standalone or from cron. Prints a one-line result (silent-friendly).
"""
import re, os, json, sys, time, urllib.request, urllib.parse, urllib.error

DEPLOY = os.path.dirname(os.path.abspath(__file__))
BASE = "https://jamiedcphillips.github.io/deal-picks/"
HOST = "jamiedcphillips.github.io"
KEY_FILE = os.path.join(DEPLOY, "indexnow_key.txt")

def log(msg):
    print(f"[traffic] {msg}")

def get_key():
    with open(KEY_FILE) as f:
        return f.read().strip()

def get_urls():
    sm = os.path.join(DEPLOY, "sitemap.xml")
    with open(sm, encoding="utf-8") as f:
        return re.findall(r"<loc>([^<]+)</loc>", f.read())

def post_json(url, payload):
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data,
        headers={"Content-Type": "application/json; charset=utf-8"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read(200).decode(errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read(200).decode(errors="replace")
    except Exception as e:
        return 0, str(e)

def get_ping(url):
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception as e:
        return f"err:{e}"

def main():
    key = get_key()
    urls = get_urls()
    if not urls:
        log("no urls in sitemap; abort"); return 1

    payload = {
        "host": HOST,
        "key": key,
        "keyLocation": f"{BASE}{key}.txt",
        "urlList": urls,
    }
    results = {}
    # IndexNow official endpoint (fans out to Bing, Yandex, Seznam, etc.)
    for endpoint in ["https://api.indexnow.org/indexnow",
                     "https://www.bing.com/indexnow"]:
        code, body = post_json(endpoint, payload)
        results[endpoint] = code
        time.sleep(1)

    # Sitemap pings
    sm = urllib.parse.quote(f"{BASE}sitemap.xml", safe="")
    results["bing_sitemap_ping"] = get_ping(f"https://www.bing.com/ping?sitemap={sm}")

    ok = any(str(v).startswith("2") for k, v in results.items() if "indexnow" in k)
    log(f"submitted {len(urls)} urls | {json.dumps(results)} | {'OK' if ok else 'CHECK'}")
    return 0 if ok else 2

if __name__ == "__main__":
    sys.exit(main())
