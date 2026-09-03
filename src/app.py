"""app.py - NIST TraCR Trend Explorer Notebook.

This notebook explores one community-resilience indicator's trend over time for
one county, using NIST Tracking Community Resilience (TraCR) data. It is also a
teaching template: fork it, re-point s00_nist_tracr_adapter.py at a different dataset,
and the rest of the pipeline and renderers keep working.

PLAN CELLS
1. Imports
2. Opening title and introduction (Markdown)
3. Load and process the data
4. Controls: county, renderer, mode
5. Controls: indicator, renderer, mode
6. Build trend result and the renderer-facing view
7. Render: one chart, or all stacked for comparison
8. Closing (Markdown)
"""

import marimo

__generated_with = "0.24.0"
app = marimo.App(width="medium")


@app.cell
async def _():
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


@app.cell
def _(mo):
    mo.md("""
    # NIST TraCR Community Trends

    Pick a county and an indicator, and watch how the indicator has
    changed over time.

    Choose one **renderer**, or switch to **Compare all** to see the same
    view rendered differently.
    """)
    return


@app.cell
def _(load_raw, mo, process):
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


@app.cell
def _(list_geographies, mo, processed):
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

    # return the selected county, mode, and renderer for further use
    return county, mode, renderer


@app.cell
def _(county, mo, mode, processed, renderer):
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

    # marimo cell displays the final layout only so it must include all UI elements
    mo.vstack(
        [
            indicator,
            mo.hstack(
                [county, renderer, mode],
                gap=1,
                justify="start",
            ),
        ],
        gap=1,
        align="start",
    )

    return (indicator,)


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
    return


@app.cell
def _(mo):
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
