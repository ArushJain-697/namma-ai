"""A small list of everyday words that make poor quiz answers (verbs, adverbs, adjectives,
abstract nouns). Concrete subject words (zinc, bridge, oxygen) are deliberately NOT here.

This is a heuristic stand-in for part-of-speech tagging, which needs a library or model.
It is untuned: ticket 7c (human "key idea / minor detail / trivial" rating on dev
passages) decides whether it helps. Extend it from the dev set only, never the held-out set.
"""

PLAIN_WORDS = frozenset(
    """
    able above across act add after again age ago agree air allow almost alone along already
    also always among amount another answer appear area around ask away back bad base become
    begin behind believe best better big bit body both bring build call came care carry case
    cause certain change check choose clear close come common complete continue cover cross
    cut day deep describe develop did die different done door down draw drive during early
    easy eat effect end enough even ever every exactly example fact fall far fast feel few
    fill final find fine finish first fit follow food form found free full gave get give go
    going gone good got great grow half hand happen hard hear heavy help high hold hope hour
    however idea important include increase instead join keep kind knew know large last late
    later lead learn leave left less let level life light line list little live long look lose
    lot low main make man manage matter mean measure meet method middle might mind mean miss
    moment morning move name near need never new next night normal note nothing notice number
    offer often old open order own page pass past pay perhaps person place plan play point
    possible power present press probably problem protect provide pull put quickly quite reach
    read ready real reason remain remember repeat result return right rise run safe same save
    say second see seem sense set several shape short show side simple since size slow slowly
    small soon sort sound speak special start state stay step still stop strong study such
    sure take talk tell test thing think though thought through throughout today together told
    took toward try turn understand until upon use used useful using usual usually value very
    view wait walk want watch way week well went whole wide within without wonder word work
    world write wrong year yet young
    """.split()
)
