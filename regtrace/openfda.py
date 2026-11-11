"""Pulls 510(k) clearances from the public openFDA API, one page at a time."""
import time
import requests

BASE = "https://api.fda.gov/device/510k.json"
PAGE = 1000          # openFDA max per request
MAX_SKIP = 25000     # openFDA refuses skip beyond this


def fetch_510k(product_code: str, api_key: str | None = None, session=None, sleep=0.25):
    """Yield raw 510(k) records for one FDA product code (e.g. 'DQY')."""
    s = session or requests.Session()
    skip = 0
    while skip <= MAX_SKIP:
        params = {"search": f'product_code:"{product_code}"', "limit": PAGE, "skip": skip}
        if api_key:
            params["api_key"] = api_key
        r = s.get(BASE, params=params, timeout=30)
        if r.status_code == 404:  # openFDA returns 404 when nothing (more) matches
            return
        r.raise_for_status()
        results = r.json().get("results", [])
        yield from results
        if len(results) < PAGE:
            return
        skip += PAGE
        time.sleep(sleep)
