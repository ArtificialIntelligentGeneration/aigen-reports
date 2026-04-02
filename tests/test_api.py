"""Smoke test for the dimension → data_level mapping."""

from aigen_reports.api import _data_level


def test_data_level_campaign() -> None:
    assert _data_level(["campaign_id", "stat_time_day"]) == "AUCTION_CAMPAIGN"


def test_data_level_adgroup() -> None:
    assert _data_level(["adgroup_id", "stat_time_day"]) == "AUCTION_ADGROUP"


def test_data_level_ad() -> None:
    assert _data_level(["ad_id", "stat_time_day"]) == "AUCTION_AD"
