"""Command-line interface for AiGen Reports."""

from __future__ import annotations

import csv
import json
import os
from datetime import date, timedelta
from pathlib import Path

import click
import requests

from .api import ReportRequest, fetch_report

DEFAULT_METRICS = ["spend", "clicks", "impressions", "conversions"]
CREDENTIALS_PATH = Path.home() / ".aigen-reports" / "credentials.json"


def _resolve_range(spec: str) -> tuple[str, str]:
    if spec.startswith("last-") and spec.endswith("d"):
        n = int(spec[len("last-") : -1])
        end = date.today()
        start = end - timedelta(days=n - 1)
        return start.isoformat(), end.isoformat()
    raise click.BadParameter(f"unsupported range: {spec}; use last-Nd")


def _load_credentials() -> dict:
    """Load credentials from ~/.aigen-reports/credentials.json if it exists."""
    if CREDENTIALS_PATH.exists():
        with CREDENTIALS_PATH.open("r") as fh:
            return json.load(fh)
    return {}


def _save_credentials(creds: dict) -> None:
    """Save credentials back to ~/.aigen-reports/credentials.json."""
    CREDENTIALS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CREDENTIALS_PATH.open("w") as fh:
        json.dump(creds, fh, indent=2)


def _refresh_token(creds: dict) -> str | None:
    """Attempt to refresh the access token using the refresh_token.

    Returns the new access token if successful, None otherwise.
    Updates credentials.json on success.
    """
    refresh_token = creds.get("refresh_token")
    app_id = creds.get("app_id")
    app_secret = os.environ.get("TIKTOK_APP_SECRET")

    if not refresh_token or not app_id or not app_secret:
        return None

    resp = requests.post(
        "https://business-api.tiktok.com/open_api/v1.3/tt_user/oauth2/refresh_token/",
        json={
            "app_id": app_id,
            "secret": app_secret,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        },
        timeout=30,
    )
    body = resp.json()
    if body.get("code") != 0:
        return None

    data = body.get("data", {})
    new_token = data.get("access_token")
    new_refresh = data.get("refresh_token", refresh_token)
    if new_token:
        creds["access_token"] = new_token
        creds["refresh_token"] = new_refresh
        _save_credentials(creds)
    return new_token


def _resolve_token() -> str:
    """Resolve the TikTok access token from env var or credentials file.

    Attempts token refresh if the credentials file has a refresh_token.
    """
    # 1. Explicit env var wins
    token = os.environ.get("TIKTOK_ACCESS_TOKEN")
    if token:
        return token

    # 2. Try credentials file
    creds = _load_credentials()
    token = creds.get("access_token")
    if token:
        # Optional: could check expiration here. For now, try refresh if available.
        if creds.get("refresh_token"):
            refreshed = _refresh_token(creds)
            if refreshed:
                return refreshed
        return token

    raise click.ClickException(
        "TikTok access token not found. "
        "Set TIKTOK_ACCESS_TOKEN env var or run `aigen-reports auth`."
    )


@click.group()
def main() -> None:
    """AiGen Reports — read-only TikTok Ads reporting utility."""


@main.command()
def auth() -> None:
    """Run the OAuth flow and save the access token."""
    click.echo("OAuth flow stub: see README for the manual exchange.")


@main.command()
@click.option("--advertiser", required=True, help="TikTok advertiser id")
@click.option(
    "--metric",
    default=",".join(DEFAULT_METRICS),
    help="Comma-separated metric list",
)
@click.option(
    "--breakdown",
    type=click.Choice(["campaign", "adgroup", "ad"], case_sensitive=False),
    default="campaign",
)
@click.option("--range", "range_spec", default="last-7d")
@click.option("--out", "out_path", required=True)
def pull(advertiser: str, metric: str, breakdown: str, range_spec: str, out_path: str) -> None:
    """Pull a report and write it to --out."""
    token = _resolve_token()

    dim_map = {
        "campaign": ["campaign_id", "stat_time_day"],
        "adgroup": ["adgroup_id", "stat_time_day"],
        "ad": ["ad_id", "stat_time_day"],
    }
    metrics = [m.strip() for m in metric.split(",") if m.strip()]
    dimensions = dim_map[breakdown.lower()]

    start, end = _resolve_range(range_spec)
    rows = fetch_report(
        token,
        ReportRequest(
            advertiser_id=advertiser,
            metrics=metrics,
            dimensions=dimensions,
            start_date=start,
            end_date=end,
        ),
    )

    if out_path.endswith(".csv"):
        _write_csv(rows, Path(out_path), dimensions, metrics)
    else:
        raise click.ClickException("only CSV output is wired in this skeleton; gsheet/webhook coming")

    click.echo(f"\u2713 wrote {len(rows)} rows \u2192 {out_path}")


def _write_csv(rows: list[dict], path: Path, dimensions: list[str], metrics: list[str]) -> None:
    fieldnames = dimensions + metrics
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            flat = {**row.get("dimensions", {}), **row.get("metrics", {})}
            writer.writerow(flat)


if __name__ == "__main__":
    main()
