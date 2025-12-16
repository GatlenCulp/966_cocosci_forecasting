# %%
from __future__ import annotations

import json
from pathlib import Path

import altair as alt
import polars as pl

from coco.config import FIGURES_DIR, logger
from coco.gjp.models.ifp import IFPs
from coco.gjp.models.survey_fcasts import SurveyForecasts

# Stage 3: Color bars by correctness (green/red) and set saturation by
# confidence (higher saturation = higher confidence).


def plot_user_timeline(  # noqa: PLR0913
    ifps_lf: pl.LazyFrame,
    *,
    user_id: str | None = None,
    years: tuple[int, ...] | None = None,
    title: str | None = None,
    width: int = 800,
    height: int = 800,
    short_title_regex: str | None = None,
) -> tuple[alt.LayerChart, str]:
    """Timeline of IFP open/close periods for questions a user forecasted on.

    Stage 1: filter the timeline down to only the set of `ifp_id`s for which the
    given user made a *baseline* forecast (their earliest observed forecast) as returned by
    `SurveyForecasts.baselines()`.

    Stage 2: sort questions by the time the user first forecasted on them, and
    overlay a dot at that timestamp with the user's baseline forecast shown in the
    tooltip.

    Returns:
        (chart, resolved_user_id)
    """
    sf = SurveyForecasts.load(years=years)
    if user_id is None:
        counts_df = (
            sf.baselines()
            .group_by("user_id")
            .len()
            .sort("len")  # ascending
            .select(["user_id", "len"])
            .collect()
        )
        # Pick someone near the top
        n_users = len(counts_df)
        mid_idx = max(0, min(n_users - 1, int(0.8 * n_users)))
        resolved_user_id = counts_df.select(pl.col("user_id").slice(mid_idx, 1)).item()
    else:
        resolved_user_id = user_id

    baselines_lf = sf.baselines().filter(pl.col("user_id") == resolved_user_id)
    ifp_ids_lf = baselines_lf.select("ifp_id").unique()

    # NOTE: Building the display string inside a lazy expression has caused
    # version-specific Polars issues (list/struct conversion errors). We keep the
    # heavy lifting lazy, but compute the per-IFP "baseline forecast" tooltip string
    # eagerly for this one user (small table), then join it back in.
    baselines_df = baselines_lf.select(
        [
            "ifp_id",
            "answer_option",
            "baseline_value",
            "baseline_timestamp",
            "baseline_fcast_date",
        ]
    ).collect()

    baselines_summary_df = (
        baselines_df.group_by("ifp_id")
        .agg(
            pl.col("baseline_timestamp").min().alias("baseline_timestamp"),
            pl.col("baseline_fcast_date").min().alias("baseline_fcast_date"),
            pl.struct(["answer_option", "baseline_value"])
            .sort_by("answer_option")
            .alias("_pairs"),
            pl.col("baseline_value").max().alias("baseline_top_prob"),
            pl.col("answer_option")
            .sort_by(pl.col("baseline_value"), descending=True)
            .first()
            .alias("baseline_top_option"),
        )
        .with_columns(
            pl.coalesce(
                pl.col("baseline_timestamp"),
                pl.col("baseline_fcast_date").cast(pl.Datetime),
            ).alias("baseline_time"),
            pl.col("_pairs")
            .list.eval(
                pl.concat_str(
                    [
                        pl.element().struct.field("answer_option"),
                        pl.lit(": "),
                        pl.element().struct.field("baseline_value").round(3).cast(pl.String),
                    ]
                )
            )
            .list.join(", ")
            .alias("baseline_forecast"),
        )
        .select(
            [
                "ifp_id",
                "baseline_time",
                "baseline_forecast",
                "baseline_top_option",
                "baseline_top_prob",
            ]
        )
    )
    baselines_summary_lf = baselines_summary_df.lazy()

    lf = (
        ifps_lf.filter(pl.col("q_status") == "closed")
        .join(ifp_ids_lf, on="ifp_id", how="inner")
        .join(baselines_summary_lf, on="ifp_id", how="inner")
        .select(
            [
                "ifp_id",
                "short_title",
                "date_start",
                "date_closed",
                "outcome",
                "baseline_time",
                "baseline_forecast",
                "baseline_top_option",
                "baseline_top_prob",
            ]
        )
        .with_columns(
            (pl.col("baseline_top_option") == pl.col("outcome")).alias("is_correct"),
            pl.col("baseline_top_prob").alias("confidence"),
        )
        .sort(["baseline_time", "date_start", "date_closed", "ifp_id"])
    )
    if short_title_regex is not None:
        lf = lf.filter(pl.col("short_title").str.contains(short_title_regex))

    timeline_df = lf.with_row_index("y_idx").collect()
    if timeline_df.is_empty():
        msg = f"No baseline forecasts found for user_id={resolved_user_id!r}"
        raise ValueError(msg)

    if title is None:
        title = f"User {resolved_user_id} — IFP timeline (Open → Closed)"

    base = alt.Chart(timeline_df)

    # If we keep a fixed pixel height while `n_ifps` grows, the band/linear spacing
    # collapses and bars/labels overlap. Scale height with the number of rows.
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
        color=alt.Color(
            "is_correct:N",
            scale=alt.Scale(
                domain=[True, False],
                range=["#2ca02c", "#d62728"],
            ),
            legend=alt.Legend(title="Correct?"),
        ),
        opacity=alt.Opacity(
            "confidence:Q",
            scale=alt.Scale(domain=[0, 1], range=[0.2, 1.0]),
            legend=alt.Legend(title="Confidence"),
        ),
        tooltip=[
            alt.Tooltip("ifp_id:N", title="IFP"),
            alt.Tooltip("short_title:N", title="Title"),
            alt.Tooltip("date_start:T", title="Opened"),
            alt.Tooltip("date_closed:T", title="Closed"),
            alt.Tooltip("outcome:N", title="Outcome"),
            alt.Tooltip("is_correct:N", title="Correct?"),
            alt.Tooltip("confidence:Q", title="Confidence", format=".3f"),
        ],
    )

    labels = base.mark_text(align="left", dx=3, fontSize=8, color="white").encode(
        x="date_start:T",
        y=y_enc,
        text="short_title:N",
    )

    dots = base.mark_point(filled=True, size=60, stroke="black").encode(
        x=alt.X("baseline_time:T", title=None),
        y=y_enc,
        color=alt.Color(
            "is_correct:N",
            scale=alt.Scale(
                domain=[True, False],
                range=["#2ca02c", "#d62728"],
            ),
            legend=None,
        ),
        opacity=alt.Opacity(
            "confidence:Q",
            scale=alt.Scale(domain=[0, 1], range=[0.2, 1.0]),
            legend=None,
        ),
        tooltip=[
            alt.Tooltip("ifp_id:N", title="IFP"),
            alt.Tooltip("short_title:N", title="Title"),
            alt.Tooltip("baseline_time:T", title="Baseline forecast time"),
            alt.Tooltip("baseline_top_option:N", title="Top option"),
            alt.Tooltip("baseline_top_prob:Q", title="Top prob", format=".3f"),
            alt.Tooltip("baseline_forecast:N", title="Baseline forecast"),
            alt.Tooltip("date_start:T", title="Opened"),
            alt.Tooltip("date_closed:T", title="Closed"),
            alt.Tooltip("outcome:N", title="Outcome"),
            alt.Tooltip("is_correct:N", title="Correct?"),
        ],
    )

    zoom_x = alt.selection_interval(bind="scales", encodings=["x"])
    zoom_y = alt.selection_interval(bind="scales", encodings=["y"])

    chart = (
        (bars + labels + dots)
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

    logger.info(
        "Built user timeline for user_id={} (n_ifps={})",
        resolved_user_id,
        len(timeline_df),
    )
    return chart, resolved_user_id


def save_user_timeline_chart(
    chart: alt.TopLevelMixin,
    *,
    timeline_dir: str | Path,
    stem: str = "user_timeline",
) -> None:
    """Save chart JSON spec + PDF to `timeline_dir`."""
    timeline_dir = Path(timeline_dir)
    timeline_dir.mkdir(parents=True, exist_ok=True)
    (timeline_dir / f"{stem}.vl.json").write_text(json.dumps(chart.to_dict(), indent=2))
    chart.save(timeline_dir / f"{stem}.pdf")


def main(*, user_id: str | None = None, years: tuple[int, ...] | None = None) -> alt.LayerChart:
    """Build + save the Stage 1-2 user timeline chart."""
    ifps = IFPs.load()
    chart, resolved_user_id = plot_user_timeline(ifps.lf, user_id=user_id, years=years)

    out_dir = FIGURES_DIR / "gjp" / "user_timeline" / resolved_user_id
    save_user_timeline_chart(chart, timeline_dir=out_dir)
    logger.info(f"Saved user timeline to {out_dir}")
    return chart


# %%
if __name__ == "__main__":
    from IPython.display import display

    from coco.gjp.models.ifp import IFPs

    sf = SurveyForecasts.load()

    logger.info("== User Timeline Plot")
    chart = main()
    display(chart)

# %%
