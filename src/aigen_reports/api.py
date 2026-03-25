"""TikTok Marketing API client (Reporting category only).

This module is intentionally minimal: only what the CLI needs to pull a
report. No write endpoints, no caching layer, no abstraction over
metric names. If you need more, fork the repo.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Iterable

import requests

API_BASE = "https://business-api.tiktok.com/open_api/v1.3"


@dataclass
class ReportRequest:
    advertiser_id: str
    metrics: list[str]
    dimensions: list[str]
    start_date: str  # YYYY-MM-DD
    end_date: str  # YYYY-MM-DD


def fetch_report(token: str, req: ReportRequest) -> list[dict]:
    """Call /report/integrated/get/ and return the rows.

    Raises ``RuntimeError`` if TikTok returns a non-zero ``code``. The
    error body is included verbatim so the caller can surface it.
    """

    params = {
        "advertiser_id": req.advertiser_id,
        "report_type": "BASIC",
        "data_level": _data_level(req.dimensions),
        "dimensions": json.dumps(req.dimensions),
        "metrics": json.dumps(req.metrics),
        "start_date": req.start_date,
        "end_date": req.end_date,
        "page_size": 1000,
    }
    headers = {"Access-Token": token}

    rows: list[dict] = []
    page = 1
    while True:
        params["page"] = page
        resp = requests.get(f"{API_BASE}/report/integrated/get/", params=params, headers=headers, timeout=30)
        body = resp.json()
        if body.get("code") != 0:
            raise RuntimeError(f"TikTok API error: {body}")
        data = body.get("data", {})
        rows.extend(data.get("list", []))
        page_info = data.get("page_info", {})
        if page >= page_info.get("total_page", 1):
            break
        page += 1
    return rows


def _data_level(dimensions: Iterable[str]) -> str:
    if "ad_id" in dimensions:
        return "AUCTION_AD"
    if "adgroup_id" in dimensions:
        return "AUCTION_ADGROUP"
    return "AUCTION_CAMPAIGN"
