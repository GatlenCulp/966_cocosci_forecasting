# Survey Forecasts
# Defined in data/dataverse_files/readme.txt
# %%

from enum import Enum
from functools import lru_cache

import pandera.polars as pa
import pandera.typing.polars as pat
import polars as pl
from pydantic import BaseModel, ConfigDict, Field

from coco.config import DATA_DIR, logger
from coco.gjp.models.ifp import IFPs

SURVEY_FCASTS_DIR = DATA_DIR / "dataverse_files"


class ForecastType(Enum):
    """Forecast type (fcast_type field)."""

    NEW = 0  # First forecast on an IFP by a user
    UPDATE = 1  # Subsequent forecast by a user
    AFFIRM = 2  # Update with no change in value
    WITHDRAW = 4  # User withdraws (scoring stops after this date)


class SurveyForecastSchema(pa.DataFrameModel):
    """Schema for survey forecasts dataset."""

    ifp_id: str = pa.Field(description="IFP identifier (e.g., '1004-0')")
    ctt: str = pa.Field(description="User condition assignment code (see readme.txt)")
    cond: int = pa.Field(ge=1, description="Condition number")
    training: str = pa.Field(description="Training condition letter")
    team: str = pa.Field(nullable=True, description="Team ID if applicable")
    user_id: str = pa.Field(description="User identifier")
    forecast_id: int = pa.Field(description="Unique forecast identifier within year")
    fcast_type: int = pa.Field(isin=[0, 1, 2, 4], description="Forecast type (see ForecastType)")
    answer_option: str = pa.Field(description="Answer option ('a'-'e')")
    value: float = pa.Field(ge=0, le=1, description="Probability estimate")
    fcast_date: pl.Date = pa.Field(description="Date of forecast")
    expertise: int = pa.Field(nullable=True, ge=1, le=5, description="Self-rated expertise (1-5)")
    q_status: str = pa.Field(isin=["closed", "voided"], description="Question status")
    viewtime: float = pa.Field(nullable=True, description="Time spent viewing")
    year: int = pa.Field(ge=1, le=4, description="GJP year (1-4)")
    timestamp: pl.Datetime = pa.Field(description="Full timestamp of forecast")

    class Config:  # noqa: D106  # pyright: ignore[reportIncompatibleVariableOverride]
        coerce = True


class SurveyForecasts(BaseModel):
    """Survey forecasts dataset wrapper (lazy)."""

    lf: pl.LazyFrame = Field(description="A pure, static lf")
    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=True)

    @staticmethod
    @pa.check_types
    def _load_single_year(year: int) -> pat.LazyFrame[SurveyForecastSchema]:
        """Load survey forecasts for a single year (lazy)."""
        path = SURVEY_FCASTS_DIR / f"survey_fcasts.yr{year}.csv"
        return pl.scan_csv(
            path,
            null_values=["NA", ""],
            infer_schema_length=10000,
            schema_overrides={
                "user_id": pl.String,
                "team": pl.String,
                "forecast_id": pl.Float64,  # Some values in scientific notation
                "viewtime": pl.Float64,
            },
        ).with_columns(
            pl.col("forecast_id").cast(pl.Int64),
            pl.col("fcast_date").str.to_date("%Y-%m-%d"),
            pl.col("timestamp").str.to_datetime("%Y-%m-%d %H:%M:%S"),
            pl.col("q_status").str.to_lowercase(),
        )  # pyright: ignore[reportReturnType]

    @classmethod
    @lru_cache(maxsize=1)
    def load(cls, years: tuple[int, ...] | None = None) -> "SurveyForecasts":
        """Load survey forecasts (cached).

        Args:
            years: Tuple of years to load (1-4). Defaults to all years.
        """
        if years is None:
            years = (1, 2, 3, 4)

        lfs = [cls._load_single_year(y) for y in years]
        lf = pl.concat(lfs)
        lf = SurveyForecastSchema.validate(lf)
        return cls(lf=lf)  # pyright: ignore[reportArgumentType]

    def filter_studied(self, lf: pl.LazyFrame | None = None) -> pl.LazyFrame:
        """Filters forecasts based on whether they are valid/being studied.
        Specifically: Do they come from a valid IFP? Baselines are done later.
        """
        lf = self.lf if lf is None else lf
        return lf.join(IFPs.load().filter_studied(), on="ifp_id", how="inner")

    def simple(self, lf: pl.LazyFrame | None = None) -> pl.LazyFrame:
        """Create a simple view of the survey forecasts."""
        lf = self.filter_studied(lf)
        if timestamp_present := "timestamp" in lf.schema:
            lf = lf.sort("timestamp")
        return lf.select(
            [
                "forecast_id",
                "ifp_id",
                "user_id",
                "fcast_type",
                "answer_option",
                "value",
                "timestamp" if timestamp_present else "fcast_date",
            ]
        )

    def user_forecast_counts(self, lf: pl.LazyFrame | None = None) -> pl.LazyFrame:
        """Returns a table of users and their number of forecasts."""
        return (
            self.filter_studied(lf)
            .group_by("user_id")
            .len()  # number of rows (forecasts) per user
            .sort("len", descending=True)
        )

    def most_active_user_id(self, lf: pl.LazyFrame | None = None) -> str:
        """Returns the id of the most active user"""
        return self.user_forecast_counts(lf).select("user_id").limit(1).collect().item()

    def baselines(self, lf: pl.LazyFrame | None = None) -> pl.LazyFrame:
        """Calculate baseline forecasts (users' earliest observed forecasts).

        Notes:
            The dataset includes a `fcast_type` field with a `NEW` value intended to mark a
            user's first forecast on a question. In practice, some users appear to have only
            UPDATE/AFFIRM/WITHDRAW rows (no `NEW` rows). To avoid silently dropping those
            users, we define a user's baseline as their earliest observed forecast per
            (`ifp_id`, `user_id`, `answer_option`) after sorting by available time fields.
        """
        lf = self.filter_studied(lf)

        cols = lf.collect_schema().names()
        required = {"ifp_id", "user_id", "answer_option", "value"}
        if missing := required - set(cols):
            msg = f"Missing required columns: {sorted(missing)}"
            raise ValueError(msg)

        # Prefer high-resolution ordering if available
        order_by = [col for col in ["timestamp", "fcast_date", "forecast_id"] if col in cols]
        base = lf.select(["ifp_id", "user_id", "answer_option", "value", *order_by])

        if order_by:
            base = base.sort(order_by)

        aggs = [
            pl.col(col).first().alias(f"baseline_{col}")
            for col in ["value", "timestamp", "fcast_date"]
            if col in cols
        ]

        return base.group_by(["ifp_id", "user_id", "answer_option"]).agg(aggs)

    def baseline_p_a(self, lf: pl.LazyFrame | None = None) -> pl.LazyFrame:
        """Baseline per (ifp_id, user_id) as p(answer_option="a") for binary questions.

        Since both "a" and "b" are always recorded for binary questions, we can simply
        filter to `answer_option == "a"` and take the earliest observed row per
        (`ifp_id`, `user_id`) (after sorting by available time fields).
        """
        lf = self.filter_studied(lf)

        cols = lf.collect_schema().names()
        required = {"ifp_id", "user_id", "answer_option", "value"}
        if missing := required - set(cols):
            msg = f"Missing required columns: {sorted(missing)}"
            raise ValueError(msg)

        order_by = [col for col in ["timestamp", "fcast_date", "forecast_id"] if col in cols]
        base = lf.filter(pl.col("answer_option") == "a").select(
            ["ifp_id", "user_id", "value", *order_by]
        )
        if order_by:
            base = base.sort(order_by)

        return (
            base.group_by(["ifp_id", "user_id"])
            .agg(pl.col("value").first().alias("baseline_p_a"))
            .select(["user_id", "ifp_id", "baseline_p_a"])
        )

    def agg_baselines(self, lf: pl.LazyFrame | None = None) -> pl.LazyFrame:
        """Aggregate baseline forecasts per IFP/option across users."""
        return (
            self.baselines(lf)
            .group_by(["ifp_id", "answer_option"])
            .agg(
                pl.col("baseline_value").mean().alias("avg_baseline"),
                pl.col("baseline_value").median().alias("median_baseline"),
                pl.col("user_id").n_unique().alias("n_users"),
            )
            .sort(["ifp_id", "answer_option"])
        )


# %%
if __name__ == "__main__":
    from IPython.display import display

    sf = SurveyForecasts.load()
    logger.info("== Raw Survey Forecasts")
    display(sf.lf.collect())

    logger.info("== Studied Survey Forecasts")
    studied_forecasts = sf.filter_studied().collect()
    display(studied_forecasts)
    logger.info(
        f"Reduced number of forecasts from {len(sf.lf.collect())} to {len(studied_forecasts)}"
    )
    # logger.info(f"Years: {studied_forecasts['year'].unique().sort().to_list()}")
    # logger.info(f"Forecasts by year:\n{studied_forecasts.group_by('year').len().sort('year')}")
    logger.info(f"Unique users: {studied_forecasts['user_id'].n_unique()}")

    logger.info("== Baselines (Post-Filter)")
    display(baselines := sf.baselines().collect())
    logger.info("Note that there is an entry for every answer option")
    display(baselines.sort(["user_id", "ifp_id", "answer_option"]))

    logger.info("== Aggregated Baselines (Post-Filter)")
    display(sf.agg_baselines().collect())

    logger.info('== Baseline Pr(answer_option="a") (Post-Filter)')
    display(sf.baseline_p_a().collect())

    logger.info("== User Forecast Counts (Post-Filter)")

    logger.info(f"Most active user: {sf.most_active_user_id()}")
    display(sf.user_forecast_counts().collect())


# %%
