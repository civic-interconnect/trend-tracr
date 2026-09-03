"""s04_charts_matplotlib.py - Matplotlib renderer.

make_matplotlib_trend(view) reads the fields and
labels from the view and returns a Matplotlib Figure.
"""

import matplotlib

matplotlib.use("Agg")  # safe default; the notebook/app decides how to display

import matplotlib.pyplot as plt

from s03_views import TrendView


def make_matplotlib_trend(view: TrendView) -> plt.Figure:
    xs = view.data[view.x_field].to_list()
    ys = view.data[view.y_field].to_list()

    figure, axes = plt.subplots()
    axes.plot(xs, ys, marker="o")
    axes.set_title(view.title)
    axes.set_xlabel(view.x_label)
    axes.set_ylabel(view.y_label)
    figure.tight_layout()
    return figure
