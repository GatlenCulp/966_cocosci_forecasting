# Individual Forecasting Problem (IFP)
# Defined in data/dataverse_files/readme.txt
# %%

from enum import Enum
from functools import lru_cache

import pandera.polars as pa
import pandera.typing.polars as pat
import polars as pl
from pydantic import BaseModel, ConfigDict, Field

from coco.config import DATA_DIR, logger

IFP_CSV_PATH = DATA_DIR / "dataverse_files" / "ifps.csv"


class QuestionType(Enum):
    """IFP question type (q_type field).
    They call regular "binomial/multinomial" but it's more like binary/multiple-choice(?)
    cIFP = Conditional IFP, e.g. If Russia invades Ukraine, will NATO respond militarily?
    """

    REGULAR = 0
    CIFP_OPT1 = 1
    CIFP_OPT2 = 2
    CIFP_OPT3 = 3
    CIFP_OPT4 = 4
    CIFP_OPT5 = 5
    ORDERED_MULTINOMIAL = 6


class IFPSchema(pa.DataFrameModel):
    """Schema for Individual Forecasting Problems dataset."""

    ifp_id: str = pa.Field(description="Unique identifier (e.g., '1001-0')")
    q_type: int = pa.Field(ge=0, le=6, description="Question type (see QuestionType enum)")
    q_text: str = pa.Field(description="Full question text")
    q_desc: str = pa.Field(nullable=True, description="Resolution criteria and additional info")
    q_status: str = pa.Field(isin=["closed", "voided"], description="Question status")
    date_start: pl.Date = pa.Field(description="Date question opened")
    date_suspend: pl.Datetime = pa.Field(nullable=True, description="Date question suspended")
    date_to_close: pl.Date = pa.Field(nullable=True, description="Specified end date")
    date_closed: pl.Date = pa.Field(nullable=True, description="Actual resolution date")
    outcome: str = pa.Field(nullable=True, description="Resolved answer ('a'-'e')")
    short_title: str = pa.Field(description="Brief title")
    days_open: int = pa.Field(nullable=True, ge=0, description="Duration question was open")
    n_opts: int = pa.Field(ge=2, le=5, description="Number of answer options")
    options: str = pa.Field(description="Answer options text")

    class Config:  # noqa: D106  # pyright: ignore[reportIncompatibleVariableOverride]
        coerce = True


class IFPs(BaseModel):
    """IFPs dataset wrapper."""

    lf: pl.LazyFrame = Field(description="A pure, static lf")
    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=True)

    @staticmethod
    @pa.check_types
    def _load_raw() -> pat.LazyFrame[IFPSchema]:
        lf = pl.scan_csv(
            IFP_CSV_PATH,
            eol_char="\r",
            null_values=["NA", ""],
            encoding="utf8-lossy",
        )

        lf = lf.with_columns(
            pl.col("date_start").str.to_date("%m/%d/%y"),
            pl.col("date_to_close").str.to_date("%m/%d/%y"),
            pl.col("date_closed").str.to_date("%m/%d/%y"),
            pl.col("date_suspend").str.to_datetime("%m/%d/%y %H:%M", strict=False),
            pl.col("q_status").str.to_lowercase(),
        )

        return IFPSchema.validate(lf)

    @classmethod
    @lru_cache(maxsize=1)
    def load(cls) -> "IFPs":
        """Load and parse the IFPs dataset (cached)."""
        return cls(lf=cls._load_raw())  # pyright: ignore[reportArgumentType]

    def filter_studied(self, lf: pl.LazyFrame | None = None) -> pl.LazyFrame:
        """Filters forecasts based on whether we are considering them in this study.
        In particular: (A) Ignore voided questions and (B) Only look at binary (yes/no) IFPs
        """
        lf = self.lf if lf is None else lf
        return (
            lf.lazy()
            .filter(pl.col("q_status") != "voided")  # Ignore voided questions
            .filter(pl.col("n_opts") == 2)  # noqa: PLR2004
        )

    def simple(self, lf: pl.LazyFrame | None = None) -> pl.LazyFrame:
        """Transform the IFPs into a simplified view with only valid IFPs"""
        lf = self.lf if lf is None else lf
        return (
            self.filter_studied(lf)
            .select(
                [
                    "ifp_id",
                    "short_title",
                    "q_text",
                    "q_desc",
                    "options",
                    "date_start",
                    "date_closed",
                ]
            )
            .sort(["date_start", "date_closed"])
        )


# %%
if __name__ == "__main__":
    from IPython.display import display

    ifps = IFPs.load()
    logger.info("== Raw IFPs")
    display(ifps.lf.collect())

    logger.info("== Simple View (Studied)")
    studied_ifps = ifps.simple().collect()
    with pl.Config(fmt_str_lengths=10_000):
        display(studied_ifps)

    logger.info(f"Reduced number of IFPs from {len(ifps.lf.collect())} to {len(studied_ifps)}")

# %%
