# Data Card

## Dataset: Tracking Community Resilience (TraCR)

TraCR is developed by the
[National Institute of Standards and Technology (NIST)](https://www.nist.gov/)
Community Resilience Program.

TraCR is a county-level database designed to support the development,
testing, and tracking of indicators related to community resilience.

NIST reports that TraCR contains data for 3,230 counties and county
equivalents across the United States and U.S. territories.

## Official Sources

[Dataset](https://data.nist.gov/od/id/mds2-3978)

```text
Data Publication
Tracking Community Resilience (TraCR) Database
Maria Dillard, Jarrod Loerzel, Donghwan Gu, Tiffany Cousins, Tzong Hao Chen
Contact: Tiffany Cousins
Identifier: <https://doi.org/10.18434/mds2-3978>
Described in these articles:
  <https://ascelibrary.org/doi/full/10.1061/NHREFO.NHENG-1642>,
  <https://ascelibrary.org/doi/10.1061/NHREFO.NHENG-2224>

Version: 1.0
First Released: 2025-11-18
Revised: 2025-11-18

Abstract

Community resilience is the ability to
prepare, adapt, withstand, and recover from disruptions.
There is a growing field of research that focuses on
community-level resilience.
Many have developed and studied methods for measuring resilience
quantitatively and qualitatively.
The Tracking Community Resilience (TraCR) database is a tool
for developing and testing analytical methods
for computing county-level indicators for community resilience.
TraCR can be used by local communities, researchers, and
decision makers at various levels to assess and
measure longitudinal community resilience.
TraCR is part of the Community Resilience Assessment Methodology,
which aims to develop a first-generation methodology
to assess resilience at the community scale based
on community functions, supported by buildings
and infrastructure systems, and
the recovery of those functions following a disruptive hazard event.
```

## API (no access)

[NIST PDR metadata API](https://data.nist.gov/rmm/)

<https://data.nist.gov/rmm/records?keyword=TraCR>

## Direct (no access)

<https://data.nist.gov/od/ds/mds2-2297/NIST_Resilience_Indicator_Inventory_v.01.xlsx>

<https://data.nist.gov/od/ds/mds2-2297/NIST_Resilience_Indicator_Inventory_v.01_Data_Dictionary.xlsx>

## Mirror / Download Option (no access)

<https://data.nist.gov/pdr/bulkdownload/>

```shell
uv run python tools/pdrdownload.py -I mds2-3978
uv run python tools/pdrdownload.py -I mds2-3978 -D
```

## Additional Resources

[NIST Community Resilience Products](https://www.nist.gov/community-resilience/products)

[NIST Community Resilience Assessment Methodology](https://www.nist.gov/community-resilience/community-resilience-assessment-methodology)

[NIST Risk Reduction and Recovery Program](https://www.nist.gov/programs-projects/risk-reduction-and-recovery-program)

[NIST Public Data Repository](https://data.nist.gov/)

[NIST Science Data Portal](https://data.nist.gov/sdp/)

## Data Access

NIST distributes public research datasets through the
NIST Public Data Repository (PDR).

The PDR provides persistent dataset records, metadata, downloadable data
files, supporting documentation, and citation information.

## Geographic Coverage

TraCR is designed for county-level analysis.

NIST reports coverage for 3,230 counties and county equivalents,
including locations in:

- the contiguous United States
- Alaska
- Hawaii
- Puerto Rico
- the U.S. Virgin Islands

Geographic identifiers should be preserved during processing so TraCR
records can later be connected to other public datasets using standard
geographic identifiers where available.

## Temporal Coverage

TraCR is intended to support analysis of community resilience indicators
over time.

Available years vary by measure and underlying source dataset.

Missing years should not automatically be interpreted as zero values.
Missingness should be preserved and evaluated during data processing and
analysis.

## Data Content

TraCR contains measures used to develop and evaluate community resilience
indicators.

The measures draw from multiple public data sources and represent aspects
of community resilience across social, economic, physical, and related
systems.

This project does not assume that all measures have identical units,
time coverage, completeness, or interpretation.

Indicator and measure metadata should be retained whenever
possible.

## Processing

The processing layer may perform operations such as:

- standardizing column names
- preserving and standardizing geographic identifiers
- converting values to appropriate data types
- identifying time fields
- reshaping source data when needed for analysis
- retaining missing values
- preserving useful indicator and source metadata

Processed data are derived artifacts.
They do not replace or modify the original raw source files.

## Provenance

The authoritative source for TraCR data and metadata is NIST.

This repository may cache copies of public source data in `data/raw/`
for reproducibility and educational use, but those copies are not
authoritative NIST publications.

When data files are downloaded, the project should retain enough
provenance information to identify:

- source organization
- dataset name
- source URL
- download date
- source version or release, when available
- original filename
- applicable citation or DOI, when available

## License and Terms

NIST data are U.S. government research data.

Users should consult the metadata, citation information, and terms
provided with the specific TraCR release in the NIST Public Data
Repository before redistributing or publishing derived datasets.

Project software in this repository is licensed separately under the
[MIT License](../LICENSE).

## Citation

```text
Dillard, Maria , Loerzel, Jarrod , Gu, Donghwan ,
Cousins, Tiffany , Chen, Tzong Hao  (2025),
Tracking Community Resilience (TraCR) Database,
National Institute of Standards and Technology,
https://doi.org/10.18434/mds2-3978
(Version: 1.0, Accessed 2026-09-02)
```

When using this software, see:

[CITATION.cff](../CITATION.cff)

## Local Source Files

The repository currently uses the following TraCR source files:

```text
data/raw/
├── TraCR_v1_database.csv
├── TraCR_Metadata.xlsx
├── TraCR_DataCoverageMatrix.xlsx
├── TraCR_ TechnicalSupportDocument.pdf
└── README.txt
```

`TraCR_v1_database.csv` is the primary analytical data file.

The database is stored in wide format.
Each row contains a geographic identifier and year,
followed by columns representing TraCR measures and indicators.

Examples include:

```text
UID
fips
period
INFRA110007
INFRA120001
ECNVIT510001
NATENV410002
...
```

The project adapter reshapes these wide indicator columns into the canonical
long-format schema used by downstream processing, analysis, views, and
renderers:

```text
geography_id
geography_name
indicator_id
indicator_name
unit
year
value
```

In this transformation:

```text
fips                  -> geography_id
period                -> year
indicator column name -> indicator_id
indicator cell value  -> value
```

## Metadata

`TraCR_Metadata.xlsx` contains four worksheets, including:

- **Measures** - metadata for TraCR measures and indicators
- **Column Metadata** - descriptions, units, types, and other metadata for
  columns in the TraCR database
- **Source Definitions** - definitions of abbreviated source names and
  general source URLs
- an introductory worksheet describing the workbook and release

The **Column Metadata** worksheet provides the metadata currently used by
this project to associate TraCR indicator identifiers with human-readable
descriptions and units.

For example:

```text
INFRA110007
% of households with broadband internet service
```

Because browser-based Marimo WASM applications should not depend on reading
Excel workbooks at runtime, the required worksheet is exported to:

```text
data/processed/TraCR_Metadata_Column_Metadata.csv
```

and copied for browser execution to:

```text
src/public/TraCR_Metadata_Column_Metadata.csv
```

The original Excel workbook remains the source metadata artifact.
The CSV is a browser-compatible derivative used by the application.

## Browser Deployment Data

The Marimo WASM application requires browser-accessible copies of the
runtime data files under:

```text
src/public/
```

Current runtime data include:

```text
src/public/
├── TraCR_v1_database.csv
└── TraCR_Metadata_Column_Metadata.csv
```

These files allow the deployed application to operate entirely in the
browser without a Python server or database service.

Generated deployment artifacts are not authoritative source data.
The original NIST files retained under `data/raw/`
remain the source artifacts for reproducibility.

## Geographic Identifiers

The TraCR database uses the `fips` field as its geographic identifier.
FIPS values must be treated as strings rather than integers so leading zeros
are preserved. For example:

```text
01001
```

must remain `01001`, not `1001`.

The current TraCR database contains geographic identifiers but does not
provide a complete human-readable geography-name lookup in the analytical
CSV itself.
The project therefore preserves the original FIPS identifier
while a separate authoritative FIPS-to-geography-name lookup is incorporated.

Until such a lookup is available, the application may display geographic
labels using the FIPS identifier itself rather than inventing geographic
names.

A future geography lookup should be derived from an authoritative geographic
reference source and stored as a small reproducible lookup table rather than
being manually constructed.

## FIPS Geography Lookup

To add human-readable county names, use the U.S. Census Bureau's official
2020 FIPS reference file.

1. Open the Census 2020 FIPS page:

   [2020 Population Estimates FIPS Codes](https://www.census.gov/geographies/reference-files/2020/demo/popest/2020-fips.html)

2. Download:

   `2020 State, County, Minor Civil Division, and Incorporated Place FIPS Codes`

3. Save the downloaded file in:

```text
data/raw/
```

The project can then generate a small browser-safe lookup such as:

```text
data/processed/TraCR_Geography_Lookup.csv
```

with fields such as:

```text
geography_id
geography_name
```

The lookup should be generated from the downloaded Census source rather than
constructed manually.

This also avoids depending on Census network availability during application
execution or build steps. The earlier direct-download attempt failed during
DNS resolution before any Census data were retrieved.
