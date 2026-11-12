"""Retention engine: diagnose misconceptions, walk the concept graph, track mastery, schedule revision.

Pure Python on plain data. It never imports the model or any hardware, so it can be built and tested
before the model exists. The model's only job is to produce a question bank (see bank.py).

  bank.py        load and repair a question bank (concepts, misconceptions, questions)
  bkt.py         mastery per concept (Bayesian Knowledge Tracing)
  bayes.py       which misconception does the student hold? and which question tells us most?
  graph.py       the concept graph: prerequisites below, harder ideas above
  fsrs_sched.py  one FSRS card per concept: when to revise (uses the py-fsrs library)
  ranker.py      revision plan: priority = 1 - mastery x recall chance today
  state.py       the learner's saved state
  session.py     the adaptive quiz loop that ties it all together
  simulate.py    fast-forward N days and compare "study once" with "revise on schedule"
"""
