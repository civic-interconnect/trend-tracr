"""Tests for s03_views.py."""

import polars as pl

from s02_analytics import TrendResult
from s03_views import TrendView, make_trend_view


def make_trend_result() -> TrendResult:
    """Return a small analytics result for view tests."""
    return TrendResult(
        data=pl.DataFrame(
            {
                "year": [2022, 2023, 2024],
                "value": [71.2, 72.5, 73.1],
            }
        ),
        geography_name="St. Louis County, Minnesota",
        indicator_name="Employment rate",
        indicator_id="employment_rate",
        unit="percent",
    )


def test_make_trend_view_returns_trend_view() -> None:
    result = make_trend_result()

    view = make_trend_view(result)

    assert isinstance(view, TrendView)


def test_make_trend_view_preserves_data() -> None:
    result = make_trend_result()

    view = make_trend_view(result)

    assert view.data.equals(result.data)


def test_make_trend_view_sets_fields() -> None:
    result = make_trend_result()

    view = make_trend_view(result)

    assert view.x_field == "year"
    assert view.y_field == "value"


def test_make_trend_view_builds_title() -> None:
    result = make_trend_result()

    view = make_trend_view(result)

    assert view.title == "Employment rate - St. Louis County, Minnesota"


def test_make_trend_view_builds_axis_labels() -> None:
    result = make_trend_result()

    view = make_trend_view(result)

    assert view.x_label == "Year"
    assert view.y_label == "Percent"


def test_make_trend_view_does_not_expose_indicator_id() -> None:
    result = make_trend_result()

    view = make_trend_view(result)

    assert not hasattr(view, "indicator_id")
