#import "@preview/fletcher:0.5.8": diagram, edge, node, shapes
#import "@preview/physica:0.9.7": *
#import "../../../notation.typ": Belief, Report, emission, trans

#set page(width: auto, height: auto, margin: 3pt)

// Initial latent state node (no observation).

#let hmm = diagram(
  spacing: (14mm, 14mm),
  node-stroke: 0.9pt,
  edge-stroke: 0.9pt,
  mark-scale: 70%,
  {
    node(
      (-2.0, 0),
      [],
      name: <start>,
      shape: circle,
      fill: black,
      stroke: none,
      width: 2.2mm,
      height: 2.2mm,
      inset: 0pt,
    )
    node((3.0, 0), [], name: <end>, shape: circle, fill: black, stroke: none, width: 2.2mm, height: 2.2mm, inset: 0pt)

    node(
      (-1.0, 0),
      $ vb(#Belief)_(0) $,
      name: <Z0>,
      shape: shapes.diamond,
      fill: luma(97%),
    )

    for t in range(3) {
      let i = t + 1
      node((t, 0), $ vb(#Belief)_(#i) $, name: label("Z" + str(i)), shape: circle, fill: luma(97%))
      node((t, 1), $ vb(#Report)_(#i) $, name: label("X" + str(i)), shape: rect, fill: luma(92%))
      edge(label("Z" + str(i)), label("X" + str(i)), "->")
    }

    for t in range(2) {
      let i = t + 1
      edge(label("Z" + str(i)), label("Z" + str(i + 1)), "->")
    }

    // Stationary transition / emission labels (shown once to avoid clutter).
    edge(label("Z2"), label("Z3"), text(0.9em, trans), "->", label-side: left)
    edge(label("Z2"), label("X2"), text(0.9em, emission), "->", label-side: left)

    edge(<start>, <Z0>, "->")
    edge(<Z0>, label("Z1"), "->")
    edge(label("Z3"), <end>, "->")
  },
)

#hmm
