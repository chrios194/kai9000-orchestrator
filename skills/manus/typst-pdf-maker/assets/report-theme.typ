#let report-accent = rgb("#1a5fb4")
#let report-theme(body, title: none, author: none) = {
  set page(margin: (x: 2.2cm, y: 2.5cm))
  set text(font: "Linux Libertine", size: 11pt)
  set par(justify: true, leading: 0.87em)
  show heading.where(level: 1): it => {
    pagebreak(weak: true)
    v(1em)
    text(size: 1.55em, weight: "bold", fill: report-accent)[#it]
    v(0.5em)
  }
  show heading.where(level: 2): it => {
    v(0.8em)
    text(size: 1.3em, weight: "bold")[#it]
    v(0.3em)
  }
  body
}
