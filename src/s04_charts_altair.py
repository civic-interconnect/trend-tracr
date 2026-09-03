"""s04_charts_altair.py - Altair renderer.

One function, one contract:
make_altair_trend(view) reads the fields and
labels from the view and returns an Altair chart.
"""

import altair as alt

from s03_views import TrendView


def make_altair_trend(view: TrendView) -> alt.Chart:
    return (
        alt.Chart(view.data)
        .mark_line(point=True)
        .encode(  # ty: ignore[unresolved-attribute]
            x=alt.X(f"{view.x_field}:O", title=view.x_label),
            y=alt.Y(f"{view.y_field}:Q", title=view.y_label),
            tooltip=[view.x_field, view.y_field],
        )
        .properties(title=view.title)
    )
