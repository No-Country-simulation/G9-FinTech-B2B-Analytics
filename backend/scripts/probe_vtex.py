"""VTEX store probing for the spike.

Usage: uv run python -m scripts.probe_vtex https://www.jumbo.com.ar https://www.carrefour.com.ar
"""

import asyncio
import sys
import time
from itertools import combinations

import httpx

TERMS = ["milk", "yerba mate", "oil", "rice", "pasta", "refrigerator", "tv"]
LOAD_REQUESTS = 30  # requests for the load test, at 1 per second
HEADERS = {"User-Agent": "PriceScopeBot/0.1 (NoCountry academic project)"}


def search_url(base: str, term: str, to_index: int = 49) -> str:
    return f"{base}/api/catalog_system/pub/products/search?ft={term}&_from=0&_to={to_index}"


def summarize(product: dict) -> dict:
    item = product["items"][0]
    seller = item["sellers"][0]
    offer = seller["commertialOffer"]
    return {
        "name": product.get("productName"),
        "ean": item.get("ean"),
        "price": offer.get("Price"),
        "list_price": offer.get("ListPrice"),
        "stock": offer.get("AvailableQuantity"),
        "seller": seller.get("sellerName"),
        "unit": item.get("measurementUnit"),
        "category": (product.get("categories") or [None])[0],
    }


async def probe(client: httpx.AsyncClient, base: str) -> set[str]:
    print(f"\n=== {base} ===")

    r = await client.get(f"{base}/robots.txt")
    print(f"robots.txt: HTTP {r.status_code}")
    keywords = ("user-agent", "crawl-delay", "api", "catalog", "sitemap")
    lines = [x for x in r.text.splitlines() if any(k in x.lower() for k in keywords)]
    for x in lines[:15]:
        print("    ", x)

    eans: set[str] = set()
    ratios: list[float] = []
    for term in TERMS:
        r = await client.get(search_url(base, term))
        if r.status_code not in (200, 206):
            print(f"[{term}] HTTP {r.status_code}")
            continue
        try:
            products = r.json()
        except ValueError:
            print(f"[{term}] did not return JSON (not VTEX or blocked?)")
            continue
        for p in products:
            try:
                d = summarize(p)
            except (KeyError, IndexError):
                continue
            if d["ean"]:
                eans.add(d["ean"])
            if d["price"] and d["list_price"] and d["list_price"] > d["price"]:
                ratios.append(d["list_price"] / d["price"])
        if products:
            print(f"[{term}] {len(products)} products. Example: {summarize(products[0])}")
        await asyncio.sleep(1)

    if ratios:
        ratios.sort()
        n = len(ratios)
        print(
            f"Products with list > price: {n}. List/price ratio -> "
            f"median {ratios[n // 2]:.2f}, p90 {ratios[int(n * 0.9)]:.2f}, max {ratios[-1]:.1f}"
        )

    statuses: dict[int, int] = {}
    start = time.perf_counter()
    for _ in range(LOAD_REQUESTS):
        r = await client.get(search_url(base, "milk", 9))
        statuses[r.status_code] = statuses.get(r.status_code, 0) + 1
        await asyncio.sleep(1)
    print(f"Load {LOAD_REQUESTS} req at 1/s: {statuses} ({time.perf_counter() - start:.0f} s)")
    print(f"Distinct EANs obtained: {len(eans)}")
    return eans


async def main(bases: list[str]) -> None:
    async with httpx.AsyncClient(headers=HEADERS, timeout=15, follow_redirects=True) as client:
        eans = {base: await probe(client, base) for base in bases}
    print("\n=== EAN Overlap ===")
    for a, b in combinations(bases, 2):
        print(f"{a} vs {b}: {len(eans[a] & eans[b])} EANs in common")


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:]))
