# %%
from pathlib import Path

import altair as alt
import polars as pl

from coco.config import FIGURES_DIR, logger
from coco.gjp.models.ifp import IFPs
from coco.gjp.models.survey_fcasts import SurveyForecasts

# %%


def _select_ifps(
    baseline_p_a_df: pl.DataFrame,
    *,
    first_k: int | None,
    sort_by: str,
    min_n: int = 2,
    min_unique: int = 2,
) -> list[str]:
    """Select IFP IDs with enough observations and variance."""
    if sort_by not in {"ifp_id", "n"}:
        msg = f"sort_by must be one of {{'ifp_id', 'n'}}, got {sort_by!r}"
        raise ValueError(msg)

    df = (
        baseline_p_a_df.group_by("ifp_id")
        .agg(
            pl.col("baseline_p_a").drop_nulls().len().alias("n"),
            pl.col("baseline_p_a").n_unique().alias("n_unique"),
        )
        .filter(pl.col("n") >= min_n)
        .filter(pl.col("n_unique") >= min_unique)
    )
    df = df.sort(sort_by, descending=(sort_by == "n"))
    s = df.select("ifp_id").to_series()
    if first_k is None:
        return s.to_list()
    return s.head(first_k).to_list()


def _pivot_baseline_p_a(
    baseline_p_a_df: pl.DataFrame,
    *,
    first_k: int | None,
    sort_by: str,
    min_n: int = 2,
    min_unique: int = 2,
) -> tuple[list[str], pl.DataFrame]:
    """Select IFPs then pivot baseline probabilities into wide format."""
    ifp_cols = _select_ifps(
        baseline_p_a_df,
        first_k=first_k,
        sort_by=sort_by,
        min_n=min_n,
        min_unique=min_unique,
    )
    if len(ifp_cols) < 2:  # noqa: PLR2004
        msg = f"Need at least 2 IFPs with usable baselines; got {len(ifp_cols)}."
        raise ValueError(msg)

    pivot_df = (
        baseline_p_a_df.filter(pl.col("ifp_id").is_in(ifp_cols))
        .pivot(
            values="baseline_p_a",
            index="user_id",
            on="ifp_id",
            aggregate_function="first",
        )
        .sort("user_id")
    )
    if pivot_df.is_empty():
        msg = "No baseline forecasts available to compute correlations."
        raise ValueError(msg)

    return ifp_cols, pivot_df


def _corr_long_with_r2(pivot_df: pl.DataFrame, ifp_cols: list[str]) -> pl.DataFrame:
    """Compute long-form correlations with corr^2 attached as r2."""
    return _corr_long(pivot_df, ifp_cols).with_columns((pl.col("corr") ** 2).alias("r2"))


def _axis_order_by_r2(corr_long: pl.DataFrame) -> list[str]:
    """Axis ordering by each row's strongest corr^2 (excluding diagonal)."""
    return (
        corr_long.filter(pl.col("ifp_id_x") != pl.col("ifp_id_y"))
        .group_by("ifp_id_x")
        .agg(pl.col("r2").max().alias("row_r2_max"))
        .sort("row_r2_max", descending=True)
        .select("ifp_id_x")
        .to_series()
        .to_list()
    )


def _corr_long(pivot_df: pl.DataFrame, ifp_cols: list[str]) -> pl.DataFrame:
    """Compute pairwise correlations into long-form (ifp_id_x, ifp_id_y, corr)."""
    corr_exprs: list[pl.Expr] = [
        pl.corr(x, y).alias(f"{x}::{y}") for x in ifp_cols for y in ifp_cols
    ]
    corr_flat = pivot_df.select(corr_exprs)
    row0 = corr_flat.row(0)
    return pl.DataFrame(
        [
            {
                "ifp_id_x": name.split("::", 1)[0],
                "ifp_id_y": name.split("::", 1)[1],
                "corr": val,
            }
            for name, val in zip(corr_flat.columns, row0, strict=True)
        ]
    )


def _attach_ifp_meta(corr_long: pl.DataFrame, ifps: IFPs) -> pl.DataFrame:
    """Attach IFP short titles for x/y ids."""
    meta = ifps.filter_studied().select(["ifp_id", "short_title"]).collect()
    return corr_long.join(
        meta.rename({"ifp_id": "ifp_id_x", "short_title": "short_title_x"}),
        on="ifp_id_x",
        how="left",
    ).join(
        meta.rename({"ifp_id": "ifp_id_y", "short_title": "short_title_y"}),
        on="ifp_id_y",
        how="left",
    )


def _corr_long_table(  # noqa: PLR0913
    baseline_p_a_df: pl.DataFrame,
    *,
    ifps: IFPs,
    first_k: int | None,
    sort_by: str,
    min_n: int = 2,
    min_unique: int = 2,
) -> tuple[list[str], pl.DataFrame]:
    """Compute long-form correlations (+r2) and attach IFP titles.

    Notes:
        If `first_k is None`, correlations are computed over *all* usable IFPs
        (after `min_n`/`min_unique` filtering). This can be expensive for large numbers
        of IFPs.
    """
    ifp_cols, pivot_df = _pivot_baseline_p_a(
        baseline_p_a_df,
        first_k=first_k,
        sort_by=sort_by,
        min_n=min_n,
        min_unique=min_unique,
    )
    corr_long = _corr_long_with_r2(pivot_df, ifp_cols)
    return ifp_cols, _attach_ifp_meta(corr_long, ifps)


def make_ifp_corr_matrix(
    sf_lf: pl.LazyFrame,
    *,
    title: str = "IFP Correlation Coefficients Matrix",
    width: int = 800,
    height: int = 800,
    first_k: int = 15,
) -> alt.LayerChart:
    """Pairwise correlation coefficient matrix across all IFPs.

    Computes correlations across questions using users' baseline probabilities.
    For binary studied questions, we use each user's *earliest observed forecast row*
    for `answer_option == "a"` (per `ifp_id`, `user_id`) as `p(answer_option="a")`.
    """
    sf = SurveyForecasts.load()
    ifps = IFPs.load()
    baseline_p_a_df = sf.baseline_p_a(sf_lf).collect()

    ifp_cols, corr_long = _corr_long_table(
        baseline_p_a_df,
        ifps=ifps,
        first_k=first_k,
        sort_by="ifp_id",
    )
    n = len(ifp_cols)
    axis_order = _axis_order_by_r2(corr_long)

    cell_px = 12
    resolved_width = max(width, cell_px * n)
    resolved_height = max(height, cell_px * n)

    zoom = alt.selection_interval(bind="scales")
    base = alt.Chart(corr_long)

    heat = base.mark_rect().encode(
        x=alt.X(
            "ifp_id_y:N",
            title=None,
            sort=axis_order,
            axis=alt.Axis(labelAngle=90, labelFontSize=10, labelLimit=60),
        ),
        y=alt.Y(
            "ifp_id_x:N",
            title=None,
            sort=axis_order,
            axis=alt.Axis(labelFontSize=10, labelLimit=60),
        ),
        color=alt.Color(
            "corr:Q",
            title="corr",
            scale=alt.Scale(domain=[-1, 1], scheme="redblue"),
        ),
        tooltip=[
            alt.Tooltip("ifp_id_x:N", title="IFP (row)"),
            alt.Tooltip("short_title_x:N", title="Title (row)"),
            alt.Tooltip("ifp_id_y:N", title="IFP (col)"),
            alt.Tooltip("short_title_y:N", title="Title (col)"),
            alt.Tooltip("corr:Q", title="corr", format=".3f"),
            alt.Tooltip("r2:Q", title="corr^2", format=".3f"),
        ],
    )

    text = base.mark_text(fontSize=10).encode(
        x=alt.X("ifp_id_y:N", sort=axis_order),
        y=alt.Y("ifp_id_x:N", sort=axis_order),
        text=alt.Text("corr:Q", format=".2f"),
        color=alt.condition(
            "datum.r2 > 0.36",
            alt.value("white"),
            alt.value("black"),
        ),
    )

    return (
        (heat + text)
        .properties(title=title, width=resolved_width, height=resolved_height)
        .add_params(zoom)
        .configure_title(fontSize=18)
        .configure_axis(grid=False)
    )


def make_ifp_corr_topk_rows(  # noqa: PLR0913
    sf_lf: pl.LazyFrame,
    *,
    title: str = "Top correlations per IFP (ranked within each row)",
    n_rows: int = 10,
    top_k: int = 10,
    width: int = 900,
    height: int = 700,
) -> alt.LayerChart:
    """Show top correlations per IFP using corr^2, with per-row ordering.

    The x-axis is rank within each row (1..top_k). Each cell shows the correlation
    squared (rounded) and the matching IFP ID underneath. Rows are sorted by max corr^2.
    """
    sf = SurveyForecasts.load()
    ifps = IFPs.load()

    baseline_p_a_df = sf.baseline_p_a(sf_lf).collect()

    base_corr = (
        _corr_long_table(baseline_p_a_df, ifps=ifps, first_k=n_rows, sort_by="n")[1]
        .filter(pl.col("ifp_id_x") != pl.col("ifp_id_y"))
        .filter(pl.col("corr").is_finite())
        .with_columns(pl.col("r2").rank("dense", descending=True).over("ifp_id_x").alias("rank"))
        .filter(pl.col("rank") <= top_k)
    )

    row_score = (
        base_corr.group_by("ifp_id_x")
        .agg(pl.col("r2").max().alias("row_r2_max"))
        .sort("row_r2_max", descending=True)
    )

    corr_long = base_corr.join(row_score, on="ifp_id_x", how="inner").with_columns(
        pl.concat_str(
            [
                pl.col("corr").round(2).cast(pl.String),
                pl.lit("\n"),
                pl.col("ifp_id_y"),
            ]
        ).alias("cell_label")
    )

    y_sort = row_score["ifp_id_x"].to_list()
    zoom = alt.selection_interval(bind="scales")

    base = alt.Chart(corr_long)
    heat = base.mark_rect().encode(
        x=alt.X("rank:O", title="Rank within row (by corr^2)"),
        y=alt.Y("ifp_id_x:N", title=None, sort=y_sort),
        color=alt.Color(
            "corr:Q",
            title="corr",
            scale=alt.Scale(domain=[-1, 1], scheme="redblue"),
        ),
        tooltip=[
            alt.Tooltip("ifp_id_x:N", title="IFP (row)"),
            alt.Tooltip("short_title_x:N", title="Title (row)"),
            alt.Tooltip("ifp_id_y:N", title="IFP (matched)"),
            alt.Tooltip("short_title_y:N", title="Title (matched)"),
            alt.Tooltip("corr:Q", title="corr", format=".3f"),
            alt.Tooltip("r2:Q", title="corr^2", format=".3f"),
        ],
    )
    text = base.mark_text(fontSize=10, lineBreak="\n").encode(
        x=alt.X("rank:O"),
        y=alt.Y("ifp_id_x:N", sort=y_sort),
        text="cell_label:N",
        color=alt.condition("datum.r2 > 0.36", alt.value("white"), alt.value("black")),
    )

    return (
        (heat + text)
        .properties(title=title, width=width, height=height)
        .add_params(zoom)
        .configure_title(fontSize=18)
        .configure_axis(grid=False)
    )


def save_ifp_corr_matrix(chart: alt.TopLevelMixin, *, corr_matrix_dir: str | Path) -> None:
    """Save chart JSON spec + PDF to `timeline_dir`."""
    corr_matrix_dir = Path(corr_matrix_dir)
    corr_matrix_dir.mkdir(parents=True, exist_ok=True)
    # `chart.to_dict()` enforces Altair's max row limit; `chart.save()` disables it by default.
    chart.save(corr_matrix_dir / "corr_matrix.vl.json", format="json", json_kwds={"indent": 2})
    chart.save(corr_matrix_dir / "corr_matrix.pdf")


def corr_pairs_table(  # noqa: PLR0913
    sf_lf: pl.LazyFrame,
    *,
    first_k: int | None = None,
    top_k: int | None = None,
    sort_by: str = "n",
    min_n: int = 2,
    min_unique: int = 2,
) -> pl.LazyFrame:
    """Return correlation pairs table (unique unordered pairs)."""
    sf = SurveyForecasts.load()
    ifps = IFPs.load()

    baseline_p_a_df = sf.baseline_p_a(sf_lf).collect()
    corr_long = _corr_long_table(
        baseline_p_a_df,
        ifps=ifps,
        first_k=first_k,
        sort_by=sort_by,
        min_n=min_n,
        min_unique=min_unique,
    )[1]

    pair_a = (
        pl.when(pl.col("ifp_id_x") <= pl.col("ifp_id_y"))
        .then(pl.col("ifp_id_x"))
        .otherwise(pl.col("ifp_id_y"))
    )
    pair_b = (
        pl.when(pl.col("ifp_id_x") <= pl.col("ifp_id_y"))
        .then(pl.col("ifp_id_y"))
        .otherwise(pl.col("ifp_id_x"))
    )
    title_a = (
        pl.when(pl.col("ifp_id_x") <= pl.col("ifp_id_y"))
        .then(pl.col("short_title_x"))
        .otherwise(pl.col("short_title_y"))
    )
    title_b = (
        pl.when(pl.col("ifp_id_x") <= pl.col("ifp_id_y"))
        .then(pl.col("short_title_y"))
        .otherwise(pl.col("short_title_x"))
    )

    df = (
        corr_long.filter(pl.col("ifp_id_x") != pl.col("ifp_id_y"))
        .filter(pl.col("corr").is_finite())
        .with_columns(
            pair_a.alias("ifp_id_a"),
            pair_b.alias("ifp_id_b"),
            title_a.alias("short_title_a"),
            title_b.alias("short_title_b"),
        )
        .unique(subset=["ifp_id_a", "ifp_id_b"], keep="first")
        .sort("r2", descending=True)
        .select(["ifp_id_a", "short_title_a", "ifp_id_b", "short_title_b", "corr", "r2"])
    )
    if top_k is not None:
        df = df.head(top_k)
    return df.lazy()


# %%
if __name__ == "__main__":
    from IPython.display import display

    sf = SurveyForecasts.load()
    out_dir = FIGURES_DIR / "gjp"

    logger.info("== IFPs Correlations Matrix (10 x 10)")
    corr_matrix_dir = out_dir / "corr_matrix"
    corr_matrix_chart = make_ifp_corr_matrix(sf.lf)
    display(corr_matrix_chart)

    logger.info("== Saving IFP Correlations Matrix")
    save_ifp_corr_matrix(corr_matrix_chart, corr_matrix_dir=corr_matrix_dir)
    logger.info(f"Saved IFP correlation matrix to {corr_matrix_dir}")

    logger.info("== Top IFP correlation pairs (by corr^2; same IFP subset as top-k rows)")
    display(corr_pairs_table(sf.lf, first_k=10, sort_by="n").collect())

    logger.info("== IFPs Top Correlations Per Row")
    corr_topk_dir = out_dir / "corr_topk_rows"
    corr_topk_chart = make_ifp_corr_topk_rows(sf.lf)
    display(corr_topk_chart)

    logger.info("== Saving IFPs Top Correlations Per Row")
    save_ifp_corr_matrix(corr_topk_chart, corr_matrix_dir=corr_topk_dir)
    logger.info(f"Saved IFP top-k correlations chart to {corr_topk_dir}")

# %%
