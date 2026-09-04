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

Human-readable geography names are joined from an authoritative Census
geography reference file (the "all geocodes" CSV) using FIPS identifiers:

    geography_name <- Census Area Name, by geography_id (FIPS)

Any observation whose FIPS id has no match in the Census file falls back to
an explicit "FIPS <id>" label rather than being dropped, so every
observation keeps a usable name.
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
    """Build a FIPS-to-name lookup: geography_id -> human-readable place name.

    The Census file lists every kind of geography (nation, state, county, and
    smaller) in one file, each row tagged with a "Summary Level" code.
    This function keeps only the two levels TraCR uses - states (level "40") and
    counties (level "50") - and turns each into a two-column lookup:
    a 5-digit FIPS geography_id and the name to show a person.

    Construction details:

    - IDs are built, not read.
      A state's id is its 2-digit state code padded to 5 digits
      with "000" (Minnesota -> "27000").
      A county's id is the 2-digit state code followed
      by the 3-digit county code ("27137" for St. Louis County, MN).
      This is string assembly so the ids line up with
      the 5-digit fips values in the TraCR data.
      It is not a database key.
    - County names get their state appended (", Minnesota") because county
      names repeat across states, and a dropdown of bare county names would
      be ambiguous.

    A hardcoded United States row ("00000") is prepended so national-level
    observations also resolve to a name.

    No SQL Needed.
    This looks like two related tables because a county row
    is enriched with its state's name (the join to `states`).
    That inner join exists only to attach the state label to each
    county so the display name is unique.
    It is not modeling a state-has-many-counties relationship.
    The output is a flat lookup table, one row per geography,
    with no relationship left to reason about.

    Args:
        path: Path (or path-like) to the Census "all geocodes" CSV. Must
            contain the columns Summary Level, State Code (FIPS),
            County Code (FIPS), and the long Area Name column.

    Returns:
        A DataFrame with exactly two columns, geography_id and geography_name,
        one row per geography, sorted by geography_id and de-duplicated.

    Raises:
        ValueError: If any of the required Census columns are absent.
    """
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
    """Build an indicator lookup: indicator_id -> readable name and unit.

    The TraCR data identifies each indicator only by a terse column code
    (like "INFRA120001").
    This function reads the metadata that NIST ships with the data and
    produces a small lookup that translates each code
    into a human-readable description and its unit of measure ("percent",
    "count", ...), so downstream layers and charts can label things for a
    person instead of showing raw codes.

    It reads three columns from the metadata:
    Column Name, Description, and Unit.
    It renames them to the canonical indicator_id, indicator_name, and unit,
    trims stray whitespace, drops rows with no code or no description,
    and keeps one row per indicator.

    No SQL Needed.
    Like the geography lookup, this is a reference table
    that can be attached to observations, not the other half
    of a relationship to model.
    Its only job is translation: code in, human-readable label out.

    Args:
        path: Path (or path-like) to the browser-friendly metadata CSV
            (the "Column Metadata" sheet exported to CSV). Must contain the
            columns Column Name, Description, and Unit.

    Returns:
        A DataFrame with columns indicator_id, indicator_name, and unit,
        de-duplicated to one row per indicator_id.

    Raises:
        ValueError: If any of the required metadata columns are absent.
    """
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
    """Read the wide TraCR CSV and return one good row per observation.

    This is the adapter's entry point and the only function the rest of the
    pipeline calls.
    It does the full conversion from "raw NIST file" to the
    canonical long-form schema every later layer (s01 onward) assumes:

        geography_id, geography_name, indicator_id, indicator_name,
        unit, year, value

    It:

    1. Reads the TraCR CSV, keeping `fips` as a string so leading zeros
       survive (state 01 must not become 1).
    2. Confirms the three identifier columns (UID, fips, period) are present;
       every other column is treated as an indicator.
    3. Casts all indicator columns to string first, because a few carry text
       codes among the numbers, and unpivoting needs one consistent dtype.
    4. Unpivots the wide table - hundreds of indicator columns - into long
       form: one row per (geography, indicator, year) observation.
       This is the key reshape; wide-to-long makes the data tidy.
    5. Casts each column to its final type, drops rows whose value is not
       numeric (this is how text codes and blanks are removed), and attaches
       the two lookups: indicator name/unit by indicator_id, and
       place name by geography_id.
    6. Fills gaps gracefully: an indicator with no metadata match keeps its
       code as its name; a geography with no Census match shows "FIPS <id>"
       rather than an empty cell. Nothing is dropped for lacking a label.

    No SQL Required.
    Steps 5-6 use left joins to two lookup tables,
    but the mental model is "attach a label to each observation," not
    "relate two entities."
    The observations are the thing; the lookups are dictionaries glued on.
    A left join (not inner) is deliberate.
    An observation with no matching name still survives, just with a
    fallback label.

    It prints a one-line load summary, and warns if any indicators failed to
    match the metadata sheet, so a bad or stale metadata file is visible
    immediately rather than showing up as unlabeled charts later.

    Args:
        path: Path to the TraCR CSV. Defaults to the packaged
            data/raw/TraCR_v1_database.csv when omitted.
        metadata_path: Path to the indicator metadata CSV. Required - there
            is no sensible default, so it must be passed explicitly.
        geography_path: Path to the Census geography CSV. Required for the
            same reason.

    Returns:
        A DataFrame in the canonical long-form schema (CANONICAL_COLUMNS),
        sorted by geography_id, indicator_id, then year, with every value
        column non-null.

    Raises:
        ValueError: If metadata_path or geography_path is None, if required
            identifier columns are missing, if there are no indicator columns,
            or if the conversion yields no numeric observations.
        FileNotFoundError: If a provided source or metadata path does not exist.
        RuntimeError: If the TraCR CSV cannot be read at all.
    """
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
