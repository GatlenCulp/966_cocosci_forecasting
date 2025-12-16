# Individual Forecasting Problem (IFP)
# Defined in data/dataverse_files/readme.txt
# %%

import datetime as dt

import pandera.errors as pa_errors
import polars as pl

from coco.config import logger
from coco.gjp.models.ifp import IFPSchema


def test_ifpschema_fails() -> None:
    """Sanity check that IFPSchema rejects invalid rows."""
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
        "n_opts": 2,
        "options": "(a) Yes, (b) No",
    }

    # Make it invalid: schema requires q_status in {"closed", "voided"} and n_opts <= 5.
    # bad["q_status"] = "open"
    # bad["n_opts"] = 6
    bad["ifp_id"] = 0

    df = pl.DataFrame([bad]).with_columns(
        pl.col("date_start").cast(pl.Date),
        pl.col("date_to_close").cast(pl.Date),
        pl.col("date_closed").cast(pl.Date),
        pl.col("date_suspend").cast(pl.Datetime),
    )

    try:
        IFPSchema.validate(df)
    except (pa_errors.SchemaError, pa_errors.SchemaErrors):
        logger.info("ifps schema succeeded in raising an error")
        return

    raise AssertionError("IFPSchema.validate should have raised on invalid data")
