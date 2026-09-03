"""s00_nist_tracr_adapter.py - Adapter for NIST TraCR source data.

The NIST TraCR CSV is stored in wide format:

    UID
    fips
    period
    INFRA120001
    INFRA120002
    ...
    NATENV410005

This adapter converts it to the canonical long format used downstream:

    geography_id
    geography_name
    indicator_id
    indicator_name
    unit
    year
    value

The TraCR CSV provides:

    geography_id  <- fips
    indicator_id  <- indicator column name
    year          <- period
    value         <- indicator cell value

The TraCR metadata workbook, sheet "Column Metadata", provides:

    indicator_name <- Description
    unit           <- Unit

The metadata workbook does not provide a FIPS-to-geography-name lookup, so
geography_name remains an explicit FIPS-based label until a geography lookup
source is incorporated.
"""

from pathlib import Path
from typing import Any

import polars as pl

CANONICAL_COLUMNS = [
    "geography_id",
    "geography_name",
    "indicator_id",
    "indicator_name",
    "unit",
    "year",
    "value",
]

RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"

TRACR_FILE = RAW_DIR / "TraCR_v1_database.csv"

ID_COLUMNS = ["UID", "fips", "period"]

METADATA_SHEET = "Column Metadata"

METADATA_REQUIRED_COLUMNS = [
    "Column Name",
    "Description",
    "Unit",
]


def load_geography_metadata(path: Any) -> pl.DataFrame:
    """Load Census geography names and construct TraCR-compatible FIPS IDs."""
    geography = pl.read_csv(
        str(path),
        schema_overrides={
            "Summary Level": pl.String,
            "State Code (FIPS)": pl.String,
            "County Code (FIPS)": pl.String,
            "Area Name (including legal/statistical area description)": pl.String,
        },
    )

    summary_col = "Summary Level"
    state_col = "State Code (FIPS)"
    county_col = "County Code (FIPS)"
    name_col = "Area Name (including legal/statistical area description)"

    required = [
        summary_col,
        state_col,
        county_col,
        name_col,
    ]

    missing = [column for column in required if column not in geography.columns]

    if missing:
        raise ValueError(
            f"Census geography file is missing required columns: {missing}"
        )

    geography = geography.with_columns(
        pl.col(summary_col).cast(pl.String).str.strip_chars(),
        pl.col(state_col).cast(pl.String).str.zfill(2),
        pl.col(county_col).cast(pl.String).str.zfill(3),
        pl.col(name_col).cast(pl.String).str.strip_chars(),
    )

    # State names are needed so county dropdown labels are unique.
    states = (
        geography.filter(pl.col(summary_col) == "40")
        .select(
            pl.col(state_col),
            pl.col(name_col).alias("state_name"),
        )
        .unique(subset=[state_col])
    )

    state_lookup = states.select(
        (pl.col(state_col) + pl.lit("000")).alias("geography_id"),
        pl.col("state_name").alias("geography_name"),
    )

    county_lookup = (
        geography.filter(pl.col(summary_col) == "50")
        .join(
            states,
            on=state_col,
            how="left",
        )
        .select(
            (pl.col(state_col) + pl.col(county_col)).alias("geography_id"),
            (pl.col(name_col) + pl.lit(", ") + pl.col("state_name")).alias(
                "geography_name"
            ),
        )
    )

    us_lookup = pl.DataFrame(
        {
            "geography_id": ["00000"],
            "geography_name": ["United States"],
        }
    )

    return (
        pl.concat(
            [
                us_lookup,
                state_lookup,
                county_lookup,
            ]
        )
        .unique(
            subset=["geography_id"],
            keep="first",
        )
        .sort("geography_id")
    )


def load_indicator_metadata(path: Any) -> pl.DataFrame:
    """Load TraCR indicator metadata from the browser-friendly CSV."""
    metadata = pl.read_csv(
        str(path),
        schema_overrides={
            "Column Name": pl.String,
            "Description": pl.String,
            "Unit": pl.String,
        },
    )

    required = [
        "Column Name",
        "Description",
        "Unit",
    ]

    missing = [column for column in required if column not in metadata.columns]

    if missing:
        raise ValueError(f"TraCR metadata CSV is missing required columns: {missing}")

    return (
        metadata.select(
            pl.col("Column Name").str.strip_chars().alias("indicator_id"),
            pl.col("Description").str.strip_chars().alias("indicator_name"),
            pl.col("Unit").str.strip_chars().alias("unit"),
        )
        .filter(
            pl.col("indicator_id").is_not_null()
            & pl.col("indicator_name").is_not_null()
        )
        .unique(
            subset=["indicator_id"],
            keep="first",
        )
    )


def load_raw(
    path: Any | None = None,
    metadata_path: Any | None = None,
    geography_path: Any | None = None,
) -> pl.DataFrame:
    """Load NIST TraCR data and convert it to canonical long format."""
    source = path or TRACR_FILE

    if isinstance(source, Path) and not source.exists():
        raise FileNotFoundError(f"TraCR source file not found: {source}")

    if metadata_path is None:
        raise ValueError(
            "TraCR metadata workbook path is required. "
            "Pass metadata_path=... to load_raw()."
        )

    if isinstance(metadata_path, Path) and not metadata_path.exists():
        raise FileNotFoundError(f"TraCR metadata workbook not found: {metadata_path}")

    try:
        frame = pl.read_csv(
            str(source),
            schema_overrides={
                "fips": pl.String,
            },
        )
    except Exception as exc:
        raise RuntimeError(
            "\nUnable to read the TraCR CSV.\n\n"
            f"Source:\n  {source}\n\n"
            f"Original error:\n  {type(exc).__name__}: {exc}"
        ) from exc

    missing_id_columns = [
        column for column in ID_COLUMNS if column not in frame.columns
    ]

    if missing_id_columns:
        raise ValueError(
            "\nTraCR source is missing required identifier columns.\n\n"
            f"Missing:\n  {missing_id_columns}\n\n"
            f"Actual columns:\n  {frame.columns}"
        )

    indicator_columns = [column for column in frame.columns if column not in ID_COLUMNS]

    if not indicator_columns:
        raise ValueError("TraCR source contains no indicator columns.")

    # TraCR indicator columns contain numeric observations plus occasional
    # source-specific text codes.
    # Cast them to string before unpivoting so the wide table
    # has a consistent dtype across all indicator columns.
    frame = frame.with_columns(
        pl.col(indicator_columns).cast(
            pl.String,
            strict=False,
        )
    )

    # Convert the wide TraCR table into one observation per row.
    long_frame = frame.unpivot(
        index=["fips", "period"],
        on=indicator_columns,
        variable_name="indicator_id",
        value_name="value_raw",
    )

    metadata = load_indicator_metadata(metadata_path)

    if geography_path is None:
        raise ValueError(
            "Census geography lookup path is required. "
            "Pass geography_path=... to load_raw()."
        )

    geography = load_geography_metadata(geography_path)

    canonical = (
        long_frame.with_columns(
            pl.col("fips").cast(pl.String).alias("geography_id"),
            pl.col("period").cast(pl.Int64).alias("year"),
            pl.col("indicator_id").cast(pl.String),
            pl.col("value_raw").cast(pl.Float64, strict=False).alias("value"),
        )
        .filter(pl.col("value").is_not_null())
        .join(
            metadata,
            on="indicator_id",
            how="left",
        )
        .join(
            geography,
            on="geography_id",
            how="left",
        )
        .with_columns(
            pl.coalesce(
                [
                    pl.col("geography_name"),
                    pl.lit("FIPS ") + pl.col("geography_id"),
                ]
            ).alias("geography_name"),
            pl.coalesce(
                [
                    pl.col("indicator_name"),
                    pl.col("indicator_id"),
                ]
            ).alias("indicator_name"),
            pl.coalesce(
                [
                    pl.col("unit"),
                    pl.lit(""),
                ]
            ).alias("unit"),
        )
        .select(CANONICAL_COLUMNS)
        .sort(
            [
                "geography_id",
                "indicator_id",
                "year",
            ]
        )
    )

    if canonical.is_empty():
        raise ValueError(
            "TraCR source loaded successfully, but no numeric observations "
            "were produced after converting the wide indicator columns."
        )

    unmatched_indicators = (
        canonical.filter(pl.col("indicator_name") == pl.col("indicator_id"))
        .select("indicator_id")
        .unique()
        .sort("indicator_id")
    )

    if unmatched_indicators.height:
        print(
            "[s00_nist_tracr_adapter] WARNING: "
            f"{unmatched_indicators.height} indicator(s) did not match "
            "the Column Metadata sheet:"
        )
        print(unmatched_indicators)

    print(
        "[s00_nist_tracr_adapter] Loaded NIST TraCR data: "
        f"{canonical.height:,} observations, "
        f"{canonical['geography_id'].n_unique():,} geographies, "
        f"{canonical['indicator_id'].n_unique():,} indicators."
    )

    return canonical
