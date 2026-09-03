"""s03_views.py - View preparation layer.

Turns a TrendResult (analytics) into a TrendView (presentation).

TrendView is the contract every renderer consumes.
It holds what a trend chart needs:

- the data
- which columns represent x and y,
- the human-facing title and axis labels

A renderer never sees an indicator_id or a geography_id.
"""

from dataclasses import dataclass

import polars as pl

from s02_analytics import TrendResult


@dataclass(frozen=True)
class TrendView:
    """Everything a renderer needs, and nothing it does not."""

    data: pl.DataFrame  # semantic columns kept: year, value
    x_field: str  # "year"
    y_field: str  # "value"
    title: str  # "Employment rate - St. Louis County, Minnesota"
    x_label: str  # "Year"
    y_label: str  # "Percent"


def make_trend_view(result: TrendResult) -> TrendView:
    """Build the renderer-facing view from an analytics result."""
    return TrendView(
        data=result.data,
        x_field="year",
        y_field="value",
        title=f"{result.indicator_name} - {result.geography_name}",
        x_label="Year",
        y_label=result.unit.title(),
    )
