"""app.py - NIST TraCR Trend Explorer Notebook.

This notebook explores one community-resilience indicator's trend over time for
one county, using NIST Tracking Community Resilience (TraCR) data. It is also a
teaching template: fork it, re-point s00_nist_tracr_adapter.py at a different dataset,
and the rest of the pipeline and renderers keep working.

PLAN CELLS FIRST

1. Imports (always first, so the notebook is self-contained)
2. Opening title and introduction (Markdown)
3. Load and process the data
4. Controls: county, renderer, mode
5. Controls: indicator, renderer, mode
6. Build trend result and the renderer-facing view
7. Render: one chart, or all stacked for comparison
8. Closing (Markdown)

HOW MARIMO NOTEBOOKS WORK

Each cell is a FUNCTION.
The return value of one cell can be passed as an argument to another cell.
We never call the functions, so they don't need names other than `_` (underscore).
(You can give them names if you want, but the notebook engine ignores them.)

The notebook is REACTIVE: when a cell's code or inputs change,
the notebook engine reruns that cell and every cell that depends on it.

The notebook is always CONSISTENT with outputs reflecting current inputs.

The first cell imports all dependencies, so the notebook is SELF-CONTAINED.

All later cells include their dependencies in their argument list.
Some other cells return values that can be used in other cells.
A cell displays the value of its last expression.

A cell whose last line is an assignment or a bare return
(like data and view cells) displays nothing;
only markdown, control, and render cells are meant to show.

RULE: Each variable must be defined in exactly one cell.
Defining the same name in two cells is a marimo error.

INPUT WIDGETS/CONTROLS: A cell that builds an input widget
resets that widget to its default every time the cell reruns.
marimo reruns a cell whenever any argument in its signature changes.
So a widget-building cell must depend only on what genuinely determines its options.
"""

# === ONLY THIS AT THE TOP OF THE FILE ===

import marimo

__generated_with_marimo_version__ = "0.24.0"
app = marimo.App(width="medium")

# === FIRST CELL IMPORTS AND RETURNS DEPS TO MAKE IT SELF-CONTAINED ===


@app.cell
async def _():
    """Import every dependency and hand them to the rest of the notebook.

    This cell has no arguments: it is the root of the dependency graph.

    It returns each import so later cells can name them as parameters.
    The micropip block installs plotly and pyarrow only under WASM (emscripten),
    used when running in GitHub Pages or other browsers
    where they are not preinstalled.
    Running locally, they are available in the project Python environment.
    """
    import sys

    import altair as alt
    import marimo as mo
    import matplotlib.pyplot as plt
    import polars as pl

    if sys.platform == "emscripten":
        import micropip

        await micropip.install(["plotly", "pyarrow"])

    import plotly.express as px

    from s00_nist_tracr_adapter import load_raw
    from s01_process_data import process
    from s02_analytics import get_trend, list_geographies, list_indicators
    from s03_views import make_trend_view
    from s04_charts_altair import make_altair_trend
    from s04_charts_matplotlib import make_matplotlib_trend
    from s04_charts_plotly import make_plotly_trend

    return (
        get_trend,
        list_geographies,
        load_raw,
        make_altair_trend,
        make_matplotlib_trend,
        make_plotly_trend,
        make_trend_view,
        mo,
        process,
    )


# ===  TYPICALLY START WITH A MARKDOWN TITLE AND OPENING ===


@app.cell
def _(mo):
    """Render the opening title and instructions. Depends only on `mo`."""
    mo.md("""
    # NIST TraCR Community Trends

    Pick a county and an indicator, and watch how the indicator has
    changed over time.

    Choose one **renderer**, or switch to **Compare all** to see the same
    view rendered differently.
    """)
    return


# ===  LOAD AND PROCESS THE DATA ===


@app.cell
def _(load_raw, mo, process):
    """Load the TraCR data and return the processed frame.

    Depends on the adapter (`load_raw`), the processor (`process`),
    and `mo` for `notebook_location()`, which resolves the three CSVs under public/
    both locally and in the exported WASM build for GitHub Pages.
    Reruns only when those change,
    so the expensive load does not repeat when the user touches a control.

    Returns `processed` for every downstream cell.
    """
    tracr_path = mo.notebook_location() / "public" / "TraCR_v1_database.csv"

    metadata_path = (
        mo.notebook_location() / "public" / "TraCR_Metadata_Column_Metadata.csv"
    )
    geography_path = mo.notebook_location() / "public" / "all-geocodes-v2020.csv"
    processed = process(
        load_raw(
            tracr_path,
            metadata_path=metadata_path,
            geography_path=geography_path,
        )
    )

    # return the processed data for further use
    return (processed,)


# ===  CONTROLS: SELECT GEOGRAPHY, RENDERER, AND MODE ===


@app.cell
def _(list_geographies, mo, processed):
    """Build and lay out the county, renderer, and mode controls.

    Depends on `processed` (to list geographies) and `mo`.
    It deliberately does NOT depend on `county`, `renderer`, or `mode`.
    This cell creates them, so nothing the user toggles reruns it,
    and these widgets never rebuild or reset once made.

    Returns the county, mode, and renderer widgets.
    """
    geographies = list_geographies(processed)

    county = mo.ui.dropdown(
        options={name: gid for gid, name in geographies},
        value=geographies[0][1],
        label="County",
    )

    renderer = mo.ui.dropdown(
        options=["Altair", "Plotly", "Matplotlib"],
        value="Altair",
        label="Renderer",
    )

    mode = mo.ui.radio(
        options=["Single", "Compare all"],
        value="Single",
        label="Mode",
    )

    # Display the independent controls here, where they are created.
    mo.vstack(
        [
            county,
            mo.hstack([renderer, mode], gap=1, justify="start"),
        ],
        gap=1,
        align="start",
    )

    return county, mode, renderer


# ===  CONTROLS: SELECT INDICATOR ===


@app.cell
def _(county, mo, processed):
    """Build the indicator control, scoped to the selected county.

    Depends ONLY on `county` (plus `processed` and `mo`) on purpose.
    Different counties report different indicators,
    so the list must rebuild when the county changes.
    Rebuilding resets the indicator to the first available,
    which is correct, since a new county may not report the
    previously selected indicator.

    This cell builds a widget, and a widget-building cell
    resets to its default every time it reruns;
    adding a control the user toggles would rerun this cell on every
    toggle and reset the indicator.

    Returns the `indicator` widget.
    """
    available_indicators = (
        processed.filter(processed["geography_id"] == county.value)
        .select(
            "indicator_id",
            "indicator_name",
        )
        .unique()
        .sort("indicator_name")
    )

    indicator_options = {
        name: indicator_id for indicator_id, name in available_indicators.iter_rows()
    }

    indicator = mo.ui.dropdown(
        options=indicator_options,
        value=available_indicators.row(0)[1],
        label="Indicator",
    )

    # display
    indicator

    return (indicator,)


# ===  RETURN THE VIEW FOR RENDERING ===


@app.cell
def _(county, get_trend, indicator, make_trend_view, processed):
    result = get_trend(
        processed,
        geography_id=county.value,
        indicator_id=indicator.value,
    )
    view = make_trend_view(result)

    # return the view for further use
    return (view,)


# === DISPLAY THE RENDERED CHART(S) ===


@app.cell
def _(
    make_altair_trend,
    make_matplotlib_trend,
    make_plotly_trend,
    mo,
    mode,
    renderer,
    view,
):
    """Render `view` with one renderer, or stacked in Compare mode.

    Depends on `view` (the data), and on `mode`/`renderer` (the user's display
    choices).
    This cell is meant to rerun on those toggles:
    it consumes the controls, it does not create them, so
    rerunning re-renders without resetting anything.

    Altair is returned via `mo.as_html`, not `mo.ui.altair_chart`,
    because the interactive wrapper over-serializes under WASM (it will send a LOT of data)
    and can blow past marimo's output-size limit.

    Returns nothing; its last expression displays the chart.
    """

    def render_one(name):
        if name == "Altair":
            chart = make_altair_trend(view)
            return mo.ui.altair_chart(chart)
        elif name == "Plotly":
            chart = make_plotly_trend(view)
            return mo.ui.plotly(chart)
        elif name == "Matplotlib":
            chart = make_matplotlib_trend(view)
            return mo.as_html(chart)

    if mode.value == "Compare all":
        output = mo.vstack(
            [render_one(name) for name in ["Altair", "Plotly", "Matplotlib"]],
            gap=2,
        )
    else:
        output = render_one(renderer.value)

    # display
    output

    # return the output for further use
    return (output,)


# ===  TYPICALLY END WITH A MARKDOWN SOURCE LINK AND CLOSING ===


@app.cell
def _(mo):
    """Render the closing suggestions and source link. Depends only on `mo`."""
    mo.md("""
    ## Suggestions

    - **Improve `s01`.** Processing is deliberately minimal.
      Add handling for suppressed values, revised indicators, or missing years.
      Document decisions.
    - **Add an analytic.** Percent change, slope, or a ranking can be new
      functions in `s02` returning their own small result types.

    [Source](https://github.com/civic-interconnect/trend-tracr)
    """)
    return


if __name__ == "__main__":
    app.run()
