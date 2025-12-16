# %%
from __future__ import annotations

import json
from pathlib import Path

import altair as alt
import polars as pl

from coco.config import FIGURES_DIR, logger
from coco.gjp.models.ifp import IFPs
from coco.gjp.models.survey_fcasts import SurveyForecasts


def plot_forecast_priors_hist(  # noqa: PLR0913
    ifp_id: str,
    *,
    years: tuple[int, ...] | None = None,
    maxbins: int = 20,
    width: int = 220,
    height: int = 180,
    title: str | None = None,
) -> alt.FacetChart:
    """Histogram of user baselines (earliest observed forecasts), faceted by answer option.

    Uses `SurveyForecasts.baselines()` to extract each user's baseline forecast on a question,
    then displays side-by-side histograms (one per `answer_option`).

    Example (an IFP with three options):

        bad = {
        "ifp_id": "6413-0",
        "q_type": 0,
        "q_text": (
            "Will the Kurdistan Regional Government *hold a referendum on national independence "
            "<b>**before 10 June 2015</b>?"
        ),
        "q_desc": (
            "Amidst a backdrop of violence in Iraq, Kurdish leader Masud Barzani has discussed "
            "plans for holding an independence referendum in the region "
            "( http://www.vox.com/2014/8/12/5991425/kurds-iraq-kurdistan-peshmerga, "
            "http://www.rferl.org/content/iraq-kurds-independence-talk-power-play/"
            "25459559.html ). "
            '*The question will resolve as "yes" when credible open source media report that '
            "voting in a referendum has begun. A referendum held in the city of Kirkuk, outside "
            "the Kurdish region, would not count for the purposes of this question. Outcome will "
            "be determined by credible open source media reporting (e.g., Reuters, BBC, AP). If "
            "the resolution criteria are not met, GJP will assume the following as the "
            '"status quo" outcome: the '
            "Kurdistan Regional Government has not held a referendum on national independence."
        ),
        "q_status": "closed",
        "date_start": dt.date(2014, 10, 17),
        "date_suspend": dt.datetime(2015, 6, 9, 9, 0, tzinfo=dt.UTC),
        "date_to_close": dt.date(2015, 6, 9),
        "date_closed": dt.date(2015, 6, 9),
        "outcome": "b",
        "short_title": "Kurdistan Referendum",
        "days_open": 235,
        "n_opts": 3,
        "options": "(a) Yes, (b) No, (C) Depends",
    }

    """
    sf = SurveyForecasts.load(years=years)
    baselines_df = sf.baselines().filter(pl.col("ifp_id") == ifp_id).collect()
    if baselines_df.is_empty():
        msg = f"No baselines found for ifp_id={ifp_id!r}"
        raise ValueError(msg)

    if title is None:
        ifp_meta = (
            IFPs.load().lf.filter(pl.col("ifp_id") == ifp_id).select(["short_title"]).collect()
        )
        if ifp_meta.is_empty():
            title = f"{ifp_id} — Survey baselines"
        else:
            short_title = ifp_meta.item(0, "short_title")
            title = f"{ifp_id} — {short_title} (survey baselines)"

    zoom = alt.selection_interval(bind="scales")

    hist = (
        alt.Chart(baselines_df)
        .transform_bin(
            as_=["bin_start", "bin_end"],
            field="baseline_value",
            bin=alt.Bin(maxbins=maxbins),
        )
        .transform_aggregate(
            n="count()",
            groupby=["answer_option", "bin_start", "bin_end"],
        )
        .mark_bar()
        .encode(
            x=alt.X(
                "bin_start:Q",
                title="Baseline probability",
                scale=alt.Scale(domain=[0, 1]),
            ),
            x2="bin_end:Q",
            y=alt.Y("n:Q", title="Users"),
            color=alt.Color("answer_option:N", legend=None),
            tooltip=[
                alt.Tooltip("answer_option:N", title="Option"),
                alt.Tooltip("n:Q", title="Users"),
                alt.Tooltip("bin_start:Q", title="Bin start", format=".2f"),
                alt.Tooltip("bin_end:Q", title="Bin end", format=".2f"),
            ],
        )
        .properties(width=width, height=height)
        .add_params(zoom)
    )

    chart = (
        hist.facet(
            column=alt.Column(
                "answer_option:N",
                title=None,
                header=alt.Header(labelAngle=0, labelOrient="bottom"),
            )
        )
        .resolve_scale(x="shared", y="shared")
        .properties(title=title)
        .configure_view(strokeWidth=0)
    )

    logger.info(
        "Built baselines histogram for ifp_id={} (n_rows={}, maxbins={})",
        ifp_id,
        len(baselines_df),
        maxbins,
    )
    return chart


def save_forecast_priors_hist_chart(
    chart: alt.TopLevelMixin,
    *,
    hist_dir: str | Path,
    stem: str = "forecast_priors_hist",
) -> None:
    """Save chart JSON spec + PDF to `hist_dir`."""
    hist_dir = Path(hist_dir)
    hist_dir.mkdir(parents=True, exist_ok=True)
    (hist_dir / f"{stem}.vl.json").write_text(json.dumps(chart.to_dict(), indent=2))
    chart.save(hist_dir / f"{stem}.pdf")


def main(
    ifp_id: str = "6413-0",
    *,
    years: tuple[int, ...] | None = None,
    maxbins: int = 20,
) -> alt.FacetChart:
    """Build + save the baselines histogram for a single IFP."""
    chart = plot_forecast_priors_hist(ifp_id, years=years, maxbins=maxbins)
    out_dir = FIGURES_DIR / "gjp" / "forecast_priors_hist" / ifp_id
    save_forecast_priors_hist_chart(chart, hist_dir=out_dir)
    logger.info(f"Saved forecast baselines histogram to {out_dir}")
    return chart


# %%
if __name__ == "__main__":
    from IPython.display import display

    ifp_id = "6413-0"
    logger.info(f"Displaying histogram guesses for {ifp_id=}")
    chart = plot_forecast_priors_hist(ifp_id)
    display(chart)

    out_dir = FIGURES_DIR / "gjp" / "forecast_priors_hist" / ifp_id
    logger.info(f"Saving histogram to {out_dir=!s}")
    save_forecast_priors_hist_chart(chart, hist_dir=out_dir)

# %%
