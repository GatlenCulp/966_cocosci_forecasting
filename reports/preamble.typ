// preamble.typ
#import "@local/gat-typst:0.1.0": *

// Overwrites for class
#let personal-info = (
  university: "MIT",
  author: "Gatlen Culp",
  email: "gculp@mit.edu",
  collaborators: [Claude 4.5 Sonnet (Questions, not Solving)],
  resources: [None],
)

#let course-info = (
  course: [9.66 Computational Cognitive Science],
)

#let info = personal-info + course-info

#let homework = homework.with(
  ..info,
)
#let cheatsheet = cheatsheet.with(
  ..info,
)
