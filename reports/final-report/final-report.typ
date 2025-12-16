#import "@preview/cogsci-conference:0.1.1": cogsci, format-authors
#import "@preview/physica:0.9.7": *
#import "../notation.typ": *

#show: cogsci.with(
  title: [
    A Hidden Markov Model of Belief Evolution in Geopolitical Forecasting\
    #text(size: 10pt)[_9.66 Self-Selected Project_]
  ],
  author-info: format-authors(
    (
      (name: [Gatlen Culp], email: "gculp@mit.edu"),
    ),
    [Massachusetts Institute of Technology, Undergraduate],
  ),

  abstract: [
    Geopolitical forecasting is a vital tool for world affairs, but is poorly understood as a concept in human psychology. I outline a simple cognitive Markov Chain Model of evolving belief states, wherein one's beliefs evolve according to a individually and  time-invariant transition function. I identify and outline a geopolitical forecasting dataset generated from volunteer reporting and demonstrate that forecasts exhibit measurable cross-question correlations, motivating better understanding of the underlying relationships. After filtering, the dataset contains 382 individual forecasting problems and 323,847 baseline probability reports. To formally study and generate the parameters for this Markov Chain model from the dataset, I propose a method of using volunteer-reported forecasts as noisy observations in a Hidden Markov Model extension of the original. I conclude by proposing train/test split strategies, baselines for evaluating the model, and methods of analysis for understanding abstract evolving beliefs and specific limitations of the simple model.
  ],
  keywords: ("forecasting", "geopolitics", "hidden markov models", "cognitive modeling"),
  anonymize: false,
  hyphenate: true,
)

\
#align(center)[
  *Link to Project Code on GitHub*\
  #link("https://github.com/GatlenCulp/966_cocosci_forecasting")
]
\
= Introduction

Forecasting -- making informed predictions about the future #footnote[Typically on the order of months to years] -- is simultaneously extremely difficult and extremely valuable. Forecasting is used constantly in our personal lives and used professionally by consultants, politicians, analysts, entrepreneurs, and more. Forecasting geopolitical events and responses is critically important for international and domestic peace, prosperity, and stability -- underestimating the likelihood is an error measured in human lives. #footnote[In addition to individual forecasting, there is much room for improvement in group forecasting and communication. E.g. the 2011 Abbottabad raid of the U.S. into Pakistan was rife with miscommunications about the likelihood of Osama bin Laden's location within the country, straining U.S.-Pakistan relations and not completely eliminating al-Qaeda. @tetlockSuperforecastingArtScience2015]

From an evolutionary psychology perspective, forecasting had limited usefulness. Predicting potential personal emergencies (such as hunting accidents) is useful for rationing food preserves and improving fitness, but forecasting more abstract concepts (such as whether China will invade Taiwan or whether Serbia will be officially granted EU candidacy) would rarely improve fitness.

Forecasting is a skill that can be trained like any other, and because modern forecasting problems are far from our evolved niches, the ceiling for human capabilities is likely far beyond our innate ability and much is yet to be known, as evidenced by research volunteers outperforming senior professionals in the U.S. Intelligence Community (IC) #footnote[Consisting of the CIA and FBI among others] after just a year. @tetlockSuperforecastingArtScience2015

One of the most fundamental tools to improve any skill is to understand our current untrained ability to forecast -- downsides, strengths, common mistakes, etc. By understanding our abilities, we can improve forecasting pedagogy and our intuitive understanding of the future.
#footnote[
  Other reasons why understanding human forecasting is interesting: (A) We may be able to build algorithms around it. For example, more efficiently sampling and de-biasing predictions about the future provided by LLMs. (B) Beyond improving forecasting, understanding how others perceive the future (e.g. citizens) may itself be valuable information in forecasting.
]

// To study this, I select 6 related events (e.g. the dataset has 22 related to the North Korean military alone) and represent them on a branching timeline (one branch for yes, one branch for no), ordered by their resolution times. I will then simulate MCMC with limited iterations on the tree for each respondent, representing "thinking about events most closely related to the one they are forecasting" in the style of @liederBurninBiasRationality2012. I will then analyze the effect of this sampling method against forward chaining from the present and through each intermediate event.


In parallel, I formalize an individual's day-by-day forecasting behavior as a Hidden Markov Model: a hidden belief vector over questions evolves over time, and the observed forecasts are noisy, sparse reports of those beliefs. I then evaluate whether this stylized model captures forecasting behavior by fitting it on subsets of each individual's timeline and measuring predictive accuracy on held-out forecasts, comparing against simple baselines (e.g. the collective average) and a collective model fit across forecasters. This sets up an empirical testbed for belief perseverance (resistance to revising beliefs) in sequential, interdependent forecasting.

= Background

Despite the extreme importance of geopolitical forecasting, little research has investigated how humans develop their intuition for the abstract and distant future.

Previous work by the *Good Judgement Project (GJP)* #footnote[_Superforecasting_, written by administrators of GJP, was the main inspiration behind this research project.] in collaboration with the U.S. Intelligence Community collected 888,328 geopolitical forecasts on questions such as _"Will Daniel Ortega win another term as President of Nicaragua during the late 2011 elections?"_ and identified practices, personality traits, and institutional procedures to improve systemic forecasting ability even beyond experts in the CIA, FBI, and more. @friedmanValuePrecisionProbability2018 @tetlockSuperforecastingArtScience2015 While this work explored how experts may improve, it said little about how everyday people make their predictions.

In this paper, I use the dataset of geopolitical forecasts provided by the Good Judgement Project @friedmanValuePrecisionProbability2018.

Previous work by @liederBurninBiasRationality2012 attempted to model the psychological concept of anchoring -- weighting the first piece of evidence more than subsequent pieces -- by using MCMC with a limited number of iterations, and demonstrated that the perceived distribution was different from the steady-state, demonstrating a probability "burn-in" of visited states.
// This limited-sampling framing is a plausible mechanism for belief perseverance in sequential reasoning.

= The Good Judgement Project Dataset

Before introducing any forecasting model, I first describe the subset of the GJP dataset I analyze and show that it contains a measurable dependency structure worth modeling.

The GJP has collected forecasts via both prediction markets and volunteer surveys. For the sake of this research, I limited myself to all four years of the survey forecasts from September 2011 to May 2015.

== Forecasting Problems (IFPs) and Filtering

Each question in the dataset is referred to as an *Individual Forecasting Problem (IFP)*. For two IFP examples, see @fig:ifp-example.
#footnote[To fit this table, a number of columns were removed/combined. An important column is `q_desc`, a 1-2 paragraph-long description containing more information and formal resolution criteria. `q_status` notes whether the IFP was `closed` or `voided`.]


#figure(
  [
    #set text(size: 8pt)
    // #set par(leading: 0.65em)
    #set par(justify: false)

    #table(
      columns: (auto, 7em, 10em, 7em, auto),
      align: (center, left, left, left, center),
      // inset: (x: 5pt, y: 4pt),
      // column-gutter: 8pt,
      // row-gutter: 6pt,
      table.hline(),
      table.header([`ifp_id`], [`short_title`], [`q_text`], [`options`], [dates]),
      table.hline(),

      [1004-0],
      [UN-GA recognize Palestine],
      [Will the United Nations General Assembly recognize a Palestinian state by 30 September 2011?],
      [(a) Yes\ (b) No],
      [2011-09-01\ to\ 2011-09-30],

      [1007-0],
      [confrontation in S. or E. China Sea],
      [Will there be a lethal confrontation involving government forces in the South China Sea or East China Sea by 31 December 2011?],
      [(a) Yes, by 15 October 2011\ (b) Yes, between 16 Oct and 31 Dec\ (c) No],
      [2011-09-01\ to\ 2011-12-11],
    )
  ],
  caption: [Example IFPs from the GJP dataset (simplified)],
) <fig:ifp-example>

To guarantee the validity of my results, I filtered any IFPs labeled `voided`. And for model simplification purposes, later explained in #link(<sec:forecast-models>)[_Forecasting Models_], I limited my analysis to boolean (yes/no) questions.
#footnote[Extension to multiple-choice questions using a different state-space is possible, but unnecessary for analysis.]
This reduced the number of IFPs from $617$ to $382$. @fig:ifp-timeline displays the remaining questions on a timeline.
#footnote[Originally an interactive graph. May be too hard to make out in the paper, but generally useful to understand the structure.]


== Individual Forecasts (Baseline Survey Priors)

Each of the volunteers in the GJP study were assigned a unique and anonymous ID and could make forecasts on IFPs via an online platform during each IFP's window shown in @fig:ifp-timeline. The forecasters would rate the probability of each option as a value between $0$ and $1$.

Because users can update their forecasts on the same IFP, I decided to consider only the first forecast, which I call the "baseline" forecast. Because I had filtered for only boolean IFPs, I was able to reduce the forecasts of an agent $i$ on any IFP to a single value, $Pr["answer"_i = "\"(a) yes\""]$. Unless otherwise noted, consider all forecasts below to be baseline forecasts.
#footnote[
  Only after I had done most of my project had I realized that some of the questions had important conditionals inside of the `outcomes` field instead of in the question text. E.g. "If Parti Quebecois does not hold a majority of seats in the Quebec provincial legislature beforehand :  (a) Yes, (b) No". These conditionals certainly have a large influence on the volunteers' responses which I did not consider in my project. However, because these conditionals $Pr("yes" | "condition")$ are positively correlated with $Pr("yes")$, the results here are not entirely invalid.
  // TODO: Add better wording.
]

After filtering all survey forecasts to include only the baseline and the restricted IFP set, the number of forecasts in this dataset was reduced to
// #footnote[This is more than was mentioned in the paper. I'm not entirely sure why this discrepancy exists but I imagine this might be due to them counting the number of forecasts differently or actually using a subset of the forecasts in their paper.]
$323,847$.

An example of five forecasts can be seen in @fig:survey-fcast-example.
#footnote[As with @fig:ifp-example, a number of columns were omitted, but the ones displayed are the focus of this study.]

#figure(
  [
    #set text(size: 8.5pt)
    // #set par(leading: 0.65em)
    #set par(justify: false)

    #table(
      columns: (auto, auto, 7em, auto, auto),
      align: (center, center, center, center, center),
      table.hline(),
      table.header([`ifp_id`], [`user_id`], [`answer_option`], [`confidence`], [`timestamp`]),
      table.hline(),

      [1340-0], [6324], [a], [0.10], [2014-02-04 10:42:04],
      [1453-0], [23336], [a], [0.15], [2014-10-25 03:43:54],
      [1468-6], [9015], [b], [0.25], [2015-01-14 12:32:09],
      [1221-6], [9219], [d], [0.97], [2014-03-30 17:58:13],
      [1129-2], [2827], [b], [0.95], [2012-08-13 11:16:23],
    )
  ],
  caption: [Example baseline survey forecast priors from the GJP dataset. Each row is a user's first forecast on an IFP for a given answer option.],
) <fig:survey-fcast-example>

In @fig:survey-fcast-timeline, there is an example of a user's complete forecasting profile depicted as a timeline. This user was in the top 80\% most active forecasters after applying the filters mentioned above.


#figure(
  image("/reports/figures/gjp/user_timeline/23066/user_timeline.pdf"),
  caption: [Zoomed-in example of user `23066`'s forecasting timeline. Only IFPs the user submitted a forecast on are shown. The dot on each bar is the forecast timestamp; green/red indicates correct/incorrect; opacity scales with confidence.],
) <fig:survey-fcast-timeline>

== Forecast Correlations

As a preliminary check before doing any dependency-based modeling, I searched for highly correlated (positive or negative) baseline forecasts across IFPs. If forecasts were close to independent across questions, then any modeling based on cross-IFP structure would be poorly motivated. In @fig:corr-topk-rows, you can see the top 10 correlations per IFP.

At first glance, these events seem to have little to do with one another and future research may be interested in exploring the chain of logic or personality/cultural biases by which individuals make these correlated forecasts -- for example, the two most correlated forecasts involve: "Will India and/or Brazil become a permanent member of the U.N. Security Council before 1 March 2015?" and "Will a referendum on Quebec's affiliation with Canada be held before 31 December 2014?". This strong correlation may indicate some underlying personal bias towards or against "cooperation".
#footnote[Principal Component Analysis across forecasters may be an interesting direction.]


#figure(
  image("/reports/figures/gjp/corr_topk_rows/corr_matrix.pdf"),
  caption: [Top correlations per IFP (ranked within each row)],
) <fig:corr-topk-rows>

The top 5 pairs, as displayed below in @fig:corr-topk-table, coincidentally have reasonably high positive correlations, ranging from $0.266$ to $0.325$. This weakly supports using the dependency structure between an individual's forecasts.
#footnote[To compare against generally temporally-similar data, see @fig:corr-matrix in the appendix, showing the correlation coefficient matrix for the first 10 IFPs from the dataset. The values here range from $-0.21$ to $0.28$.
  // Is it a coincidence that 0.28 is in the top five? Also that pairing is NOT in the top five? What is going on?
  // Also, I should really add the counts because this could easily be coincidence -- low number of people that forecasted both A and B and law of large numbers has failed to kick in
]

#figure(
  [
    #set text(size: 8.5pt)
    // #set par(leading: 0.65em)
    #set par(justify: false)

    #table(
      columns: (auto, 8.5em, auto, 10.5em, auto),
      align: (center, left, center, left, right),
      table.hline(),
      table.header([`ifp_id_a`], [`short_title_a`], [`ifp_id_b`], [`short_title_b`], [`corr`]),
      table.hline(),

      [1244-0], [India/Brazil UNSC], [1399-2], [Quebec Referendum], [0.325],
      [1413-0], [Kurdistan Referendum], [1427-0], [Russia annexation of Ukraine], [0.305],
      [1244-0], [India/Brazil UNSC], [1394-0], [China: Second Thomas Shoal], [0.277],
      [1394-0], [China: Second Thomas Shoal], [1413-0], [Kurdistan Referendum], [0.270],
      [1413-0], [Kurdistan Referendum], [1416-0], [North Korea nuclear device], [0.266],
    )
  ],
  caption: [
    Top 5 correlated IFP pairs in the filtered survey forecasts.
    #footnote[Given more time, I would have also liked to examine which IFPs had the most variance and how much the variance of one IFP could explain that of another. The figure here does not tell us much about the differences between individuals.]
  ],
) <fig:corr-topk-table>



= Modeling Forecasts <sec:forecast-models>

Now that we have a better understanding of the data and reason to believe that forecasts are correlated across IFPs, we can go about modeling (and later simulating) how forecasters form and update their predictions. The first step is choosing a representation for the discrete time series of an individual's forecasts. Because we are interested in representing the internal beliefs of the human forecaster and not just representing the forecasts themselves, one promising formalization of this data is as a Hidden Markov Model (HMM) as depicted in @fig:hmm.

For a single forecaster, I write the hidden belief state at time $t$ as $vb(Belief)_t$, where $t$ is a discrete day index measured from the start of the dataset (so $t = 1$ is the day of the first GJP datapoint). Let $IFPs$ be the set of boolean IFPs after filtering. Then $vb(Belief)_t$ is a vector in $[0, 1]^(abs(IFPs))$, Where for $ifp in IFPs$, $Belief_(t, ifp)$ is the forecaster's subjective probability (on day $t$) that IFP $ifp$ will resolve to "Yes".

Because the forecaster's mind cannot be read directly, the belief state must be inferred from the forecasts they submitted. I therefore represent the forecast at time $t$ as $vb(Report)_t$, a vector with the same indexing as $vb(Belief)_t$. When a forecaster submits a forecast on day $t$ for IFP $ifp$, the value $Report_(t, ifp)$ represents the reported probability that the forecaster assigns to "Yes". Let lowercase variables represent the realized values of their uppercase counterparts. When they do *not* submit a forecast for $ifp$ on day $t$, that coordinate is unobserved, which I encode as $report_(t, ifp) = -1$.

For simplicity, I assume a stationary HMM (both the belief transitions and the reporting emissions are time-independent), with *transition* distribution $trans(dot | dot)$ and *emission* distribution $emission(dot | dot)$ (see the #link(<app:notation-ref>)[Notation Reference]). I also do not attempt to model exogenous information (e.g. reading the news) which may be represented (albeit at a lower resolution) in the hidden belief transitions.

// TODO: A more general formalization? E.g. can represent anything.

#figure(
  image("../figures/cogsci/hmm/hmm.pdf"),
  caption: [
    Hidden Markov Model. The initial dot represents that the individual's background (provided in the GJP dataset) may be used to help configure their priors $vb(Belief)_0$, which we do not do here.
  ],
) <fig:hmm>

We can additionally assume that forecasters are simply report their hidden beliefs from a tight normal distribution ($sigma = 0.05$), clamped by the probability range $[0, 1]$ and with a mean around their actual hidden belief and the forecasts they decide to make at time $t$ are independent of their internal beliefs (e.g. we ignore that individuals may be more likely to make forecasts on IFPs they have greater certainty on). Mathematically:
$
  emission(report_(t, ifp) mid(|) belief_(t, ifp)) =
  cases(
    // TODO: Update to represent sampling from the normal distribution.
    1 & "if" report_(t, ifp) = -1,
    1 & "if" report_(t, ifp) = belief_(t, ifp),
    0 & "otherwise",
  )
$

The last thing to do now would be to learn the transitions probabilities $trans$ and the prior (initial belief-state) $vb(Belief)_0$. Which can be done using the Baum-Welch (Forward-Backward) Algorithm. @devijverBaumsForwardbackwardAlgorithm1985 We can start a uniform prior and identical transition probabilities:
$
  vb(Belief)_0 <- [1 slash 2, dots.c, 1 slash 2]^TT, \ trans(vb(belief)_(t+1) mid(|) vb(belief)_t) <- cases(1 "if" z_(t+1) = z_t, 0 "otherwise")
$
For the individual, the emissions distribution will simply be learned to be a normal distribution with the mean of the observation.
// #footnote[If one had the goal to make _accurate_ forecasts (not necessarily ones reflecting human cognition), then instead one could represent the hidden states $vb(Belief)_t$ as "states of the world" and the observations $vb(Report)_t$ as]

// However, with only a single individual forecaster, we have only a single sample, which is extremely difficult to develop a robust model of forecasting for.

After developing an HMM model from the forwards-backwards algorithm for an individual, we can then also develop another HMM algorithm for the collective set of forecasts to compare against, treating each individual forecast as if they come from the same, unknown distribution.
// TODO: Check if this is right.
#footnote[We could also use the correlation coefficient matrix as a transition function and renormalize after each step.]

= Evaluating Models <sec:model-evaluation>

// We would like to determine whether humans make forecasting decisions in a similar fashion to this model. More specifically this model entails that humans have a prior over world events. Over-time, these beliefs interact with one another in time-consistent ways to develop new beliefs, and that this dynamic is entirely isolated from external events and information. While this is an extremely primitive view of how people develop their view of the future, it may be an extremely valuable starting point for future research -- for example, much of the field of economics was founded on developing models for decision making and the economy, analyzing where they fall apart, developing more sophisticated models, and developing an understanding of the limitations and unknowns of any one view point.

There are a few ways we can evaluate this model using the GJP dataset, by combining (A) all of the train / test splits below with any of the (B) evaluation metrics also found below. The "_dataset_" referenced here is the _set of forecasts made by the individual_ that the model was fit to. Each of these should be repeated across all users and the distribution of results should be analyzed.

== (A) Train/Test Split Strategies

For any of the train/test splits below, we fit our model with the forwards-backwards algorithm only using the training data and evaluate it based on the witheld testing data.
1. *Randomized Split*: Select a random $x%$ of the available forecasts to include in training, the rest become part of the testing set. This is meant to evaluate overall quality of our model
2. *Temporal Cut-Off Split*: Select a time $tau$ as the stopping point. Everything before is used for training, everything after is used for testing. This is meant to evaluate our stationary-transition condition -- being able to successfully forecast a long and uninterrupted sequence of events would be positive evidence that a stationary-transition assumption is reasonable.
3. *Time-Interval Split*: Select a start and end time such that $1 < tau_"start" < tau_"end" < abs("dataset")$. This is meant to contrast against the temporal cut-off split -- just how much prediction accuracy is gained by knowing forecasts in the far future? If similarly sized train/test splits have higher accuracy in this split than the cut-off split and the stationary-transition assumption appears false, then this is positive evidence for a predictably evolving belief transition function -- i.e. evidence as time progresses, the way beliefs "interact" in your head to form new ideas and beliefs mutates slowly and continuously.

== (B) Evaluation Metrics

Both of these metrics should be used and compared with one another. After a model is fit using the training data, the following are measured on the testing data. *Accuracy* here is defined to be the average squared error across model-predictions. E.g. if the model predicts a user's belief state of ifp $i$ and $j$ to be $0.25$ at time $t$ but they had actually reported $0.75$ and $0.5$ at time $t$ respectively, then the *error* of that prediction is defined to be the euclidean distance between the predicted and true forecasts, in this instance: $sqrt((0.75 - 0.25)^2 + (0.5 - 0.25)^2)$.
1. *Collective-Average Prediction Accuracy*: As a baseline statistic -- what is the accuracy of predicting that the forecaster will make a forecast on every IFP equal to the average over the collective forecasts of all users?
2. *Collective-Model Prediction Accuracy*: If we were to use the HMM that fit to the collective predictions across all users -- what is the accuracy?
3. *Individual-Model Prediction Accuracy*: If we were then to use the individually-fitted model, how much better does it perform than the collective-model? If the accuracy is much better, this is positive evidence for there being strong differences between how individuals make forecasts.


= Conclusion

In this paper, I introduce the importance of further developing the field of computational cognitive science in understanding how humans develop their beliefs about the future and forecast geopolitical events as a starting point for developing better forecasting algorithms and practices. I identify and outline a promising dataset by the Good Judgement Project to further develop this research. And I design a simple Hidden Markov Model algorithm, parameter-fitting process, evaluation procedure, and methods of analysis that may be used to understand this topic in depth.

While I did not have the time to implement my procedure and collect data due to spending a considerable amount of time parsing, filtering, and understanding the GJP dataset that I had plan to fit and test my model on, I believe this project is in line with the spirit of computational modeling and analysis that was focused on in the majority of the 9.66 Computational Cognitive Science class.



= Appendix

== Original Scope

For context, here is some information about the original scope of my project:

An important starting point is understanding not just how individuals update their beliefs in response to new information, but how individuals update their beliefs as they think more about the future. In particular, I decided to model the following: when people forecast whether or not an event will occur in the future, how does this affect their beliefs about other events they have yet to consider? And does the order in which they consider these events "stick", or become hard to change? If they believe a far-off event is likely to occur, might they be averse to revising their belief even as they later consider related events happening beforehand?
#footnote[For example, I have been talking with people about the consequences of advanced AI up to and including superintelligent AI before ChatGPT was released. I find that many people find it improbable, not from forward-chaining events from today but from some bias towards a future that they are familiar with, and backwards-chain from that future to discount the probability of a much crazier future (may be an availability heuristic)]

I had intended to simulate MCMC with limited iterations, representing "thinking about events most closely related to the one they are forecasting" in the style of @liederBurninBiasRationality2012. Then analyze the effect of this sampling method against forward chaining from the present and through each intermediate event.

== IFP Timeline

#figure(
  image("../figures/gjp/ifp_timeline/ifp_timeline.pdf", fit: "contain", height: 550pt),
  caption: [Timeline of all IFPs. The x-axis is time. Each horizontal bar represents an IFP: the left end is when it opened for forecasts and the right end is when it closed, either by deadline (e.g. "Will the city of Kiev be bombed by Russia by Nov 11th, 2012?") or by resolution (e.g. if Russia bombed Kiev on Oct 11th, 2012).],
  // TODO: Give this plot more vertical spacing and vertical zoom. Remove labels for readability.
) <fig:ifp-timeline>

== Arbitrary Correlation Coefficients Matrix

#figure(
  image("/reports/figures/gjp/corr_matrix/corr_matrix.pdf"),
  caption: [Correlation coefficient matrix for the first 10 IFPs. Meant as a point of comparison between strongly correlated forecasts and those that may be correlated mainly due to temporal proximity.],
) <fig:corr-matrix>

= Notation Reference <app:notation-ref>

// Notation is defined in `reports/notation.typ`.
#notation-reference()

= Notes for 9.66 Staff

*Author Contributions*: This project was my original idea, heavily inspired by the book _Superforecasting_. I am an MIT Undergraduate and received no outside assistance. This is not related to any of my other work and would not be done otherwise. However, it may include some interesting findings for future research or work I may do. (See Additional Note on Motivation)

*AI Use*: For the report, I had used AI to generate the Hidden Markov Model diagram and notation reference (both of which I had described and edited personally).

As for the code, I used AI for debugging (improper API-usage) and refactoring (breaking up large functions). Because I decided to use unfamiliar data-manipulation and data-visualization libraries (`polars` and `altair` respectively), I used AI extensively to understand and describe the API calls needed to perform an operation. Nowhere in my code is there logic I personally did not personally design.

I had used Claude 4.5 Sonnet/Opus or GPT-5.2.

*Additional Note on Motivation*: The LLM sampling mentioned in a footnote is a large component of my underlying motivation. I know the authors behind AI-2027 and they are interested in developing better geopolitical forecasting tools and have a small team working on something related. Forecasting and logically stepping through events is an extremely time consuming process and LLMs aren't great at doing this out of the box. I was originally interested in GenLM for my mini project as some way to tie LLMs to quantitative forecasts or parameters representing the modeler's assumptions. Link to my notes related project idea: https://gatlen.notion.site/automated-wargames?source=copy_link

#bibliography("../966_cocosci.bib"),
