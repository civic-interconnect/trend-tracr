"""Tests for s02_analytics.py."""

import polars as pl
import pytest

from s02_analytics import (
    TrendResult,
    get_trend,
    list_geographies,
    list_indicators,
)


def make_processed_data() -> pl.DataFrame:
    """Return a small processed dataset for analytics tests."""
    return pl.DataFrame(
        {
            "geography_id": ["27001", "27001", "27001", "27003"],
            "geography_name": [
                "Aitkin County, Minnesota",
                "Aitkin County, Minnesota",
                "Aitkin County, Minnesota",
                "Anoka County, Minnesota",
            ],
            "indicator_id": [
                "indicator_a",
                "indicator_a",
                "indicator_b",
                "indicator_a",
            ],
            "indicator_name": [
                "Indicator A",
                "Indicator A",
                "Indicator B",
                "Indicator A",
            ],
            "unit": [
                "percent",
                "percent",
                "count",
                "percent",
            ],
            "year": [2024, 2023, 2024, 2024],
            "value": [42.5, 40.0, 100.0, 55.0],
        }
    )


def test_get_trend_returns_trend_result() -> None:
    processed = make_processed_data()

    result = get_trend(
        processed,
        geography_id="27001",
        indicator_id="indicator_a",
    )

    assert isinstance(result, TrendResult)


def test_get_trend_returns_requested_series_only() -> None:
    processed = make_processed_data()

    result = get_trend(
        processed,
        geography_id="27001",
        indicator_id="indicator_a",
    )

    assert result.data.rows() == [
        (2023, 40.0),
        (2024, 42.5),
    ]


def test_get_trend_returns_only_year_and_value_columns() -> None:
    processed = make_processed_data()

    result = get_trend(
        processed,
        geography_id="27001",
        indicator_id="indicator_a",
    )

    assert result.data.columns == ["year", "value"]


def test_get_trend_returns_metadata() -> None:
    processed = make_processed_data()

    result = get_trend(
        processed,
        geography_id="27001",
        indicator_id="indicator_a",
    )

    assert result.geography_name == "Aitkin County, Minnesota"
    assert result.indicator_name == "Indicator A"
    assert result.indicator_id == "indicator_a"
    assert result.unit == "percent"


def test_get_trend_raises_for_missing_series() -> None:
    processed = make_processed_data()

    with pytest.raises(
        ValueError,
        match="No observations",
    ):
        get_trend(
            processed,
            geography_id="99999",
            indicator_id="indicator_a",
        )


def test_list_geographies_returns_unique_pairs_sorted_by_name() -> None:
    processed = make_processed_data()

    result = list_geographies(processed)

    assert result == [
        ("27001", "Aitkin County, Minnesota"),
        ("27003", "Anoka County, Minnesota"),
    ]


def test_list_indicators_returns_unique_pairs_sorted_by_name() -> None:
    processed = make_processed_data()

    result = list_indicators(processed)

    assert result == [
        ("indicator_a", "Indicator A"),
        ("indicator_b", "Indicator B"),
    ]
