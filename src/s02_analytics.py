"""s02_analytics.py - Analytics layer.

Owns the TrendResult contract and its creation.
TrendResult is the boundary between analytics and visualization.
It contains the observations plus the semantics needed to read them.

Percent change, slope, min/max, latest value, ranking are additional
analytics.
They get their own functions and their own small result types
when the application needs them.
They do NOT get added to TrendResult.

Hard rule: this module imports no charting or notebook library.
"""

from dataclasses import dataclass

import polars as pl


@dataclass(frozen=True)
class TrendResult:
    """The observations and metadata for one indicator's trend, one geography.

    Data carries only what the trend needs: columns `year` and `value`.

    Remaining fields carry the semantics needed to understand those numbers.
    """

    data: pl.DataFrame  # columns: year (int), value (float)
    geography_name: str  # "St. Louis County, Minnesota"
    indicator_name: str  # human-readable NIST indicator name
    indicator_id: str  # stable source identifier
    unit: str  # "percent", "count", "index", ...


def get_trend(
    processed: pl.DataFrame, geography_id: str, indicator_id: str
) -> TrendResult:
    """Ask for one indicator's trend for one geography.

    Filters the processed observations to the requested series and packages
    the year/value observations with their semantics.

    Args:
        processed: The processed DataFrame containing all observations.
        geography_id: The ID of the geography to filter by.
        indicator_id: The ID of the indicator to filter by.

    Returns:
        A TrendResult containing the filtered observations and their semantics.
    """
    subset = processed.filter(
        (pl.col("geography_id") == geography_id)
        & (pl.col("indicator_id") == indicator_id)
    ).sort("year")

    if subset.is_empty():
        raise ValueError(
            f"No observations for geography_id={geography_id!r}, indicator_id={indicator_id!r}."
        )

    first = subset.row(0, named=True)
    data = subset.select(["year", "value"])

    return TrendResult(
        data=data,
        geography_name=first["geography_name"],
        indicator_name=first["indicator_name"],
        indicator_id=first["indicator_id"],
        unit=first["unit"],
    )


def list_geographies(processed: pl.DataFrame) -> list[tuple[str, str]]:
    """Return (geography_id, geography_name) pairs present in the data.

    Args:
        processed: The processed DataFrame containing all observations.

    Returns:
        A list of tuples, each containing a geography_id and its corresponding geography_name.
    """
    rows = (
        processed.select(["geography_id", "geography_name"])
        .unique()
        .sort("geography_name")
        .iter_rows()
    )
    return list(rows)


def list_indicators(processed: pl.DataFrame) -> list[tuple[str, str]]:
    """Return (indicator_id, indicator_name) pairs present in the data.

    Args:
        processed: The processed DataFrame containing all observations.

    Returns:
        A list of tuples, each containing an indicator_id and its corresponding indicator_name.
    """
    rows = (
        processed.select(["indicator_id", "indicator_name"])
        .unique()
        .sort("indicator_name")
        .iter_rows()
    )
    return list(rows)
