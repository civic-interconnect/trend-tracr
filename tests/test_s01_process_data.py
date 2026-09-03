"""Tests for s01_process_data.py."""

import polars as pl

from s00_nist_tracr_adapter import CANONICAL_COLUMNS
from s01_process_data import process


def test_process_returns_canonical_columns() -> None:
    raw = pl.DataFrame(
        {
            "geography_id": ["27001"],
            "geography_name": ["Aitkin County, Minnesota"],
            "indicator_id": ["example_indicator"],
            "indicator_name": ["Example Indicator"],
            "unit": ["percent"],
            "year": ["2024"],
            "value": ["42.5"],
        }
    )

    result = process(raw)

    assert result.columns == CANONICAL_COLUMNS


def test_process_casts_year_and_value_types() -> None:
    raw = pl.DataFrame(
        {
            "geography_id": ["27001"],
            "geography_name": ["Aitkin County, Minnesota"],
            "indicator_id": ["example_indicator"],
            "indicator_name": ["Example Indicator"],
            "unit": ["percent"],
            "year": ["2024"],
            "value": ["42.5"],
        }
    )

    result = process(raw)

    assert result.schema["year"] == pl.Int64
    assert result.schema["value"] == pl.Float64


def test_process_drops_rows_with_null_values() -> None:
    raw = pl.DataFrame(
        {
            "geography_id": ["27001", "27001"],
            "geography_name": [
                "Aitkin County, Minnesota",
                "Aitkin County, Minnesota",
            ],
            "indicator_id": [
                "example_indicator",
                "example_indicator",
            ],
            "indicator_name": [
                "Example Indicator",
                "Example Indicator",
            ],
            "unit": ["percent", "percent"],
            "year": [2023, 2024],
            "value": [42.5, None],
        }
    )

    result = process(raw)

    assert result.height == 1
    assert result["year"].to_list() == [2023]
    assert result["value"].to_list() == [42.5]


def test_process_sorts_by_geography_indicator_and_year() -> None:
    raw = pl.DataFrame(
        {
            "geography_id": ["27003", "27001", "27001", "27001"],
            "geography_name": [
                "Anoka County, Minnesota",
                "Aitkin County, Minnesota",
                "Aitkin County, Minnesota",
                "Aitkin County, Minnesota",
            ],
            "indicator_id": [
                "indicator_b",
                "indicator_b",
                "indicator_a",
                "indicator_a",
            ],
            "indicator_name": [
                "Indicator B",
                "Indicator B",
                "Indicator A",
                "Indicator A",
            ],
            "unit": [
                "percent",
                "percent",
                "percent",
                "percent",
            ],
            "year": [2024, 2024, 2024, 2023],
            "value": [4.0, 3.0, 2.0, 1.0],
        }
    )

    result = process(raw)

    assert result.select(
        "geography_id",
        "indicator_id",
        "year",
    ).rows() == [
        ("27001", "indicator_a", 2023),
        ("27001", "indicator_a", 2024),
        ("27001", "indicator_b", 2024),
        ("27003", "indicator_b", 2024),
    ]


def test_process_preserves_valid_observation_values() -> None:
    raw = pl.DataFrame(
        {
            "geography_id": ["27001"],
            "geography_name": ["Aitkin County, Minnesota"],
            "indicator_id": ["example_indicator"],
            "indicator_name": ["Example Indicator"],
            "unit": ["percent"],
            "year": [2024],
            "value": [42.5],
        }
    )

    result = process(raw)

    assert result.row(0, named=True) == {
        "geography_id": "27001",
        "geography_name": "Aitkin County, Minnesota",
        "indicator_id": "example_indicator",
        "indicator_name": "Example Indicator",
        "unit": "percent",
        "year": 2024,
        "value": 42.5,
    }
