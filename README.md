# MIT 9.66 Final Project: Modeling Belief Perseverance in Geopolitical Forecasting

**Author:** Gatlen Culp (gculp@mit.edu)
**Project Type:** Self-Selected Project

[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)

---

## 00 Table of Contents

- [01 Project Overview](#01-project-overview)
- [02 Getting Started](#02-getting-started)
  - [02.01 Prerequisites](#0201-prerequisites)
  - [02.02 Installation](#0202-installation)
- [03 Repository Structure](#03-repository-structure)
- [04 Data](#04-data)
- [05 Running the Code](#05-running-the-code)
- [06 Reproducing Results](#06-reproducing-results)
- [07 Key Files](#07-key-files)
- [08 Author Notes](#08-author-notes)

---

## 01 Project Overview

This project investigates how individuals update their beliefs when forecasting geopolitical events using the Good Judgement Project (GJP) dataset containing 888,328 forecasts made between 2011-2015.

**Research Question:** When people forecast whether events will occur, how does this affect their beliefs about other related events they have yet to consider? Does the order in which they consider events create belief perseverance?

**Approach:** Model forecasters' belief updates using Hidden Markov Models with MCMC-based limited sampling, inspired by the "burn-in bias" framework from Lieder et al. (2012).

**Key Contributions:**
- Analysis of 382 binary IFPs from the GJP survey forecast dataset
- Visualization tools for temporal forecasting patterns
- Benchmark framework for evaluating cognitive models of human forecasting

See `reports/final-report/final-report.pdf` for the complete paper.

---

## 02 Getting Started

### 02.01 Prerequisites

- Python >= 3.12
- [uv](https://github.com/astral-sh/uv) package manager (recommended) or pip
- Typst (optional, for compiling reports)

### 02.02 Installation

**Clone the repository:**

```bash
git clone https://github.com/GatlenCulp/966_cocosci.git
cd 966_cocosci
```

**Install dependencies:**

Using uv (recommended):
```bash
uv sync
```

---

## 03 Repository Structure

```
📁 .
├── 📁 coco/                    <- Source code package
│   ├── config.py               <- Configuration and logging setup
│   └── gjp/                    <- Good Judgement Project analysis
│       ├── models/             <- Data models and processing
│       │   ├── ifp.py          <- Individual Forecasting Problem models
│       │   └── survey_fcasts.py <- Survey forecast models
│       └── viz/                <- Visualization code
│           ├── plot_forecasts_hist.py
│           ├── plot_ifp_timeline.py
│           └── plot_user_timeline.py
├── 📁 notebooks/               <- Jupyter notebooks for analysis
│   └── 0.1-gcc-ifp.ipynb       <- Main exploratory analysis
├── 📁 reports/                 <- Final report and figures
│   ├── final-report/
│   │   ├── final-report.typ    <- Source (Typst format)
│   │   └── final-report.pdf    <- Compiled report
│   ├── figures/gjp/            <- Generated visualizations
│   └── 966_cocosci.bib         <- Bibliography
├── 📁 tests/                   <- Unit tests
├── pyproject.toml              <- Project dependencies
└── README.md                   <- This file
```

---

## 04 Data

The project uses the Good Judgement Project survey forecast dataset. Raw data files are not included in this repository but may be found here: https://dataverse.harvard.edu/dataverse/gjp. Download it and move it to `$PROJ_ROOT/data/dataverse_files`


**Expected data location:** Data should be placed according to paths in `coco/config.py`

**Data processing:** 
- IFP (question) data: `coco/gjp/models/ifp.py`
- Survey forecast data: `coco/gjp/models/survey_fcasts.py`

---

## 05 Running the Code

**Main analysis notebook:**
```bash
jupyter notebook notebooks/0.1-gcc-ifp.ipynb
```

**Generate visualizations:**

```python
from coco.gjp.viz import plot_ifp_timeline, plot_user_timeline, plot_forecasts_hist

# Generate IFP timeline
plot_ifp_timeline()

# Generate user timeline for specific user
plot_user_timeline(user_id=3257)

# Generate forecast distribution histogram
plot_forecasts_hist(ifp_id="6413-0")
```

---

## 06 Reproducing Results

To reproduce the figures in the final report:

1. Ensure data is properly located (see [04 Data](#04-data))
2. Run the main notebook: `notebooks/0.1-gcc-ifp.ipynb`
3. Figures will be generated in `reports/figures/gjp/`

Key figures:
- **IFP Timeline:** Shows all 382 binary IFPs over time
- **User Timelines:** Individual forecasting behavior over time
- **Forecast Distributions:** Prior distributions for specific IFPs

---

## 07 Key Files

**For TAs reviewing the project:**

| File | Purpose |
|------|---------|
| `reports/final-report/final-report.pdf` | **Main deliverable** - complete paper |
| `notebooks/0.1-gcc-ifp.ipynb` | Primary analysis and exploration |
| `coco/gjp/models/ifp.py` | IFP data models and filtering logic |
| `coco/gjp/viz/plot_ifp_timeline.py` | Timeline visualization (Figure 2 in paper) |
| `reports/figures/gjp/` | All generated figures |

---

## 08 Author Notes

**Author Contributions:** This project was my original idea, heavily inspired by the book *Superforecasting*. I am an MIT Undergraduate and received no outside assistance. This is not related to any of my other work.

**Fresh Repo:** I keep the majority of my coursework into individual GitHub repos. Unfortunately GitHub repos can only be private or public but not unlisted. Because my original repo also contained all my coursework, I had to move my final-project specific code into a fresh repo.

**Questions?** Contact gculp@mit.edu

---

**Project Template:** This project uses [Gatlen's Opinionated Template (GOTem)](https://github.com/GatlenCulp/gatlens-opinionated-template)

_This README was generated by Claude 4.5 Sonnet_