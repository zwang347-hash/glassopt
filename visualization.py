"""Draw the pane in the raw stock's coordinate system."""

from matplotlib.figure import Figure
from matplotlib.patches import Polygon, Rectangle

from geometry import GlassPlan, VERTICES


def draw_plan(plan: GlassPlan) -> Figure:
    figure = Figure(figsize=(7.2, 4.8), layout="constrained")
    axes = figure.subplots()
    stock = plan.stock
    points = [(x - stock.left, y - stock.bottom)
              for x, y in map(stock.project, plan.points)]

    axes.add_patch(Rectangle((0, 0), stock.width, stock.height,
                             facecolor="#eef2f6", edgecolor="#526578",
                             linewidth=1.6, label="Raw stock"))
    axes.add_patch(Polygon(points, closed=True, facecolor="#a9e1d6",
                           edgecolor="#087b72", linewidth=2, label="Glass"))
    for i in range(2, len(points) - 1):
        x, y = zip(points[0], points[i])
        axes.plot(x, y, "--", color="#526578", linewidth=1,
                  label="Input diagonal" if i == 2 else None)
    for label, point in zip(VERTICES, points):
        axes.annotate(label, point, xytext=(5, 5), textcoords="offset points",
                      color="#143341", weight="bold")

    padding = max(stock.width, stock.height) * 0.06
    axes.set(xlim=(-padding, stock.width + padding),
             ylim=(-padding, stock.height + padding), aspect="equal",
             xlabel="X (mm)", ylabel="Y (mm)")
    axes.ticklabel_format(style="plain", useOffset=False)
    axes.legend(loc="lower center", bbox_to_anchor=(0.5, 1.01), ncols=3, frameon=False)
    return figure
