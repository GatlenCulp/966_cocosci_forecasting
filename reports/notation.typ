// notation.typ
//
// Single source of truth for notation used in the HMM writeup + figures.

#import "@preview/physica:0.9.7": *

#let IFPs = $cal(I)$
#let ifp = $i$

#let Belief = $Z$
#let belief = $z$

#let Report = $X$
#let report = $x$

#let trans = $p_(vb(#Belief)_(t + 1) mid(|) vb(#Belief)_(t))$

#let emission = $p_(vb(#Report)_(t) mid(|) vb(#Belief)_(t))$

#let _notation_item(term, desc) = [
  - *#term*: #desc
]

#let notation-reference() = block[
  #set par(spacing: 1em)

  *Conventions*
  #set list(marker: none, indent: 1em, spacing: 0.8em)
  #_notation_item(
    $X, Y$,
    [Uppercase denotes random variables; lowercase denotes realized values (e.g. $Report$ vs. $report$).],
  )
  #_notation_item(
    $vb(x), vb(z)$,
    [Bold denotes a vector / collection across IFPs at a time $t$.],
  )
  #_notation_item(
    $t$,
    [Discrete time index; subscripts indicate time (e.g. $vb(z)_(t)$).],
  )
  #_notation_item(
    $p_(X mid(|) Y) (x | y)$,
    [Conditional probability. We use stationary parameters unless explicitly time-indexed.],
  )

  *Variables and distributions*
  #set list(marker: none, indent: 1em)
  #_notation_item(IFPs, [Set of Individual Forecasting Problems (IFPs).])
  #_notation_item(ifp, [An individual IFP index, with #ifp in #IFPs.])
  #_notation_item(Belief, [Latent belief state of a forecaster.])
  #_notation_item(belief, [Realization of the latent belief state.])
  #_notation_item(Report, [Observed report / forecast derived from the dataset.])
  #_notation_item(report, [Realization of an observed report.])
  #_notation_item(
    trans,
    [Stationary transition distribution over belief states.],
  )
  #_notation_item(
    emission,
    [Stationary emission distribution from belief states to reports.],
  )
]
