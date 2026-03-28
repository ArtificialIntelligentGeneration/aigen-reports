"""Command-line interface for AiGen Reports."""

from __future__ import annotations

import csv
import os
from datetime import date, timedelta
from pathlib import Path

import click

from .api import ReportRequest, fetch_report

DEFAULT_METRICS = ["spend", "clicks", "impressions", "conversions"]


def _resolve_range(spec: str) -> tuple[str, str]:
    if spec.startswith("last-") and spec.endswith("d"):
        n = int(spec[len("last-") : -1])
        end = date.today()
        start = end - timedelta(days=n - 1)
        return start.isoformat(), end.isoformat()
    raise click.BadParameter(f"unsupported range: {spec}; use last-Nd")


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
    token = os.environ.get("TIKTOK_ACCESS_TOKEN")
    if not token:
        raise click.ClickException("TIKTOK_ACCESS_TOKEN env var not set; run `aigen-reports auth`")

    dim_map = {
        "campaign": ["campaign_id", "campaign_name", "stat_time_day"],
        "adgroup": ["adgroup_id", "adgroup_name", "stat_time_day"],
        "ad": ["ad_id", "ad_name", "stat_time_day"],
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
