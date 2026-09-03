"""s04_charts_plotly.py - Plotly renderer.

make_plotly_trend(view) reads the fields and
labels from the view and returns a Plotly figure.

Data is pulled as plain lists.
"""

import plotly.graph_objects as go

from s03_views import TrendView


def make_plotly_trend(view: TrendView) -> go.Figure:
    xs = view.data[view.x_field].to_list()
    ys = view.data[view.y_field].to_list()

    figure = go.Figure(go.Scatter(x=xs, y=ys, mode="lines+markers"))
    figure.update_layout(
        title=view.title,
        xaxis_title=view.x_label,
        yaxis_title=view.y_label,
    )
    return figure
