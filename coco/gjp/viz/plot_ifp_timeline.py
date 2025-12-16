# %%
import json
from pathlib import Path

import altair as alt
import polars as pl

from coco.config import FIGURES_DIR, logger


def make_ifp_timeline_chart(
    ifps_lf: pl.LazyFrame,
    *,
    title: str = "IFP Question Timeline (Open → Closed)",
    width: int = 800,
    height: int = 800,
    short_title_regex: str | None = None,
) -> alt.LayerChart:
    """Timeline visualization of IFP open/close periods."""
    ifps = IFPs.load()
    lf = ifps.filter_studied(ifps_lf)
    if short_title_regex is not None:
        lf = lf.filter(pl.col("short_title").str.contains(short_title_regex))

    timeline_df = (
        lf.select(["ifp_id", "short_title", "date_start", "date_closed"])
        .sort(["date_start", "date_closed", "ifp_id"])
        .with_row_index("y_idx")
        .collect()
    )

    base = alt.Chart(timeline_df)

    row_px = 14
    n_rows = len(timeline_df)
    resolved_height = max(height, row_px * n_rows)

    y_enc = alt.Y(
        "y_idx:Q",
        title=None,
        axis=alt.Axis(labels=False, ticks=False, domain=False),
        # Explicit domain avoids Vega-Lite "nicifying" to a much larger max, which
        # can create massive empty space between the last bar and the x-axis.
        scale=alt.Scale(domain=[-0.5, n_rows - 0.5], reverse=True, nice=False),
    )

    bars = base.mark_bar(height=10).encode(
        x=alt.X("date_start:T", title="Date"),
        x2="date_closed:T",
        y=y_enc,
        color=alt.Color("date_start:T", scale=alt.Scale(scheme="viridis"), legend=None),
        tooltip=[
            alt.Tooltip("ifp_id:N", title="IFP"),
            alt.Tooltip("short_title:N", title="Title"),
            alt.Tooltip("date_start:T", title="Opened"),
            alt.Tooltip("date_closed:T", title="Closed"),
        ],
    )

    labels = base.mark_text(align="left", dx=3, fontSize=8, color="white").encode(
        x="date_start:T",
        y=y_enc,
        text="short_title:N",
    )

    zoom_x = alt.selection_interval(bind="scales", encodings=["x"])
    zoom_y = alt.selection_interval(bind="scales", encodings=["y"])

    return (
        (bars + labels)
        .properties(
            title=title,
            width=width,
            height=resolved_height,
        )
        .add_params(zoom_x, zoom_y)
        .configure_legend(
            titleFontSize=14,
            labelFontSize=12,
            symbolSize=160,
        )
        .configure_title(fontSize=18)
    )


def save_ifp_timeline_chart(chart: alt.TopLevelMixin, *, timeline_dir: str | Path) -> None:
    """Save chart JSON spec + PDF to `timeline_dir`."""
    timeline_dir = Path(timeline_dir)
    timeline_dir.mkdir(parents=True, exist_ok=True)
    (timeline_dir / "ifp_timeline.vl.json").write_text(json.dumps(chart.to_dict(), indent=2))
    chart.save(timeline_dir / "ifp_timeline.pdf")


# %%
if __name__ == "__main__":
    from IPython.display import display

    from coco.gjp.models.ifp import IFPs

    logger.info("== IFPs Timeline Chart")
    ifps = IFPs.load()
    chart = make_ifp_timeline_chart(ifps.lf)
    display(chart)

    logger.info("== Saving IFP Timeline")
    out_dir = FIGURES_DIR / "gjp"
    timeline_dir = out_dir / "ifp_timeline"
    save_ifp_timeline_chart(chart, timeline_dir=timeline_dir)
    logger.info(f"Saved IFP timeline to {timeline_dir}")

# %%
