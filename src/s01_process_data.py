"""s01_process_data.py - Minimal processing (raw -> processed).

This stage is DELIBERATELY minimal. It does only what every downstream layer
must be able to assume: correct types, no null observations, sorted order.

It does NOT impute, smooth, deduplicate, reconcile geographies, handle
suppressed values, or reconcile indicator revisions. That is where students
extend the pipeline - and where the interesting decisions live. Improving
this stage (and documenting the choices) is an intended exercise, noted in
the README.

Contract: input is the canonical schema from s00; output is the same schema,
cleaned to the guarantees above.
"""

import polars as pl

from s00_nist_tracr_adapter import CANONICAL_COLUMNS


def process(raw: pl.DataFrame) -> pl.DataFrame:
    """Return processed observations in the canonical schema.

    Guarantees for downstream layers:
      - year is Int64, value is Float64
      - rows with a null value are dropped
      - rows are sorted by geography, indicator, year
    """
    return (
        raw.select(CANONICAL_COLUMNS)
        .with_columns(
            pl.col("year").cast(pl.Int64),
            pl.col("value").cast(pl.Float64),
        )
        .drop_nulls(subset=["value"])
        .sort(["geography_id", "indicator_id", "year"])
    )
